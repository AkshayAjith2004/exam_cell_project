from django.urls import path
from . import views

urlpatterns = [
    path('', views.student_list, name='student_list'),
    path('register/', views.student_register, name='student_register'),
    path('edit/<int:pk>/', views.student_edit, name='student_edit'),
    path('delete/<int:pk>/', views.student_delete, name='student_delete'),
    path('upload-excel/', views.student_bulk_upload, name='student_bulk_upload'),
    path('download-template/', views.student_sample_template, name='student_sample_template'),
]
