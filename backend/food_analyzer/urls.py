from django.urls import path
from . import views

urlpatterns = [
    path('analyze/', views.AnalyzeFoodView.as_view(), name='analyze_food'),
    path('health/', views.HealthView.as_view(), name='health'),
]