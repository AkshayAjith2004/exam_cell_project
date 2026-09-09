from django.urls import path
from . import views

urlpatterns = [
    path('', views.department_list, name='department_list'),
    path('branch/', views.branch_list, name='branch_list'),
    path('academic-year/<int:pk>/toggle/', views.academic_year_toggle, name='academic_year_toggle'),
    path('academic-year/add/', views.academic_year_add, name='academic_year_add'),
    path('academic-year/<int:pk>/delete/', views.academic_year_delete, name='academic_year_delete'),
]

