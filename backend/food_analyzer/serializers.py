from rest_framework import serializers
from .models import FoodAnalysis

class FoodAnalysisSerializer(serializers.ModelSerializer):
    macros = serializers.SerializerMethodField()
    micros = serializers.SerializerMethodField()
    serving = serializers.SerializerMethodField()
    sources = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = FoodAnalysis
        fields = ['food_name', 'confidence', 'serving', 'calories_kcal', 
                 'macros', 'micros', 'sources', 'image_url']
    
    def get_macros(self, obj):
        return {
            'protein_g': obj.protein_g or 0,
            'fat_g': obj.fat_g or 0,
            'carbs_g': obj.carbs_g or 0,
        }
    
    def get_micros(self, obj):
        # Placeholder for micronutrients
        return {
            'vitamin_c_mg': None,
            'calcium_mg': None,
            'iron_mg': None,
        }
    
    def get_sources(self, obj):
        return ['USDA FoodData Central', 'TensorFlow Food-101']
    
    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return None
    
    def get_serving(self, obj):
        return obj.serving_size or "100g"