import os
import io
import time
import logging
from PIL import Image as PILImage
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone
from django.db.models import F, Q
from .models import FoodAnalysis, UserFeedback, SystemStatistics, FoodDatabase, LearningCache
from .serializers import (
    FoodAnalysisSerializer, UserFeedbackSerializer, SystemStatisticsSerializer,
    FoodDatabaseSerializer, DetailedAnalysisSerializer
)
from .utils.enhanced_food_detector import EnhancedFoodDetector
from .utils.enhanced_nutrition_api import EnhancedNutritionAPI
from .utils.image_processor import ImageProcessor

logger = logging.getLogger(__name__)


class AnalyzeFoodView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    
    def __init__(self):
        super().__init__()
        self.image_processor = ImageProcessor()
        self.food_detector = EnhancedFoodDetector()
        self.nutrition_api = EnhancedNutritionAPI()
    
    def post(self, request):
        start_time = time.time()
        
        try:
            # Check if image is in the request
            if 'image' not in request.FILES:
                return Response(
                    {'error': 'No image file provided'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            image_file = request.FILES['image']
            
            # Validate image file
            content_type = getattr(image_file, 'content_type', '') or ''
            if not content_type.startswith('image/'):
                try:
                    # Read bytes and attempt to open/verify as an image
                    image_bytes = image_file.read()
                    image_file.seek(0)
                    PILImage.open(io.BytesIO(image_bytes)).verify()
                except Exception:
                    return Response(
                        {'error': 'File must be an image'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Enhanced food detection
            try:
                food_name, confidence = self.food_detector.detect_food(image_file)
                logger.info(f"Detected: {food_name} with confidence: {confidence:.2f}%")
            except Exception as e:
                logger.error(f"Food detection failed: {e}")
                return Response(
                    {'error': f'Food classification failed: {str(e)}'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Apply learning corrections if available
            try:
                corrected_food, confidence = self._apply_learning_corrections(food_name, confidence)
                if corrected_food != food_name:
                    logger.info(f"Applied learning correction: {food_name} → {corrected_food}")
                    food_name = corrected_food
            except Exception as e:
                logger.error(f"Learning correction failed: {e}")
                # Continue with original detection
            
            # Get enhanced nutrition data
            try:
                nutrition_data = self.nutrition_api.get_comprehensive_nutrition(food_name)
                logger.info(f"Retrieved nutrition data from: {nutrition_data.get('source', 'unknown')}")
            except Exception as e:
                logger.error(f"Nutrition lookup error: {e}")
                # Provide fallback nutrition data
                nutrition_data = self._get_fallback_nutrition()
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Save analysis to database
            try:
                food_analysis = FoodAnalysis.objects.create(
                    image=image_file,
                    food_name=food_name,
                    confidence=confidence,
                    calories_kcal=nutrition_data.get('calories', 0),
                    protein_g=nutrition_data.get('protein', 0),
                    fat_g=nutrition_data.get('fat', 0),
                    carbs_g=nutrition_data.get('carbs', 0),
                    fiber_g=nutrition_data.get('fiber', 0),
                    sugar_g=nutrition_data.get('sugar', 0),
                    sodium_mg=nutrition_data.get('sodium', 0),
                    serving_size="100g",
                    model_used="enhanced_multi_model",
                    processing_time=processing_time,
                    data_source=nutrition_data.get('source', 'unknown')
                )
                
                # Update system statistics
                self._update_system_statistics(confidence, processing_time, nutrition_data.get('source'))
                
                # Update food database search count
                self._update_food_database_stats(food_name)
                
            except Exception as e:
                logger.error(f"Database save error: {e}")
                # Continue with response even if DB save fails
                food_analysis = None
            
            # Serialize and return response
            if food_analysis:
                serializer = FoodAnalysisSerializer(food_analysis, context={'request': request})
                response_data = serializer.data
            else:
                # Manual response if DB save failed
                response_data = self._create_manual_response(food_name, confidence, nutrition_data, processing_time)
            
            # Add enhanced analysis information
            response_data['enhanced_analysis'] = {
                'model_ensemble': True,
                'models_used': list(self.food_detector.models.keys()),
                'image_variations_processed': len(self.food_detector.models) * 4,
                'confidence_level': self._get_confidence_level(confidence),
                'processing_time': round(processing_time, 2),
                'nutrition_source': nutrition_data.get('source', 'unknown'),
                'learning_applied': corrected_food != food_name if 'corrected_food' in locals() else False
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Analysis exception: {e}")
            import traceback
            traceback.print_exc()
            
            return Response(
                {
                    'error': f'Analysis failed: {str(e)}',
                    'processing_time': round(processing_time, 2)
                }, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _apply_learning_corrections(self, food_name, confidence):
        """Apply learning corrections based on user feedback"""
        try:
            # Look for learned corrections
            cache_entries = LearningCache.objects.filter(
                predicted_food=food_name.lower().strip()
            ).order_by('-occurrence_count', '-last_seen')
            
            if cache_entries.exists():
                best_correction = cache_entries.first()
                
                # Apply correction with confidence boost
                corrected_name = best_correction.correct_food.title()
                boosted_confidence = min(confidence * best_correction.confidence_boost, 95.0)
                
                logger.info(f"Applied learning: {food_name} → {corrected_name} "
                           f"(confidence: {confidence:.1f}% → {boosted_confidence:.1f}%)")
                
                return corrected_name, boosted_confidence
            
        except Exception as e:
            logger.error(f"Error applying learning corrections: {e}")
        
        return food_name, confidence
    
    def _update_system_statistics(self, confidence, processing_time, data_source):
        """Update system performance statistics"""
        try:
            stats, created = SystemStatistics.objects.get_or_create(
                date=timezone.now().date(),
                defaults={
                    'total_predictions': 0,
                    'correct_predictions': 0,
                    'average_processing_time': 0.0,
                }
            )
            
            # Update prediction counts
            stats.total_predictions += 1
            
            # Update confidence-based metrics
            if confidence >= 80:
                stats.high_confidence_predictions += 1
            elif confidence >= 60:
                stats.medium_confidence_predictions += 1
            else:
                stats.low_confidence_predictions += 1
            
            # Update processing time (moving average)
            if stats.total_predictions == 1:
                stats.average_processing_time = processing_time
            else:
                stats.average_processing_time = (
                    (stats.average_processing_time * (stats.total_predictions - 1) + processing_time) 
                    / stats.total_predictions
                )
            
            # Update nutrition search statistics
            stats.total_nutrition_searches += 1
            if data_source not in ['default_fallback', 'mock_data']:
                stats.successful_nutrition_searches += 1
            
            # Calculate accuracy rate (will be updated by feedback)
            if stats.total_predictions > 0:
                stats.accuracy_rate = (stats.correct_predictions / stats.total_predictions) * 100
            
            stats.save()
            
        except Exception as e:
            logger.error(f"Error updating system statistics: {e}")
    
    def _update_food_database_stats(self, food_name):
        """Update food database search statistics"""
        try:
            food_entry, created = FoodDatabase.objects.get_or_create(
                food_name=food_name.lower().strip(),
                defaults={
                    'search_count': 0,
                    'data_source': 'detection',
                    'category': 'detected',
                }
            )
            
            food_entry.search_count += 1
            food_entry.last_searched = timezone.now()
            food_entry.save()
            
        except Exception as e:
            logger.error(f"Error updating food database stats: {e}")
    
    def _get_fallback_nutrition(self):
        """Provide fallback nutrition data"""
        return {
            'calories': 200,
            'protein': 10,
            'fat': 8,
            'carbs': 25,
            'fiber': 2,
            'sugar': 5,
            'sodium': 100,
            'source': 'fallback'
        }
    
    def _create_manual_response(self, food_name, confidence, nutrition_data, processing_time):
        """Create manual response when database save fails"""
        return {
            'food_name': food_name,
            'confidence': confidence,
            'serving': '100g',
            'calories_kcal': nutrition_data.get('calories', 0),
            'macros': {
                'protein_g': nutrition_data.get('protein', 0),
                'fat_g': nutrition_data.get('fat', 0),
                'carbs_g': nutrition_data.get('carbs', 0),
                'fiber_g': nutrition_data.get('fiber', 0),
            },
            'micros': {
                'sugar_g': nutrition_data.get('sugar', 0),
                'sodium_mg': nutrition_data.get('sodium', 0),
                'calcium_mg': None,
                'iron_mg': None,
                'vitamin_c_mg': None,
            },
            'sources': ['Enhanced Multi-Model AI Detection'],
            'image_url': None,
            'analysis_metadata': {
                'model_used': 'enhanced_multi_model',
                'processing_time': processing_time,
                'data_source': nutrition_data.get('source', 'unknown'),
                'confidence_level': self._get_confidence_level(confidence),
            },
            'created_at': timezone.now(),
            'processing_time': processing_time
        }
    
    def _get_confidence_level(self, confidence):
        """Get confidence level description"""
        if confidence >= 80:
            return 'high'
        elif confidence >= 60:
            return 'medium'
        else:
            return 'low'


class FeedbackView(APIView):
    """Handle user feedback for learning and improvement"""
    
    def post(self, request):
        try:
            # Get the food analysis ID
            analysis_id = request.data.get('analysis_id')
            if not analysis_id:
                return Response(
                    {'error': 'analysis_id is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get the analysis object
            try:
                food_analysis = FoodAnalysis.objects.get(id=analysis_id)
            except FoodAnalysis.DoesNotExist:
                return Response(
                    {'error': 'Food analysis not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Prepare feedback data
            feedback_data = {
                'food_analysis': food_analysis,
                'feedback_type': request.data.get('feedback_type'),
                'predicted_food': food_analysis.food_name,
                'correct_food': request.data.get('correct_food'),
                'original_confidence': food_analysis.confidence,
                'correction_reason': request.data.get('correction_reason'),
                'user_notes': request.data.get('user_notes', ''),
            }
            
            # Add user if authenticated
            if request.user.is_authenticated:
                feedback_data['user'] = request.user
            
            # Create feedback using serializer (which handles learning cache updates)
            serializer = UserFeedbackSerializer(data=feedback_data)
            if serializer.is_valid():
                feedback = serializer.save()
                
                # Update system statistics based on feedback
                self._update_statistics_from_feedback(feedback)
                
                # Return success response
                return Response({
                    'message': 'Feedback recorded successfully',
                    'feedback_id': feedback.id,
                    'learning_updated': True
                }, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'error': 'Invalid feedback data', 'details': serializer.errors}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Feedback processing error: {e}")
            return Response(
                {'error': f'Feedback processing failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _update_statistics_from_feedback(self, feedback):
        """Update system statistics based on user feedback"""
        try:
            stats, created = SystemStatistics.objects.get_or_create(
                date=timezone.now().date(),
                defaults={'total_predictions': 0, 'correct_predictions': 0}
            )
            
            # Update based on feedback type
            if feedback.feedback_type in ['perfect', 'confirmation']:
                # User confirmed the prediction was correct
                stats.correct_predictions += 1
                stats.total_confirmations += 1
                
                # Update confidence-based accuracy
                confidence = feedback.original_confidence
                if confidence >= 80:
                    stats.high_confidence_correct += 1
                elif confidence >= 60:
                    stats.medium_confidence_correct += 1
                else:
                    stats.low_confidence_correct += 1
                    
            elif feedback.feedback_type in ['correction', 'wrong']:
                # User corrected the prediction
                stats.total_corrections += 1
            
            # Recalculate accuracy rate
            if stats.total_predictions > 0:
                stats.accuracy_rate = (stats.correct_predictions / stats.total_predictions) * 100
            
            stats.save()
            
        except Exception as e:
            logger.error(f"Error updating statistics from feedback: {e}")


class SystemStatsView(APIView):
    """Get system performance statistics"""
    
    def get(self, request):
        try:
            # Get latest statistics
            latest_stats = SystemStatistics.objects.first()
            
            if latest_stats:
                serializer = SystemStatisticsSerializer(latest_stats)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                # Return default stats if none exist
                default_stats = {
                    'date': timezone.now().date(),
                    'performance_metrics': {
                        'total_predictions': 0,
                        'correct_predictions': 0,
                        'accuracy_rate': 0.0,
                        'nutrition_search_success_rate': 0.0,
                    },
                    'confidence_breakdown': {
                        'high_confidence': {'predictions': 0, 'accuracy': 0.0},
                        'medium_confidence': {'predictions': 0, 'accuracy': 0.0},
                        'low_confidence': {'predictions': 0, 'accuracy': 0.0}
                    },
                    'learning_metrics': {
                        'total_corrections': 0,
                        'total_confirmations': 0,
                        'learning_improvement': 0.0,
                    }
                }
                return Response(default_stats, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Error fetching system stats: {e}")
            return Response(
                {'error': f'Failed to fetch statistics: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FoodDatabaseView(APIView):
    """Manage food database entries"""
    
    def get(self, request):
        try:
            # Get query parameters
            search = request.GET.get('search', '')
            category = request.GET.get('category', '')
            limit = int(request.GET.get('limit', 50))
            
            # Build query
            queryset = FoodDatabase.objects.all()
            
            if search:
                queryset = queryset.filter(
                    Q(food_name__icontains=search) |
                    Q(alternative_names__icontains=search)
                )
            
            if category:
                queryset = queryset.filter(category=category)
            
            # Limit results
            queryset = queryset[:limit]
            
            serializer = FoodDatabaseSerializer(queryset, many=True)
            
            return Response({
                'count': len(serializer.data),
                'foods': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching food database: {e}")
            return Response(
                {'error': f'Failed to fetch food database: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """Add new food to database"""
        try:
            serializer = FoodDatabaseSerializer(data=request.data)
            if serializer.is_valid():
                food = serializer.save()
                return Response(
                    FoodDatabaseSerializer(food).data, 
                    status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    {'error': 'Invalid food data', 'details': serializer.errors}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Error adding food to database: {e}")
            return Response(
                {'error': f'Failed to add food: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DetailedAnalysisView(APIView):
    """Get detailed analysis with comprehensive information"""
    
    def get(self, request, analysis_id):
        try:
            food_analysis = FoodAnalysis.objects.get(id=analysis_id)
            serializer = DetailedAnalysisSerializer(food_analysis)
            
            # Add additional analysis data
            response_data = serializer.data
            response_data['system_context'] = self._get_system_context()
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except FoodAnalysis.DoesNotExist:
            return Response(
                {'error': 'Analysis not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error fetching detailed analysis: {e}")
            return Response(
                {'error': f'Failed to fetch analysis: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_system_context(self):
        """Get system context information"""
        try:
            stats = SystemStatistics.objects.first()
            return {
                'system_accuracy': stats.accuracy_rate if stats else 0.0,
                'total_predictions': stats.total_predictions if stats else 0,
                'models_available': ['ResNet50', 'EfficientNetB3', 'InceptionV3'],
                'nutrition_sources': ['USDA', 'OpenFoodFacts', 'Google Search'],
                'learning_enabled': True
            }
        except:
            return {
                'system_accuracy': 0.0,
                'total_predictions': 0,
                'models_available': [],
                'nutrition_sources': [],
                'learning_enabled': False
            }


class RecentAnalysisView(APIView):
    """Get recent food analysis results"""
    
    def get(self, request):
        try:
            limit = int(request.GET.get('limit', 20))
            user_only = request.GET.get('user_only', 'false').lower() == 'true'
            
            # Build query
            queryset = FoodAnalysis.objects.all()
            
            # Filter by user if requested and authenticated
            if user_only and request.user.is_authenticated:
                # If you add user field to FoodAnalysis model in future
                pass
            
            # Get recent analyses
            recent_analyses = queryset[:limit]
            
            serializer = FoodAnalysisSerializer(recent_analyses, many=True, context={'request': request})
            
            return Response({
                'count': len(serializer.data),
                'analyses': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching recent analyses: {e}")
            return Response(
                {'error': f'Failed to fetch recent analyses: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class HealthView(APIView):
    """Enhanced health check endpoint with system status"""
    permission_classes = []

    def get(self, request):
        try:
            # Basic health check
            health_status = {
                'status': 'ok',
                'timestamp': timezone.now().isoformat(),
                'version': '2.0.0',
                'service': 'Enhanced Food Detection API'
            }
            
            # Check model availability
            try:
                detector = EnhancedFoodDetector()
                health_status['models'] = {
                    'available': list(detector.models.keys()),
                    'count': len(detector.models),
                    'status': 'loaded'
                }
            except Exception as e:
                health_status['models'] = {
                    'available': [],
                    'count': 0,
                    'status': 'error',
                    'error': str(e)
                }
            
            # Check database connectivity
            try:
                total_analyses = FoodAnalysis.objects.count()
                health_status['database'] = {
                    'status': 'connected',
                    'total_analyses': total_analyses
                }
            except Exception as e:
                health_status['database'] = {
                    'status': 'error',
                    'error': str(e)
                }
            
            # Check nutrition API
            try:
                nutrition_api = EnhancedNutritionAPI()
                health_status['nutrition_api'] = {
                    'status': 'available',
                    'sources': ['USDA', 'OpenFoodFacts', 'Google Search']
                }
            except Exception as e:
                health_status['nutrition_api'] = {
                    'status': 'error',
                    'error': str(e)
                }
            
            return Response(health_status, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)