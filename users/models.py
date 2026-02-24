from django.db import models
from django.contrib.auth.models import AbstractUser



class User(AbstractUser):
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.PositiveIntegerField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True)
    fitness_goal = models.CharField(max_length=100, blank=True)
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        null=True, blank=True
    )

    def __str__(self):
        return f"{self.user.email}'s Profile"

    def get_bmi(self):
        """Calculate BMI from weight and height"""
        if self.weight and self.height:
            height_m = self.height / 100
            bmi = self.weight / (height_m * height_m)
            return round(bmi, 1)
        return None


