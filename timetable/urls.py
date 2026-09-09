from django.urls import path
from . import views

urlpatterns = [
    path('', views.timetable_list, name='timetable_list'),
    path('delete/<int:pk>/', views.timetable_delete, name='timetable_delete'),
]
