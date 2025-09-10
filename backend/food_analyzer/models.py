from django.db import models
from django.utils import timezone

class FoodAnalysis(models.Model):
    image = models.ImageField(upload_to='food_images/')
    food_name = models.CharField(max_length=200)
    confidence = models.FloatField()
    calories_kcal = models.FloatField(null=True, blank=True)
    protein_g = models.FloatField(null=True, blank=True)
    fat_g = models.FloatField(null=True, blank=True)
    carbs_g = models.FloatField(null=True, blank=True)
    serving_size = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.food_name} - {self.confidence:.2f}%"