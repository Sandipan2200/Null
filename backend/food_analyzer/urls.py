from django.urls import path
from . import views

urlpatterns = [
    # Main food analysis endpoint
    path('analyze/', views.AnalyzeFoodView.as_view(), name='analyze_food'),
    
    # Feedback and learning endpoints
    path('feedback/', views.FeedbackView.as_view(), name='user_feedback'),
    
    # Statistics and analytics endpoints
    path('stats/', views.SystemStatsView.as_view(), name='system_stats'),
    
    # Food database management
    path('foods/', views.FoodDatabaseView.as_view(), name='food_database'),
    
    # Detailed analysis
    path('analysis/<uuid:analysis_id>/', views.DetailedAnalysisView.as_view(), name='detailed_analysis'),
    
    # Recent analyses
    path('recent/', views.RecentAnalysisView.as_view(), name='recent_analyses'),
    
    # Health check endpoint
    path('health/', views.HealthView.as_view(), name='health'),
]