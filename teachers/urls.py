from django.urls import path
from . import views

urlpatterns = [
    path('', views.teacher_list, name='teacher_list'),
    path('register/', views.teacher_register, name='teacher_register'),
]
