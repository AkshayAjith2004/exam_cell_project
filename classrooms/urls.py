from django.urls import path
from . import views

urlpatterns = [
    path('', views.classroom_list, name='classroom_list'),
    path('toggle/<int:pk>/', views.classroom_toggle, name='classroom_toggle'),
]
