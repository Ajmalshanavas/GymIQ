from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import RegisterForm
from .models import Profile
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from tracker.models import Subscription


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Account created! Please login.')
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid email or password.')
    return render(request, 'login.html')


def user_logout(request):
    logout(request)
    return redirect('home')


def get_sub_context(user):
    """Helper — returns is_pro and sub_expires for any user"""
    sub, _ = Subscription.objects.get_or_create(user=user)
    return {
        'is_pro':      sub.is_pro(),
        'sub_expires': sub.expires_at,
    }


def profile(request):
    if not request.user.is_authenticated:
        return redirect('login')

    user = request.user
    profile_obj, created = Profile.objects.get_or_create(user=user)

    if request.method == 'POST':
        username       = request.POST.get('username', '').strip()
        email          = request.POST.get('email', '').strip()
        age            = request.POST.get('age', '').strip()
        weight         = request.POST.get('weight', '').strip()
        height         = request.POST.get('height', '').strip()
        fitness_goal   = request.POST.get('fitness_goal', '').strip()
        profile_picture = request.FILES.get('profile_picture')
        remove_picture  = request.POST.get('remove_picture')

        # Validate
        if not username or not email:
            return render(request, 'profile.html', {
                'profile': profile_obj,
                'error':   'Username and email are required.',
                **get_sub_context(user),
            })

        # Update user
        user.username = username
        user.email    = email
        user.save()

        # Update profile
        profile_obj.age          = int(age)        if age    else None
        profile_obj.weight       = float(weight)   if weight else None
        profile_obj.height       = float(height)   if height else None
        profile_obj.fitness_goal = fitness_goal
        profile_obj.challenge_level = request.POST.get('challenge_level', 'intermediate')

        # Handle profile picture
        if remove_picture:
            if profile_obj.profile_picture:
                profile_obj.profile_picture.delete(save=False)
            profile_obj.profile_picture = None
        elif profile_picture:
            if profile_obj.profile_picture:
                profile_obj.profile_picture.delete(save=False)
            profile_obj.profile_picture = profile_picture

        profile_obj.save()

        return render(request, 'profile.html', {
            'profile': profile_obj,
            'success': 'Profile updated successfully!',
            **get_sub_context(user),
        })

    return render(request, 'profile.html', {
        'profile': profile_obj,
        **get_sub_context(user),
    })


def change_password(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':
        current_password  = request.POST.get('current_password', '').strip()
        new_password      = request.POST.get('new_password', '').strip()
        confirm_password  = request.POST.get('confirm_password', '').strip()

        if not request.user.check_password(current_password):
            return render(request, 'change_password.html', {
                'error': 'Current password is incorrect.'
            })

        if new_password != confirm_password:
            return render(request, 'change_password.html', {
                'error': 'New passwords do not match.'
            })

        if len(new_password) < 8:
            return render(request, 'change_password.html', {
                'error': 'Password must be at least 8 characters.'
            })

        request.user.set_password(new_password)
        request.user.save()
        update_session_auth_hash(request, request.user)

        return render(request, 'change_password.html', {
            'success': 'Password changed successfully!'
        })

    return render(request, 'change_password.html')


def delete_account(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        return redirect('home')

    return redirect('profile')