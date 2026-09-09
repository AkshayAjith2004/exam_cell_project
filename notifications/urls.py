from django.urls import path
from . import views

urlpatterns = [
    path('', views.notification_list, name='notification_list'),
    path('add/', views.notification_add, name='notification_add'),
    path('<int:pk>/delete/', views.notification_delete, name='notification_delete'),
]
