import os
import io
from PIL import Image as PILImage
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import FoodAnalysis
from .serializers import FoodAnalysisSerializer
from .utils.image_processor import ImageProcessor
from .utils.food_classifier import FoodClassifier
from .utils.nutrition_api import NutritionAPI

class AnalyzeFoodView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    
    def __init__(self):
        super().__init__()
        self.image_processor = ImageProcessor()
        self.food_classifier = FoodClassifier()
        self.nutrition_api = NutritionAPI()
    
    def post(self, request):
        try:
            # Check if image is in the request
            if 'image' not in request.FILES:
                return Response(
                    {'error': 'No image file provided'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            image_file = request.FILES['image']
            
            # Validate image file by content type if present; otherwise try to open it with PIL.
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
            
            # Process image
            try:
                preprocessed_image = self.image_processor.preprocess_image(image_file)
            except Exception as e:
                return Response(
                    {'error': f'Image processing failed: {str(e)}'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Classify food
            try:
                food_name, confidence = self.food_classifier.predict(preprocessed_image)
            except Exception as e:
                return Response(
                    {'error': f'Food classification failed: {str(e)}'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Get nutrition data
            try:
                nutrition_data = self.nutrition_api.search_nutrition(food_name)
            except Exception as e:
                print(f"Nutrition lookup error: {e}")
                # Provide fallback nutrition data
                nutrition_data = {
                    'calories_kcal': 200,
                    'protein_g': 10,
                    'fat_g': 8,
                    'carbs_g': 25,
                    'serving_size': '100g'
                }
            
            # Save to database
            food_analysis = FoodAnalysis.objects.create(
                image=image_file,
                food_name=food_name,
                confidence=confidence,
                calories_kcal=nutrition_data.get('calories_kcal', 0),
                protein_g=nutrition_data.get('protein_g', 0),
                fat_g=nutrition_data.get('fat_g', 0),
                carbs_g=nutrition_data.get('carbs_g', 0),
                serving_size=nutrition_data.get('serving_size', '100g')
            )
            
            # Serialize and return response
            serializer = FoodAnalysisSerializer(food_analysis, context={'request': request})
            
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            print(f"Analysis exception: {e}\n{tb}")
            return Response(
                {'error': f'Analysis failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class HealthView(APIView):
    """Simple health check endpoint used for host discovery and readiness checks."""
    permission_classes = []

    def get(self, request):
        return Response({'status': 'ok'}, status=status.HTTP_200_OK)