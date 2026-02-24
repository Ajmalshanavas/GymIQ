from django.urls import path
from tracker import views

urlpatterns=[
path('',views.home,name="home"),
path('dashboard/', views.dashboard, name='dashboard')
]