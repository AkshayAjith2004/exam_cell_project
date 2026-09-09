from django.urls import path
from . import views

urlpatterns = [
    path('', views.subject_list, name='subject_list'),
    path('edit/<int:pk>/', views.subject_edit, name='subject_edit'),
    path('assign-faculty/<int:subject_id>/', views.assign_faculty, name='assign_faculty'),
    path('delete/<int:pk>/', views.subject_delete, name='subject_delete'),
]
