from django.shortcuts import render,redirect
from tracker.models import Workout,NutritionLog,Exercise, Set,ContactMessage
from django.utils import timezone
from django.contrib.auth.decorators import login_required


# Create your views here.
def home(request):
    context = {}

    if request.user.is_authenticated:
        user = request.user
        today = timezone.now().date()

        # Get last 2 workouts
        recent_workouts = Workout.objects.filter(
            user=user
        ).order_by('-date')[:2]

        # Get today's nutrition
        todays_nutrition = NutritionLog.objects.filter(
            user=user,
            date=today
        )[:2]

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
            'is_logged_in': True,
            'user': user,
            'today': today,
            'recent_workouts': recent_workouts,
            'todays_nutrition': todays_nutrition,
            'total_calories': total_calories,
            'total_protein': round(total_protein, 1),
            'total_carbs': round(total_carbs, 1),
            'total_fat': round(total_fat, 1),
        }
    else:
        context = {
            'is_logged_in': False,
        }

    return render(request, 'home.html', context)


def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')

    user = request.user
    today = timezone.now().date()

    # Get recent workouts (last 5)
    recent_workouts = Workout.objects.filter(
        user=user
    ).order_by('-date')[:5]

    # Get today's nutrition logs
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

    # Calculate workout streak
    streak = 0
    check_date = today
    while True:
        worked_out = Workout.objects.filter(
            user=user,
            date=check_date
        ).exists()
        if worked_out:
            streak += 1
            check_date = check_date - timezone.timedelta(days=1)
        else:
            break

    # BMI calculation
    bmi = None
    bmi_category = None
    try:
        profile = user.profile
        if profile.weight and profile.height:
            height_m = profile.height / 100
            bmi = round(profile.weight / (height_m * height_m), 1)
            if bmi < 18.5:
                bmi_category = 'Underweight'
            elif bmi < 25:
                bmi_category = 'Normal'
            elif bmi < 30:
                bmi_category = 'Overweight'
            else:
                bmi_category = 'Obese'
    except:
        pass

    context = {
        'user': user,
        'recent_workouts': recent_workouts,
        'todays_nutrition': todays_nutrition,
        'total_calories': total_calories,
        'total_protein': round(total_protein, 1),
        'total_carbs': round(total_carbs, 1),
        'total_fat': round(total_fat, 1),
        'today': today,
        'streak': streak,
        'bmi': bmi,
        'bmi_category': bmi_category,
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
        image = request.FILES.get('image')  # get uploaded image

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
            notes=notes,
            image=image  # save image
        )

        # Loop through exercises
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

    context = {
        'today': timezone.now().date(),
    }
    return render(request, 'log_workout.html', context)
def delete_workout(request, workout_id):
    if not request.user.is_authenticated:
        return redirect('login')

    try:
        workout = Workout.objects.get(id=workout_id, user=request.user)
        workout.delete()
    except Workout.DoesNotExist:
        pass

    return redirect('dashboard')
def log_meal(request):
    if not request.user.is_authenticated:
        return redirect('login')

    user = request.user

    if request.method == 'POST':
        meal_name = request.POST.get('meal_name', '').strip()
        date = request.POST.get('date', '').strip()
        calories = request.POST.get('calories', '').strip()
        protein = request.POST.get('protein', '').strip()
        carbs = request.POST.get('carbs', '').strip()
        fat = request.POST.get('fat', '').strip()

        # Debug — print what we received
        print("meal_name:", meal_name)
        print("date:", date)
        print("calories:", calories)
        print("protein:", protein)
        print("carbs:", carbs)
        print("fat:", fat)

        # Basic validation
        if not meal_name or not date or not calories:
            error = "Please fill in meal name, date and calories."
            return render(request, 'log_meal.html', {
                'error': error,
                'today': timezone.now().date(),
            })

        # Save to database
        NutritionLog.objects.create(
            user=user,
            meal_name=meal_name,
            date=date,
            calories=int(calories),
            protein=float(protein) if protein else 0,
            carbs=float(carbs) if carbs else 0,
            fat=float(fat) if fat else 0,
        )

        return redirect('dashboard')

    context = {
        'today': timezone.now().date(),
    }
    return render(request, 'log_meal.html', context)

def delete_meal(request, meal_id):
    if not request.user.is_authenticated:
        return redirect('login')
    try:
        meal = NutritionLog.objects.get(id=meal_id, user=request.user)
        meal.delete()
    except NutritionLog.DoesNotExist:
        pass
    return redirect('dashboard')

# Calorie burn lookup table
CALORIE_BURN_PER_SET = {
    'bench press': 5,
    'squat': 7,
    'deadlift': 8,
    'overhead press': 5,
    'barbell row': 5,
    'pull up': 4,
    'chin up': 4,
    'dip': 3,
    'pushup': 2,
    'push up': 2,
    'lunge': 4,
    'leg press': 5,
    'leg curl': 3,
    'leg extension': 3,
    'calf raise': 2,
    'bicep curl': 2,
    'tricep pushdown': 2,
    'lateral raise': 2,
    'face pull': 2,
    'plank': 3,
    'running': 10,
    'cycling': 8,
    'rowing': 7,
}

def get_calorie_burn(exercise_name, num_sets):
    # Look up the exercise name (case insensitive)
    name_lower = exercise_name.lower().strip()
    calories_per_set = CALORIE_BURN_PER_SET.get(name_lower, 3)  # default 3 if not found
    return calories_per_set * num_sets


def workout_detail(request, workout_id):
    if not request.user.is_authenticated:
        return redirect('login')

    # Get workout — make sure it belongs to this user
    try:
        workout = Workout.objects.get(id=workout_id, user=request.user)
    except Workout.DoesNotExist:
        return redirect('dashboard')

    # Get all exercises for this workout
    exercises = workout.exercises.all()

    # Build exercise data with calorie predictions
    exercise_data = []
    total_calories_burned = 0

    for exercise in exercises:
        sets = exercise.sets.all()
        num_sets = sets.count()
        calories_burned = get_calorie_burn(exercise.name, num_sets)
        total_calories_burned += calories_burned

        exercise_data.append({
            'exercise': exercise,
            'sets': sets,
            'calories_burned': calories_burned,
        })

    context = {
        'workout': workout,
        'exercise_data': exercise_data,
        'total_calories_burned': total_calories_burned,
    }
    return render(request, 'workout_detail.html', context)


def edit_workout(request, workout_id):
    if not request.user.is_authenticated:
        return redirect('login')

    try:
        workout = Workout.objects.get(id=workout_id, user=request.user)
    except Workout.DoesNotExist:
        return redirect('dashboard')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        date = request.POST.get('date', '').strip()
        notes = request.POST.get('notes', '').strip()
        new_image = request.FILES.get('image')
        remove_image = request.POST.get('remove_image')

        if not title or not date:
            error = "Please fill in the workout title and date."
            return render(request, 'edit_workout.html', {
                'workout': workout,
                'error': error,
            })

        # Update basic fields
        workout.title = title
        workout.date = date
        workout.notes = notes

        # Handle image
        if remove_image:
            # User wants to remove existing image
            if workout.image:
                workout.image.delete(save=False)
            workout.image = None
        elif new_image:
            # User uploaded a new image
            if workout.image:
                workout.image.delete(save=False)
            workout.image = new_image

        workout.save()

        # Delete existing exercises and recreate
        workout.exercises.all().delete()

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

        return redirect('workout_detail', workout_id=workout.id)

    context = {
        'workout': workout,
        'exercises': workout.exercises.all(),
    }
    return render(request, 'edit_workout.html', context)

def edit_meal(request, meal_id):
    if not request.user.is_authenticated:
        return redirect('login')

    try:
        meal = NutritionLog.objects.get(id=meal_id, user=request.user)
    except NutritionLog.DoesNotExist:
        return redirect('dashboard')

    if request.method == 'POST':
        meal_name = request.POST.get('meal_name', '').strip()
        date = request.POST.get('date', '').strip()
        calories = request.POST.get('calories', '').strip()
        protein = request.POST.get('protein', '').strip()
        carbs = request.POST.get('carbs', '').strip()
        fat = request.POST.get('fat', '').strip()

        if not meal_name or not date or not calories:
            error = "Please fill in meal name, date and calories."
            return render(request, 'edit_meal.html', {
                'meal': meal,
                'error': error,
            })

        # Update the meal
        meal.meal_name = meal_name
        meal.date = date
        meal.calories = int(calories)
        meal.protein = float(protein) if protein else 0
        meal.carbs = float(carbs) if carbs else 0
        meal.fat = float(fat) if fat else 0
        meal.save()

        return redirect('dashboard')

    context = {
        'meal': meal,
    }
    return render(request, 'edit_meal.html', context)

def about(request):
    return render(request, 'about.html')


def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        if not name or not email or not subject or not message:
            return render(request, 'contact.html', {
                'error': 'Please fill in all fields.',
                'name': name,
                'email': email,
                'subject': subject,
                'message': message,
            })

        ContactMessage.objects.create(
            name=name,
            email=email,
            subject=subject,
            message=message,
        )

        return render(request, 'contact.html', {
            'success': True,
        })

    return render(request, 'contact.html')