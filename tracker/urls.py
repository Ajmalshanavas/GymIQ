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
path('progress/', views.progress, name='progress'),
path('personal-records/', views.personal_records, name='personal_records'),
path('water/add/', views.water_add, name='water_add'),
path('water/remove/', views.water_remove, name='water_remove'),
path('water/set-goal/', views.water_set_goal, name='water_set_goal'),
path('templates/', views.workout_templates, name='workout_templates'),
path('templates/save/<int:workout_id>/', views.save_template, name='save_template'),
path('templates/delete/<int:template_id>/', views.delete_template, name='delete_template'),
path('templates/load/<int:template_id>/', views.load_template, name='load_template')
]