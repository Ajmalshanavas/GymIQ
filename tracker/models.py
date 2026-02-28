from django.db import models
from users.models import User


class Workout(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='workouts'
    )
    title = models.CharField(max_length=200)
    date = models.DateField()
    notes = models.TextField(blank=True)
    image = models.ImageField(
        upload_to='workout_images/',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.title} ({self.date})"

    def get_total_volume(self):
        """Total weight = sum of all sets × reps × weight"""
        total = 0
        for exercise in self.exercises.all():
            total += exercise.get_volume()
        return total

    def get_total_exercises(self):
        """Total number of exercises in this workout"""
        return self.exercises.count()

    def get_total_sets(self):
        """Total number of sets across all exercises"""
        total = 0
        for exercise in self.exercises.all():
            total += exercise.sets.count()
        return total


class Exercise(models.Model):
    workout = models.ForeignKey(
        Workout,
        on_delete=models.CASCADE,
        related_name='exercises'
    )
    name = models.CharField(max_length=200)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.workout.title})"

    def get_volume(self):
        """Total volume for this exercise across all sets"""
        total = 0
        for s in self.sets.all():
            total += s.reps * s.weight
        return total

    def get_total_sets(self):
        """Number of sets for this exercise"""
        return self.sets.count()

    def get_best_set(self):
        """Returns the set with highest weight"""
        return self.sets.order_by('-weight').first()


class Set(models.Model):
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name='sets'
    )
    set_number = models.PositiveIntegerField()
    reps = models.PositiveIntegerField()
    weight = models.FloatField(help_text="Weight in kg")

    def __str__(self):
        return f"Set {self.set_number} → {self.reps} reps @ {self.weight}kg"

    def get_set_volume(self):
        """Volume for this single set"""
        return self.reps * self.weight


class NutritionLog(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='nutrition_logs'
    )
    date = models.DateField()
    meal_name = models.CharField(max_length=200)
    calories = models.PositiveIntegerField()
    protein = models.FloatField(help_text="Protein in grams")
    carbs = models.FloatField(help_text="Carbs in grams")
    fat = models.FloatField(help_text="Fat in grams")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.meal_name} ({self.date})"

    def get_daily_totals(self, user, date):
        """Get total calories, protein, carbs, fat for a day"""
        logs = NutritionLog.objects.filter(user=user, date=date)
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        for log in logs:
            total_calories += log.calories
            total_protein += log.protein
            total_carbs += log.carbs
            total_fat += log.fat
        return {
            'total_calories': total_calories,
            'total_protein': total_protein,
            'total_carbs': total_carbs,
            'total_fat': total_fat,
        }