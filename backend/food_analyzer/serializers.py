from rest_framework import serializers
from .models import FoodAnalysis, UserFeedback, FoodDatabase, SystemStatistics


class FoodAnalysisSerializer(serializers.ModelSerializer):
    macros = serializers.SerializerMethodField()
    micros = serializers.SerializerMethodField()
    serving = serializers.SerializerMethodField()
    sources = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    analysis_metadata = serializers.SerializerMethodField()
    
    class Meta:
        model = FoodAnalysis
        fields = [
            'id', 'food_name', 'confidence', 'serving', 'calories_kcal',
            'macros', 'micros', 'sources', 'image_url', 'analysis_metadata',
            'created_at', 'processing_time'
        ]
    
    def get_macros(self, obj):
        return {
            'protein_g': obj.protein_g or 0,
            'fat_g': obj.fat_g or 0,
            'carbs_g': obj.carbs_g or 0,
            'fiber_g': obj.fiber_g or 0,
        }
    
    def get_micros(self, obj):
        return {
            'sugar_g': obj.sugar_g or 0,
            'sodium_mg': obj.sodium_mg or 0,
            'calcium_mg': None,  # Placeholder for future enhancement
            'iron_mg': None,
            'vitamin_c_mg': None,
        }
    
    def get_sources(self, obj):
        sources = ['Multi-Model AI Detection']
        if obj.data_source:
            source_map = {
                'usda': 'USDA FoodData Central',
                'openfoodfacts': 'OpenFoodFacts Database',
                'google_search': 'Google Nutrition Search',
                'mock_data': 'Built-in Food Database',
                'default_fallback': 'Default Nutrition Values'
            }
            sources.append(source_map.get(obj.data_source, obj.data_source))
        return sources
    
    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return None
    
    def get_serving(self, obj):
        return obj.serving_size or "100g"
    
    def get_analysis_metadata(self, obj):
        return {
            'model_used': obj.model_used,
            'processing_time': obj.processing_time,
            'data_source': obj.data_source,
            'confidence_level': self._get_confidence_level(obj.confidence),
        }
    
    def _get_confidence_level(self, confidence):
        if confidence >= 80:
            return 'high'
        elif confidence >= 60:
            return 'medium'
        else:
            return 'low'


class UserFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFeedback
        fields = [
            'id', 'feedback_type', 'predicted_food', 'correct_food',
            'original_confidence', 'correction_reason', 'user_notes',
            'created_at'
        ]
    
    def create(self, validated_data):
        # Create feedback and update learning cache
        feedback = UserFeedback.objects.create(**validated_data)
        
        # Update learning patterns
        if feedback.feedback_type in ['correction', 'wrong']:
            self._update_learning_cache(feedback)
        
        return feedback
    
    def _update_learning_cache(self, feedback):
        """Update learning cache with new correction pattern"""
        from .models import LearningCache
        
        try:
            cache_entry, created = LearningCache.objects.get_or_create(
                predicted_food=feedback.predicted_food.lower().strip(),
                correct_food=feedback.correct_food.lower().strip(),
                defaults={
                    'average_original_confidence': feedback.original_confidence,
                    'occurrence_count': 1,
                }
            )
            
            if not created:
                # Update existing entry
                cache_entry.occurrence_count += 1
                cache_entry.average_original_confidence = (
                    (cache_entry.average_original_confidence * (cache_entry.occurrence_count - 1) + 
                     feedback.original_confidence) / cache_entry.occurrence_count
                )
                cache_entry.save()
                
        except Exception as e:
            # Log error but don't fail the feedback creation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error updating learning cache: {e}")


class FoodDatabaseSerializer(serializers.ModelSerializer):
    nutrition_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = FoodDatabase
        fields = [
            'id', 'food_name', 'alternative_names', 'category',
            'nutrition_summary', 'data_source', 'data_quality',
            'search_count', 'last_searched', 'created_at'
        ]
    
    def get_nutrition_summary(self, obj):
        return {
            'calories': obj.calories_kcal or 'Unknown',
            'protein': obj.protein_g or 'Unknown',
            'fat': obj.fat_g or 'Unknown',
            'carbs': obj.carbs_g or 'Unknown',
            'fiber': obj.fiber_g or 'Unknown',
            'per_100g': True
        }


class SystemStatisticsSerializer(serializers.ModelSerializer):
    performance_metrics = serializers.SerializerMethodField()
    confidence_breakdown = serializers.SerializerMethodField()
    learning_metrics = serializers.SerializerMethodField()
    
    class Meta:
        model = SystemStatistics
        fields = [
            'id', 'date', 'performance_metrics', 'confidence_breakdown',
            'learning_metrics', 'average_processing_time', 'last_updated'
        ]
    
    def get_performance_metrics(self, obj):
        return {
            'total_predictions': obj.total_predictions,
            'correct_predictions': obj.correct_predictions,
            'accuracy_rate': round(obj.accuracy_rate, 2),
            'nutrition_search_success_rate': round(obj.nutrition_search_success_rate, 2),
        }
    
    def get_confidence_breakdown(self, obj):
        return {
            'high_confidence': {
                'predictions': obj.high_confidence_predictions,
                'accuracy': round(obj.high_confidence_accuracy, 2)
            },
            'medium_confidence': {
                'predictions': obj.medium_confidence_predictions,
                'accuracy': round(obj.medium_confidence_accuracy, 2)
            },
            'low_confidence': {
                'predictions': obj.low_confidence_predictions,
                'accuracy': round(obj.low_confidence_accuracy, 2)
            }
        }
    
    def get_learning_metrics(self, obj):
        return {
            'total_corrections': obj.total_corrections,
            'total_confirmations': obj.total_confirmations,
            'learning_improvement': self._calculate_learning_improvement(obj),
        }
    
    def _calculate_learning_improvement(self, obj):
        """Calculate learning improvement based on corrections vs confirmations"""
        total_feedback = obj.total_corrections + obj.total_confirmations
        if total_feedback > 0:
            confirmation_rate = (obj.total_confirmations / total_feedback) * 100
            return round(confirmation_rate, 2)
        return 0.0


class DetailedAnalysisSerializer(serializers.ModelSerializer):
    """Detailed serializer for comprehensive analysis results"""
    complete_nutrition = serializers.SerializerMethodField()
    confidence_analysis = serializers.SerializerMethodField()
    similar_foods = serializers.SerializerMethodField()
    user_feedback_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = FoodAnalysis
        fields = [
            'id', 'food_name', 'confidence', 'complete_nutrition',
            'confidence_analysis', 'similar_foods', 'user_feedback_summary',
            'model_used', 'processing_time', 'data_source', 'created_at'
        ]
    
    def get_complete_nutrition(self, obj):
        return {
            'per_100g': True,
            'macronutrients': {
                'calories': obj.calories_kcal or 'Unknown',
                'protein': obj.protein_g or 'Unknown',
                'fat': obj.fat_g or 'Unknown',
                'carbohydrates': obj.carbs_g or 'Unknown',
                'fiber': obj.fiber_g or 'Unknown',
            },
            'micronutrients': {
                'sugar': obj.sugar_g or 'Unknown',
                'sodium': obj.sodium_mg or 'Unknown',
            },
            'serving_size': obj.serving_size or '100g'
        }
    
    def get_confidence_analysis(self, obj):
        confidence = obj.confidence
        
        if confidence >= 90:
            level = 'very_high'
            description = 'Extremely confident - Multiple models strongly agree'
        elif confidence >= 80:
            level = 'high'
            description = 'High confidence - Good model agreement'
        elif confidence >= 70:
            level = 'medium_high'
            description = 'Good confidence - Moderate model agreement'
        elif confidence >= 60:
            level = 'medium'
            description = 'Medium confidence - Some uncertainty'
        elif confidence >= 50:
            level = 'low_medium'
            description = 'Low-medium confidence - High uncertainty'
        else:
            level = 'low'
            description = 'Low confidence - Please verify result'
        
        return {
            'level': level,
            'score': confidence,
            'description': description,
            'recommendation': self._get_confidence_recommendation(confidence)
        }
    
    def get_similar_foods(self, obj):
        """Get similar foods from database for comparison"""
        # This would ideally use ML similarity or fuzzy matching
        # For now, return placeholder
        return {
            'found': [],
            'note': 'Similar food suggestions coming soon'
        }
    
    def get_user_feedback_summary(self, obj):
        """Get summary of user feedback for this analysis"""
        feedbacks = obj.feedbacks.all()
        
        if not feedbacks.exists():
            return {'has_feedback': False}
        
        feedback_types = list(feedbacks.values_list('feedback_type', flat=True))
        corrections = feedbacks.filter(feedback_type__in=['correction', 'wrong'])
        
        return {
            'has_feedback': True,
            'feedback_count': feedbacks.count(),
            'feedback_types': feedback_types,
            'has_corrections': corrections.exists(),
            'latest_feedback': feedbacks.first().feedback_type if feedbacks.exists() else None
        }
    
    def _get_confidence_recommendation(self, confidence):
        if confidence >= 80:
            return 'Result is likely accurate. You can trust this detection.'
        elif confidence >= 60:
            return 'Result is probably correct, but please verify if needed.'
        else:
            return 'Low confidence result. Please verify or provide feedback to improve accuracy.'