from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Profile



class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'username', 'is_staff', 'is_active', 'date_joined']
    ordering = ['-date_joined']
    search_fields = ['email', 'username']



class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'age', 'weight', 'height', 'fitness_goal']
    search_fields = ['user__email']

admin.site.register(User, CustomUserAdmin)
admin.site.register(Profile, ProfileAdmin)

