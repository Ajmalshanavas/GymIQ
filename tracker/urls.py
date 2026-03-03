from django.urls import path
from tracker import views

urlpatterns=[
path('',views.home,name="home"),
path('dashboard/', views.dashboard, name='dashboard'),
path('log_workout/', views.log_workout, name='log_workout'),
    path('log_meal/', views.log_meal, name='log_meal'),
path('delete-workout/<int:workout_id>/', views.delete_workout, name='delete_workout'),
path('delete-meal/<int:meal_id>/', views.delete_meal, name='delete_meal'),
path('workout/<int:workout_id>/', views.workout_detail, name='workout_detail'),
path('workout/<int:workout_id>/edit/', views.edit_workout, name='edit_workout'),
path('edit-meal/<int:meal_id>/', views.edit_meal, name='edit_meal'),
path('about/', views.about, name='about'),
path('contact/', views.contact, name='contact'),
path('progress/', views.progress, name='progress')
]