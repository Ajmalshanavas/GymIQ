from django.shortcuts import render,redirect
from tracker.models import Workout,NutritionLog,Exercise, Set
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

def log_workout(request):
    if not request.user.is_authenticated:
        return redirect('login')

    user = request.user

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        date = request.POST.get('date', '').strip()
        notes = request.POST.get('notes', '').strip()

        # Basic validation
        if not title or not date:
            error = "Please fill in the workout title and date."
            return render(request, 'log_workout.html', {
                'error': error,
                'today': timezone.now().date(),
            })

        # Create the workout
        workout = Workout.objects.create(
            user=user,
            title=title,
            date=date,
            notes=notes
        )

        # Loop through exercises submitted
        exercise_index = 0
        while f'exercise_{exercise_index}_name' in request.POST:
            ex_name = request.POST.get(f'exercise_{exercise_index}_name', '').strip()
            ex_notes = request.POST.get(f'exercise_{exercise_index}_notes', '').strip()

            if ex_name:
                exercise = Exercise.objects.create(
                    workout=workout,
                    name=ex_name,
                    notes=ex_notes
                )

                # Loop through sets for this exercise
                set_index = 0
                while f'exercise_{exercise_index}_set_{set_index}_reps' in request.POST:
                    reps = request.POST.get(f'exercise_{exercise_index}_set_{set_index}_reps', '').strip()
                    weight = request.POST.get(f'exercise_{exercise_index}_set_{set_index}_weight', '').strip()

                    if reps and weight:
                        Set.objects.create(
                            exercise=exercise,
                            set_number=set_index + 1,
                            reps=int(reps),
                            weight=float(weight)
                        )
                    set_index += 1

            exercise_index += 1

        return redirect('dashboard')

    # GET request — just show the empty form
    context = {
        'today': timezone.now().date(),
    }
    return render(request, 'log_workout.html', context)