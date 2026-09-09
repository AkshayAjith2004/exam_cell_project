from django.urls import path
from . import views

urlpatterns = [
    path('print/<str:report_type>/', views.print_report, name='print_report'),
]
