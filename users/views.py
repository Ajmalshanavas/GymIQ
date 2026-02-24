from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import RegisterForm
from .models import Profile
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Auto-create profile when user registers

            messages.success(request, 'Account created! Please login.')
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'users/register.html', {'form': form})


from django.shortcuts import render

def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')  # we'll create this later
        else:
            messages.error(request, 'Invalid email or password.')
    return render(request, 'users/login.html')

def user_logout(request):
    logout(request)
    return redirect('home')
