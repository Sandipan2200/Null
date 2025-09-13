from django.db import models
from django.contrib.auth.models import User
import uuid


class FoodAnalysis(models.Model):
    """Model to store food analysis results"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.ImageField(upload_to='food_images/', null=True, blank=True)
    food_name = models.CharField(max_length=255)
    confidence = models.FloatField(default=0.0)
    
    # Nutrition data per 100g
    calories_kcal = models.FloatField(null=True, blank=True)
    protein_g = models.FloatField(null=True, blank=True)
    fat_g = models.FloatField(null=True, blank=True)
    carbs_g = models.FloatField(null=True, blank=True)
    fiber_g = models.FloatField(null=True, blank=True)
    sugar_g = models.FloatField(null=True, blank=True)
    sodium_mg = models.FloatField(null=True, blank=True)
    
    serving_size = models.CharField(max_length=100, default="100g")
    
    # Analysis metadata
    model_used = models.CharField(max_length=100, default="multi_model")
    processing_time = models.FloatField(null=True, blank=True)  # in seconds
    data_source = models.CharField(max_length=100, null=True, blank=True)  # usda, openfoodfacts, etc.
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Food Analysis"
        verbose_name_plural = "Food Analyses"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.food_name} - {self.confidence:.1f}% confidence"


class UserFeedback(models.Model):
    """Model to store user feedback for learning"""
    FEEDBACK_TYPES = [
        ('perfect', 'Perfect Detection'),
        ('close', 'Close but not exact'),
        ('wrong', 'Completely Wrong'),
        ('correction', 'Manual Correction'),
        ('confirmation', 'User Confirmation'),
    ]
    
    CORRECTION_REASONS = [
        ('similar_looking', 'Similar looking food'),
        ('different_prep', 'Different preparation'),
        ('wrong_category', 'Wrong category entirely'),
        ('image_quality', 'Image quality issue'),
        ('other', 'Other reason'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    food_analysis = models.ForeignKey(FoodAnalysis, on_delete=models.CASCADE, related_name='feedbacks')
    
    # Feedback details
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPES)
    predicted_food = models.CharField(max_length=255)
    correct_food = models.CharField(max_length=255, null=True, blank=True)
    original_confidence = models.FloatField()
    
    # Additional feedback information
    correction_reason = models.CharField(max_length=20, choices=CORRECTION_REASONS, null=True, blank=True)
    user_notes = models.TextField(null=True, blank=True)
    
    # User information (if available)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "User Feedback"
        verbose_name_plural = "User Feedbacks"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.feedback_type}: {self.predicted_food} → {self.correct_food or 'N/A'}"


class FoodDatabase(models.Model):
    """Enhanced food database with comprehensive nutrition data"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Food identification
    food_name = models.CharField(max_length=255, unique=True)
    alternative_names = models.JSONField(default=list, blank=True)  # List of alternative names
    category = models.CharField(max_length=100, null=True, blank=True)
    
    # Nutrition data (per 100g)
    calories_kcal = models.FloatField(null=True, blank=True)
    protein_g = models.FloatField(null=True, blank=True)
    fat_g = models.FloatField(null=True, blank=True)
    carbs_g = models.FloatField(null=True, blank=True)
    fiber_g = models.FloatField(null=True, blank=True)
    sugar_g = models.FloatField(null=True, blank=True)
    sodium_mg = models.FloatField(null=True, blank=True)
    
    # Additional nutrients
    calcium_mg = models.FloatField(null=True, blank=True)
    iron_mg = models.FloatField(null=True, blank=True)
    vitamin_c_mg = models.FloatField(null=True, blank=True)
    vitamin_a_ug = models.FloatField(null=True, blank=True)
    
    # Data source and quality
    data_source = models.CharField(max_length=100)  # usda, openfoodfacts, manual, etc.
    source_url = models.URLField(null=True, blank=True)
    data_quality = models.CharField(max_length=20, default='good')  # excellent, good, fair, poor
    
    # Usage statistics
    search_count = models.PositiveIntegerField(default=0)
    last_searched = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Food Database Entry"
        verbose_name_plural = "Food Database Entries"
        ordering = ['food_name']
    
    def __str__(self):
        return self.food_name


class SystemStatistics(models.Model):
    """Model to track system performance and learning statistics"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Performance metrics
    total_predictions = models.PositiveIntegerField(default=0)
    correct_predictions = models.PositiveIntegerField(default=0)
    accuracy_rate = models.FloatField(default=0.0)
    
    # Confidence-based metrics
    high_confidence_predictions = models.PositiveIntegerField(default=0)  # >80%
    high_confidence_correct = models.PositiveIntegerField(default=0)
    medium_confidence_predictions = models.PositiveIntegerField(default=0)  # 60-80%
    medium_confidence_correct = models.PositiveIntegerField(default=0)
    low_confidence_predictions = models.PositiveIntegerField(default=0)  # <60%
    low_confidence_correct = models.PositiveIntegerField(default=0)
    
    # Learning metrics
    total_corrections = models.PositiveIntegerField(default=0)
    total_confirmations = models.PositiveIntegerField(default=0)
    
    # Web scraping metrics
    total_nutrition_searches = models.PositiveIntegerField(default=0)
    successful_nutrition_searches = models.PositiveIntegerField(default=0)
    
    # Processing metrics
    average_processing_time = models.FloatField(default=0.0)  # in seconds
    
    # Timestamps
    date = models.DateField(auto_now=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "System Statistics"
        verbose_name_plural = "System Statistics"
        ordering = ['-date']
    
    def __str__(self):
        return f"Stats for {self.date} - {self.accuracy_rate:.1f}% accuracy"
    
    @property
    def high_confidence_accuracy(self):
        if self.high_confidence_predictions > 0:
            return (self.high_confidence_correct / self.high_confidence_predictions) * 100
        return 0.0
    
    @property
    def medium_confidence_accuracy(self):
        if self.medium_confidence_predictions > 0:
            return (self.medium_confidence_correct / self.medium_confidence_predictions) * 100
        return 0.0
    
    @property
    def low_confidence_accuracy(self):
        if self.low_confidence_predictions > 0:
            return (self.low_confidence_correct / self.low_confidence_predictions) * 100
        return 0.0
    
    @property
    def nutrition_search_success_rate(self):
        if self.total_nutrition_searches > 0:
            return (self.successful_nutrition_searches / self.total_nutrition_searches) * 100
        return 0.0


class LearningCache(models.Model):
    """Model to cache learned patterns and corrections"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Pattern identification
    predicted_food = models.CharField(max_length=255)
    correct_food = models.CharField(max_length=255)
    
    # Pattern strength
    occurrence_count = models.PositiveIntegerField(default=1)
    confidence_boost = models.FloatField(default=1.15)  # How much to boost confidence
    
    # Pattern quality
    average_original_confidence = models.FloatField()
    success_rate = models.FloatField(default=100.0)  # Success rate of this correction
    
    # Timestamps
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Learning Cache"
        verbose_name_plural = "Learning Cache"
        unique_together = ['predicted_food', 'correct_food']
        ordering = ['-occurrence_count', '-last_seen']
    
    def __str__(self):
        return f"{self.predicted_food} → {self.correct_food} ({self.occurrence_count}x)"