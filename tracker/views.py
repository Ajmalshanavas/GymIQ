from django.shortcuts import render,redirect
from tracker.models import Workout,NutritionLog
from django.utils import timezone
from django.contrib.auth.decorators import login_required


# Create your views here.
def home(request):
    return render(request,"home.html")


def dashboard(request):
    # If user is not logged in, redirect to login page
    if not request.user.is_authenticated:
        return redirect('login')

    user = request.user

    # Get recent workouts (last 5)
    recent_workouts = Workout.objects.filter(
        user=user
    ).order_by('-date')[:5]

    # Get today's nutrition logs
    today = timezone.now().date()
    todays_nutrition = NutritionLog.objects.filter(
        user=user,
        date=today
    )

    # Calculate today's totals
    total_calories = 0
    total_protein = 0
    total_carbs = 0
    total_fat = 0
    for log in todays_nutrition:
        total_calories += log.calories
        total_protein += log.protein
        total_carbs += log.carbs
        total_fat += log.fat

    context = {
        'user': user,
        'recent_workouts': recent_workouts,
        'todays_nutrition': todays_nutrition,
        'total_calories': total_calories,
        'total_protein': round(total_protein, 1),
        'total_carbs': round(total_carbs, 1),
        'total_fat': round(total_fat, 1),
        'today': today,
    }
    return render(request, 'dashboard.html', context)