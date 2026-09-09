from django.urls import path
from . import views

urlpatterns = [
    path('generate/', views.generate_seating_view, name='generate_seating'),
    path('details/', views.seating_details, name='seating_details'),
    path('edit/', views.edit_seating, name='edit_seating'),
    path('clear/', views.clear_seating, name='clear_seating'),
    path('clear-all/', views.clear_all_seating, name='clear_all_seating'),
]
