from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email


class Profile(models.Model):
    CHALLENGE_CHOICES = [
        ('beginner',     'Beginner — 1000kg'),
        ('intermediate', 'Intermediate — 3000kg'),
        ('advanced',     'Advanced — 4000kg'),
        ('beast',        'Beast Mode — 6000kg'),
    ]
    CHALLENGE_TARGETS = {
        'beginner':     1000,
        'intermediate': 3000,
        'advanced':     4000,
        'beast':        6000,
    }

    user            = models.OneToOneField(User, on_delete=models.CASCADE)
    age             = models.PositiveIntegerField(null=True, blank=True)
    weight          = models.FloatField(null=True, blank=True)
    height          = models.FloatField(null=True, blank=True)
    fitness_goal    = models.CharField(max_length=100, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    challenge_level = models.CharField(
        max_length=20,
        choices=CHALLENGE_CHOICES,
        default='intermediate'
    )

    def __str__(self):
        return f"{self.user.email}'s Profile"

    def get_bmi(self):
        if self.weight and self.height:
            height_m = self.height / 100
            bmi = self.weight / (height_m * height_m)
            return round(bmi, 1)
        return None

    def get_challenge_target(self):
        return self.CHALLENGE_TARGETS.get(self.challenge_level, 1000)