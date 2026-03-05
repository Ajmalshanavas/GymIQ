from django.shortcuts import render, redirect
from django.db import models as django_models
from tracker.models import Workout, NutritionLog, Exercise, Set, ContactMessage, PersonalRecord, WaterIntake
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import zoneinfo
import json
from django.db.models import Sum, Max, F
from datetime import timedelta


# ── IST TIMEZONE HELPER ────────────────────────────────────────
def get_ist_today():
    ist = zoneinfo.ZoneInfo('Asia/Kolkata')
    return timezone.now().astimezone(ist).date()


# ── PR HELPER ──────────────────────────────────────────────────
def check_and_update_pr(user, exercise, workout):
    """Check if any set in this exercise is a new PR"""
    best_set = exercise.sets.order_by('-weight').first()
    if not best_set:
        return False

    existing_pr = PersonalRecord.objects.filter(
        user=user,
        exercise_name__iexact=exercise.name
    ).first()

    if not existing_pr:
        PersonalRecord.objects.create(
            user=user,
            exercise_name=exercise.name,
            weight=best_set.weight,
            reps=best_set.reps,
            achieved_on=workout.date,
            workout=workout
        )
        return True
    elif best_set.weight > existing_pr.weight:
        existing_pr.weight = best_set.weight
        existing_pr.reps = best_set.reps
        existing_pr.achieved_on = workout.date
        existing_pr.workout = workout
        existing_pr.save()
        return True

    return False


# ── HOME ───────────────────────────────────────────────────────
def home(request):
    context = {}

    if request.user.is_authenticated:
        user = request.user
        today = get_ist_today()

        recent_workouts = Workout.objects.filter(
            user=user
        ).order_by('-date')[:2]

        todays_nutrition = NutritionLog.objects.filter(
            user=user,
            date=today
        )[:2]

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


# ── DASHBOARD ──────────────────────────────────────────────────
def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')

    user = request.user
    today = get_ist_today()

    # Recent workouts
    recent_workouts = Workout.objects.filter(
        user=user
    ).order_by('-date')[:5]

    # Today's nutrition (for totals)
    todays_nutrition = NutritionLog.objects.filter(
        user=user,
        date=today
    )

    # Recent nutrition (last 5 meals with date)
    recent_nutrition = NutritionLog.objects.filter(
        user=user
    ).order_by('-date', '-created_at')[:5]

    # Today's totals
    total_calories = 0
    total_protein = 0
    total_carbs = 0
    total_fat = 0
    for log in todays_nutrition:
        total_calories += log.calories
        total_protein += log.protein
        total_carbs += log.carbs
        total_fat += log.fat

    # Workout streak
    streak = 0
    check_date = today
    while True:
        worked_out = Workout.objects.filter(
            user=user,
            date=check_date
        ).exists()
        if worked_out:
            streak += 1
            check_date = check_date - timedelta(days=1)
        else:
            break

    # BMI
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

    # Last 7 days volume for chart
    last_7_volume = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        vol = Set.objects.filter(
            exercise__workout__user=user,
            exercise__workout__date=day
        ).aggregate(
            total=Sum(F('reps') * F('weight'))
        )['total'] or 0
        last_7_volume.append({
            'day': day.strftime('%a'),
            'volume': round(float(vol), 1),
        })

    # Recent PRs for banner
    recent_prs = PersonalRecord.objects.filter(
        user=user
    ).order_by('-achieved_on')[:3]

    # ── WATER INTAKE ──────────────────────────────────────────
    water_log, created = WaterIntake.objects.get_or_create(
        user=user,
        date=today,
        defaults={'glasses': 0, 'goal': 8}
    )

    context = {
        'user': user,
        'recent_workouts': recent_workouts,
        'recent_nutrition': recent_nutrition,
        'total_calories': total_calories,
        'total_protein': round(total_protein, 1),
        'total_carbs': round(total_carbs, 1),
        'total_fat': round(total_fat, 1),
        'today': today,
        'streak': streak,
        'bmi': bmi,
        'bmi_category': bmi_category,
        'last_7_volume': json.dumps(last_7_volume),
        'recent_prs': recent_prs,
        'water_log': water_log,
        'water_percentage': water_log.get_percentage(),
    }
    return render(request, 'dashboard.html', context)


# ── WATER INTAKE VIEWS ─────────────────────────────────────────
def water_add(request):
    """Add one glass of water — AJAX or redirect"""
    if not request.user.is_authenticated:
        return redirect('login')

    today = get_ist_today()
    water_log, created = WaterIntake.objects.get_or_create(
        user=request.user,
        date=today,
        defaults={'glasses': 0, 'goal': 8}
    )
    water_log.glasses += 1
    water_log.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'glasses': water_log.glasses,
            'goal': water_log.goal,
            'percentage': water_log.get_percentage(),
            'goal_met': water_log.is_goal_met(),
        })

    return redirect('dashboard')


def water_remove(request):
    """Remove one glass of water"""
    if not request.user.is_authenticated:
        return redirect('login')

    today = get_ist_today()
    water_log, created = WaterIntake.objects.get_or_create(
        user=request.user,
        date=today,
        defaults={'glasses': 0, 'goal': 8}
    )
    if water_log.glasses > 0:
        water_log.glasses -= 1
        water_log.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'glasses': water_log.glasses,
            'goal': water_log.goal,
            'percentage': water_log.get_percentage(),
            'goal_met': water_log.is_goal_met(),
        })

    return redirect('dashboard')


def water_set_goal(request):
    """Update daily water goal"""
    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':
        today = get_ist_today()
        goal = request.POST.get('goal', '8').strip()
        try:
            goal = int(goal)
            if goal < 1:
                goal = 1
            if goal > 20:
                goal = 20
        except ValueError:
            goal = 8

        water_log, created = WaterIntake.objects.get_or_create(
            user=request.user,
            date=today,
            defaults={'glasses': 0, 'goal': goal}
        )
        if not created:
            water_log.goal = goal
            water_log.save()

    return redirect('dashboard')


# ── LOG WORKOUT ────────────────────────────────────────────────
def log_workout(request):
    if not request.user.is_authenticated:
        return redirect('login')

    user = request.user
    today = get_ist_today()

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        date = request.POST.get('date', '').strip()
        notes = request.POST.get('notes', '').strip()
        image = request.FILES.get('image')

        if not title or not date:
            return render(request, 'log_workout.html', {
                'error': 'Please fill in the workout title and date.',
                'today': today,
            })

        workout = Workout.objects.create(
            user=user,
            title=title,
            date=date,
            notes=notes,
            image=image
        )

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

                # Check for new PR after all sets are saved
                check_and_update_pr(user, exercise, workout)

            exercise_index += 1

        return redirect('dashboard')

    context = {
        'today': today,'templates': WorkoutTemplate.objects.filter(user=user),
    }
    return render(request, 'log_workout.html')


# ── DELETE WORKOUT ─────────────────────────────────────────────
def delete_workout(request, workout_id):
    if not request.user.is_authenticated:
        return redirect('login')

    try:
        workout = Workout.objects.get(id=workout_id, user=request.user)
        workout.delete()
    except Workout.DoesNotExist:
        pass



    return redirect('dashboard')


# ── LOG MEAL ───────────────────────────────────────────────────
def log_meal(request):
    if not request.user.is_authenticated:
        return redirect('login')

    user = request.user
    today = get_ist_today()

    if request.method == 'POST':
        meal_name = request.POST.get('meal_name', '').strip()
        date = request.POST.get('date', '').strip()
        calories = request.POST.get('calories', '').strip()
        protein = request.POST.get('protein', '').strip()
        carbs = request.POST.get('carbs', '').strip()
        fat = request.POST.get('fat', '').strip()

        if not meal_name or not date or not calories:
            return render(request, 'log_meal.html', {
                'error': 'Please fill in meal name, date and calories.',
                'today': today,
            })

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
        'today': today,
    }
    return render(request, 'log_meal.html', context)


# ── DELETE MEAL ────────────────────────────────────────────────
def delete_meal(request, meal_id):
    if not request.user.is_authenticated:
        return redirect('login')

    try:
        meal = NutritionLog.objects.get(id=meal_id, user=request.user)
        meal.delete()
    except NutritionLog.DoesNotExist:
        pass

    return redirect('dashboard')


# ── CALORIE BURN TABLE ─────────────────────────────────────────
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
    name_lower = exercise_name.lower().strip()
    calories_per_set = CALORIE_BURN_PER_SET.get(name_lower, 3)
    return calories_per_set * num_sets


# ── WORKOUT DETAIL ─────────────────────────────────────────────
def workout_detail(request, workout_id):
    if not request.user.is_authenticated:
        return redirect('login')

    try:
        workout = Workout.objects.get(id=workout_id, user=request.user)
    except Workout.DoesNotExist:
        return redirect('dashboard')

    exercises = workout.exercises.all()
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


# ── EDIT WORKOUT ───────────────────────────────────────────────
def edit_workout(request, workout_id):
    if not request.user.is_authenticated:
        return redirect('login')

    today = get_ist_today()

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
            return render(request, 'edit_workout.html', {
                'workout': workout,
                'error': 'Please fill in the workout title and date.',
                'today': today,
            })

        workout.title = title
        workout.date = date
        workout.notes = notes

        if remove_image:
            if workout.image:
                workout.image.delete(save=False)
            workout.image = None
        elif new_image:
            if workout.image:
                workout.image.delete(save=False)
            workout.image = new_image

        workout.save()
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

                check_and_update_pr(user=request.user, exercise=exercise, workout=workout)

            exercise_index += 1

        return redirect('workout_detail', workout_id=workout.id)

    context = {
        'workout': workout,
        'exercises': workout.exercises.all(),
        'today': today,
    }
    return render(request, 'edit_workout.html', context)


# ── EDIT MEAL ──────────────────────────────────────────────────
def edit_meal(request, meal_id):
    if not request.user.is_authenticated:
        return redirect('login')

    today = get_ist_today()

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
            return render(request, 'edit_meal.html', {
                'meal': meal,
                'error': 'Please fill in meal name, date and calories.',
                'today': today,
            })

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
        'today': today,
    }
    return render(request, 'edit_meal.html', context)


# ── ABOUT & CONTACT ────────────────────────────────────────────
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

        return render(request, 'contact.html', {'success': True})

    return render(request, 'contact.html')


# ── PROGRESS ───────────────────────────────────────────────────
def progress(request):
    if not request.user.is_authenticated:
        return redirect('login')

    user = request.user
    today = get_ist_today()

    exercise_names = Exercise.objects.filter(
        workout__user=user
    ).values_list('name', flat=True).distinct().order_by('name')

    selected_exercise = request.GET.get('exercise', '')
    if not selected_exercise and exercise_names:
        selected_exercise = list(exercise_names)[0]

    strength_data = []
    if selected_exercise:
        workouts_with_exercise = Exercise.objects.filter(
            workout__user=user,
            name__iexact=selected_exercise
        ).order_by('workout__date')

        for ex in workouts_with_exercise:
            max_weight = ex.sets.aggregate(Max('weight'))['weight__max']
            if max_weight:
                strength_data.append({
                    'date': str(ex.workout.date),
                    'weight': float(max_weight),
                })

    weekly_volume = []
    for i in range(7, -1, -1):
        week_start = today - timedelta(days=today.weekday() + 7 * i)
        week_end = week_start + timedelta(days=6)
        volume = Set.objects.filter(
            exercise__workout__user=user,
            exercise__workout__date__range=[week_start, week_end]
        ).aggregate(
            total=Sum(django_models.F('reps') * django_models.F('weight'))
        )['total'] or 0

        weekly_volume.append({
            'week': week_start.strftime('%b %d'),
            'volume': round(float(volume), 1),
        })

    last_7_days = today - timedelta(days=6)
    nutrition_logs = NutritionLog.objects.filter(
        user=user,
        date__range=[last_7_days, today]
    )

    total_protein = float(nutrition_logs.aggregate(Sum('protein'))['protein__sum'] or 0)
    total_carbs = float(nutrition_logs.aggregate(Sum('carbs'))['carbs__sum'] or 0)
    total_fat = float(nutrition_logs.aggregate(Sum('fat'))['fat__sum'] or 0)

    workout_dates = list(
        Workout.objects.filter(
            user=user,
            date__range=[today - timedelta(days=29), today]
        ).values_list('date', flat=True)
    )
    workout_dates_str = [str(d) for d in workout_dates]

    todays_logs = NutritionLog.objects.filter(user=user, date=today)
    dash_protein = float(todays_logs.aggregate(Sum('protein'))['protein__sum'] or 0)
    dash_carbs = float(todays_logs.aggregate(Sum('carbs'))['carbs__sum'] or 0)
    dash_fat = float(todays_logs.aggregate(Sum('fat'))['fat__sum'] or 0)

    last_7_volume = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        vol = Set.objects.filter(
            exercise__workout__user=user,
            exercise__workout__date=day
        ).aggregate(
            total=Sum(django_models.F('reps') * django_models.F('weight'))
        )['total'] or 0
        last_7_volume.append({
            'day': day.strftime('%a'),
            'volume': round(float(vol), 1),
        })

    context = {
        'exercise_names': exercise_names,
        'selected_exercise': selected_exercise,
        'strength_data': json.dumps(strength_data),
        'weekly_volume': json.dumps(weekly_volume),
        'total_protein': round(total_protein, 1),
        'total_carbs': round(total_carbs, 1),
        'total_fat': round(total_fat, 1),
        'workout_dates': json.dumps(workout_dates_str),
        'today': str(today),
        'dash_protein': dash_protein,
        'dash_carbs': dash_carbs,
        'dash_fat': dash_fat,
        'last_7_volume': json.dumps(last_7_volume),
    }
    return render(request, 'progress.html', context)


# ── PERSONAL RECORDS ───────────────────────────────────────────
def personal_records(request):
    if not request.user.is_authenticated:
        return redirect('login')

    prs = PersonalRecord.objects.filter(
        user=request.user
    ).order_by('exercise_name')

    context = {
        'prs': prs,
        'total_prs': prs.count(),
    }
    return render(request, 'personal_records.html', context)

from tracker.models import Workout, NutritionLog, Exercise, Set, ContactMessage, PersonalRecord, WaterIntake, WorkoutTemplate, TemplateExercise, TemplateSet

def workout_templates(request):
    if not request.user.is_authenticated:
        return redirect('login')

    templates = WorkoutTemplate.objects.filter(
        user=request.user
    ).prefetch_related('exercises__sets')

    context = {
        'templates': templates,
    }
    return render(request, 'workout_templates.html', context)


def save_template(request, workout_id):
    """Save an existing workout as a template"""
    if not request.user.is_authenticated:
        return redirect('login')

    try:
        workout = Workout.objects.get(id=workout_id, user=request.user)
    except Workout.DoesNotExist:
        return redirect('dashboard')

    if request.method == 'POST':
        template_name = request.POST.get('template_name', workout.title).strip()

        # Create template
        template = WorkoutTemplate.objects.create(
            user=request.user,
            name=template_name,
        )

        # Copy exercises and sets
        for i, exercise in enumerate(workout.exercises.all()):
            tmpl_exercise = TemplateExercise.objects.create(
                template=template,
                name=exercise.name,
                notes=exercise.notes,
                order=i,
            )
            for s in exercise.sets.all():
                TemplateSet.objects.create(
                    exercise=tmpl_exercise,
                    set_number=s.set_number,
                    reps=s.reps,
                    weight=s.weight,
                )

        return redirect('workout_templates')

    return redirect('workout_detail', workout_id=workout_id)


def delete_template(request, template_id):
    if not request.user.is_authenticated:
        return redirect('login')

    try:
        template = WorkoutTemplate.objects.get(id=template_id, user=request.user)
        template.delete()
    except WorkoutTemplate.DoesNotExist:
        pass

    return redirect('workout_templates')


def load_template(request, template_id):
    """Return template data as JSON for pre-filling log workout form"""
    if not request.user.is_authenticated:
        return redirect('login')

    try:
        template = WorkoutTemplate.objects.get(id=template_id, user=request.user)
    except WorkoutTemplate.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

    data = {
        'name': template.name,
        'exercises': []
    }

    for exercise in template.exercises.all():
        ex_data = {
            'name': exercise.name,
            'notes': exercise.notes,
            'sets': [
                {'reps': s.reps, 'weight': s.weight}
                for s in exercise.sets.all()
            ]
        }
        data['exercises'].append(ex_data)

    return JsonResponse(data)