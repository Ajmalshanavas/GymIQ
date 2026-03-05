from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Profile


def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

def save_profile(sender, instance, created, **kwargs):
    if not created:
        try:
            instance.profile.save()
        except Profile.DoesNotExist:
            Profile.objects.create(user=instance)


post_save.connect(create_profile, sender=User)
post_save.connect(save_profile, sender=User)