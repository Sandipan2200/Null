import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications import ResNet50, EfficientNetB3, InceptionV3
from tensorflow.keras.applications.resnet import preprocess_input as resnet_preprocess
from tensorflow.keras.applications.efficientnet import preprocess_input as efficientnet_preprocess
from tensorflow.keras.applications.inception_v3 import preprocess_input as inception_preprocess
from tensorflow.keras.applications.resnet import decode_predictions
from tensorflow.keras.preprocessing import image
from PIL import Image, ImageEnhance, ImageFilter
import os
import logging
from collections import Counter
import requests
from io import BytesIO

logger = logging.getLogger(__name__)

class EnhancedFoodDetector:
    """Enhanced food detector using multiple AI models for better accuracy"""
    
    def __init__(self):
        logger.info("Initializing Enhanced Food Detection System...")
        
        # Load multiple pre-trained models
        self.models = {}
        self.load_models()
        
        # Enhanced food keywords with more specific categories
        self.food_keywords = self.load_comprehensive_food_keywords()
        
        # Model weights for ensemble prediction
        self.model_weights = {
            'resnet50': 0.4,
            'efficientnet': 0.35,
            'inception': 0.25
        }
        
    def load_models(self):
        """Load multiple pre-trained models"""
        try:
            logger.info("Loading ResNet50...")
            self.models['resnet50'] = ResNet50(weights='imagenet', include_top=True)
            
            logger.info("Loading EfficientNetB3...")
            self.models['efficientnet'] = EfficientNetB3(weights='imagenet', include_top=True)
            
            logger.info("Loading InceptionV3...")
            self.models['inception'] = InceptionV3(weights='imagenet', include_top=True)
            
            logger.info("✅ All models loaded successfully!")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            # Fallback to single model
            try:
                self.models['resnet50'] = ResNet50(weights='imagenet', include_top=True)
                self.model_weights = {'resnet50': 1.0}
                logger.info("Fallback: Using only ResNet50")
            except Exception as fallback_error:
                logger.error(f"Fallback model loading failed: {fallback_error}")
                raise
    
    def load_comprehensive_food_keywords(self):
        """Load comprehensive food keywords organized by categories"""
        return {
            # Fruits
            'apple', 'banana', 'orange', 'strawberry', 'grape', 'pineapple',
            'mango', 'peach', 'pear', 'cherry', 'blueberry', 'raspberry',
            'watermelon', 'cantaloupe', 'kiwi', 'papaya', 'coconut',
            
            # Vegetables
            'broccoli', 'carrot', 'tomato', 'potato', 'onion', 'pepper',
            'cucumber', 'lettuce', 'spinach', 'cabbage', 'cauliflower',
            'zucchini', 'eggplant', 'asparagus', 'mushroom', 'corn',
            
            # Proteins
            'chicken', 'beef', 'pork', 'fish', 'salmon', 'tuna',
            'egg', 'tofu', 'beans', 'lentils', 'nuts', 'cheese',
            
            # Grains & Starches
            'rice', 'pasta', 'bread', 'noodle', 'quinoa', 'oats',
            'cereal', 'bagel', 'croissant', 'muffin', 'pancake', 'waffle',
            
            # Fast Food
            'pizza', 'burger', 'hamburger', 'cheeseburger', 'hot_dog',
            'french_fries', 'fries', 'sandwich', 'burrito', 'taco',
            'nachos', 'wings', 'fried_chicken',
            
            # Desserts
            'ice_cream', 'cake', 'cookie', 'donut', 'chocolate',
            'candy', 'pie', 'pudding', 'brownie', 'cupcake',
            
            # Beverages
            'coffee', 'tea', 'soda', 'juice', 'milk', 'smoothie',
            
            # International Cuisine
            'sushi', 'ramen', 'curry', 'biryani', 'dosa', 'naan',
            'dim_sum', 'gyoza', 'tempura', 'pad_thai', 'pho',
            
            # Snacks
            'chips', 'crackers', 'pretzels', 'popcorn', 'granola',
            
            # Soups & Salads
            'soup', 'salad', 'stew', 'chili', 'broth'
        }
    
    def preprocess_image_enhanced(self, img_input):
        """Enhanced image preprocessing with multiple techniques"""
        try:
            # Load image
            if isinstance(img_input, str):
                if img_input.startswith('http'):
                    response = requests.get(img_input, timeout=10)
                    img = Image.open(BytesIO(response.content))
                else:
                    img = Image.open(img_input)
            else:
                # Handle Django UploadedFile or similar
                if hasattr(img_input, 'read'):
                    img_input.seek(0)
                    img = Image.open(img_input)
                else:
                    img = img_input
            
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Apply image enhancements
            enhanced_images = []
            
            # Original image
            enhanced_images.append(('original', img))
            
            # Enhanced contrast
            enhancer = ImageEnhance.Contrast(img)
            enhanced_images.append(('contrast', enhancer.enhance(1.2)))
            
            # Enhanced brightness
            enhancer = ImageEnhance.Brightness(img)
            enhanced_images.append(('brightness', enhancer.enhance(1.1)))
            
            # Sharpened
            enhanced_images.append(('sharp', img.filter(ImageFilter.SHARPEN)))
            
            return enhanced_images, img
            
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            return None, None
    
    def get_model_predictions(self, img_variations):
        """Get predictions from all models on image variations"""
        all_predictions = []
        
        for model_name, model in self.models.items():
            for variation_name, img in img_variations:
                try:
                    # Preprocess based on model type
                    img_array = img.resize((224, 224))
                    img_array = image.img_to_array(img_array)
                    img_array = np.expand_dims(img_array, axis=0)
                    
                    if model_name == 'resnet50':
                        img_array = resnet_preprocess(img_array)
                    elif model_name == 'efficientnet':
                        img_array = efficientnet_preprocess(img_array)
                    elif model_name == 'inception':
                        img_array = inception_preprocess(img_array)
                    
                    # Get predictions
                    predictions = model.predict(img_array, verbose=0)
                    decoded = decode_predictions(predictions, top=10)[0]
                    
                    # Store predictions with metadata
                    for rank, (class_id, class_name, confidence) in enumerate(decoded):
                        all_predictions.append({
                            'model': model_name,
                            'variation': variation_name,
                            'rank': rank,
                            'class_name': class_name,
                            'confidence': float(confidence),
                            'weight': self.model_weights.get(model_name, 0.33)
                        })
                        
                except Exception as e:
                    logger.error(f"Error getting predictions from {model_name}: {e}")
                    continue
        
        return all_predictions
    
    def ensemble_prediction(self, all_predictions):
        """Combine predictions from all models using weighted ensemble"""
        # Group predictions by class name
        class_scores = {}
        
        for pred in all_predictions:
            class_name = pred['class_name']
            confidence = pred['confidence']
            weight = pred['weight']
            
            # Weight by model confidence and model weight
            weighted_score = confidence * weight
            
            if class_name in class_scores:
                class_scores[class_name]['total_score'] += weighted_score
                class_scores[class_name]['count'] += 1
                class_scores[class_name]['max_confidence'] = max(
                    class_scores[class_name]['max_confidence'], confidence
                )
            else:
                class_scores[class_name] = {
                    'total_score': weighted_score,
                    'count': 1,
                    'max_confidence': confidence
                }
        
        # Calculate final scores
        final_predictions = []
        for class_name, data in class_scores.items():
            # Average weighted score with bonus for multiple model agreement
            avg_score = data['total_score'] / data['count']
            agreement_bonus = min(data['count'] / len(self.models), 1.0) * 0.1
            final_score = avg_score + agreement_bonus
            
            final_predictions.append({
                'class_name': class_name,
                'confidence': final_score,
                'max_confidence': data['max_confidence'],
                'model_agreement': data['count']
            })
        
        # Sort by confidence
        final_predictions.sort(key=lambda x: x['confidence'], reverse=True)
        return final_predictions
    
    def extract_food_predictions(self, ensemble_results):
        """Extract food-related predictions from ensemble results"""
        food_predictions = []
        
        for pred in ensemble_results:
            class_name = pred['class_name']
            is_food = any(food_word in class_name.lower().replace('_', ' ') 
                         for food_word in self.food_keywords)
            
            if is_food:
                food_predictions.append({
                    'class_name': class_name.replace('_', ' ').title(),
                    'confidence': pred['confidence'] * 100,  # Convert to percentage
                    'max_confidence': pred['max_confidence'] * 100,
                    'model_agreement': pred['model_agreement']
                })
        
        return food_predictions
    
    def detect_food(self, img_input):
        """Main food detection method with enhanced accuracy"""
        logger.info("🔍 Analyzing image with multiple AI models...")
        
        # Preprocess image
        img_variations, original_img = self.preprocess_image_enhanced(img_input)
        if not img_variations:
            return None, None
        
        # Get predictions from all models
        all_predictions = self.get_model_predictions(img_variations)
        
        if not all_predictions:
            logger.warning("No predictions obtained from models")
            return None, None
        
        # Ensemble prediction
        ensemble_results = self.ensemble_prediction(all_predictions)
        
        # Extract food predictions
        food_predictions = self.extract_food_predictions(ensemble_results)
        
        if not food_predictions:
            return "Unknown Food Item", 0
        
        # Return top prediction
        top_prediction = food_predictions[0]
        
        logger.info(f"🎯 Top prediction: {top_prediction['class_name']} "
                   f"({top_prediction['confidence']:.1f}% confidence, "
                   f"{top_prediction['model_agreement']} models agreed)")
        
        return top_prediction['class_name'], top_prediction['confidence']