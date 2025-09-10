import os
import numpy as np
from dotenv import load_dotenv

load_dotenv()

class FoodClassifier:
    def __init__(self):
        self.model_path = os.getenv('MODEL_PATH', 'models/food101_model.h5')
        self.labels_path = os.getenv('LABELS_PATH', 'models/food101_labels.txt')
        self.model = None
        self.labels = self._load_labels()
        self._load_model()
    
    def _load_model(self):
        """Load TensorFlow model or use mock classifier"""
        try:
            import tensorflow as tf
            if os.path.exists(self.model_path):
                self.model = tf.keras.models.load_model(self.model_path)
                print(f"Model loaded successfully from {self.model_path}")
            else:
                print(f"Model file not found at {self.model_path}, using mock classifier")
                self.model = None
        except ImportError:
            print("TensorFlow not available, using mock classifier")
            self.model = None
        except Exception as e:
            print(f"Error loading model: {e}, using mock classifier")
            self.model = None
    
    def _load_labels(self):
        """Load class labels"""
        if os.path.exists(self.labels_path):
            with open(self.labels_path, 'r') as f:
                return [line.strip() for line in f.readlines()]
        else:
            # Food-101 sample labels for testing
            return [
                'apple_pie', 'baby_back_ribs', 'baklava', 'beef_carpaccio', 'beef_tartare',
                'beet_salad', 'beignets', 'bibimbap', 'bread_pudding', 'breakfast_burrito',
                'bruschetta', 'caesar_salad', 'cannoli', 'caprese_salad', 'carrot_cake',
                'ceviche', 'cheese_plate', 'cheesecake', 'chicken_curry', 'chicken_quesadilla',
                'chicken_wings', 'chocolate_cake', 'chocolate_mousse', 'churros', 'clam_chowder',
                'club_sandwich', 'crab_cakes', 'creme_brulee', 'croque_madame', 'cup_cakes',
                'deviled_eggs', 'donuts', 'dumplings', 'edamame', 'eggs_benedict',
                'escargots', 'falafel', 'filet_mignon', 'fish_and_chips', 'foie_gras',
                'french_fries', 'french_onion_soup', 'french_toast', 'fried_calamari', 'fried_rice',
                'frozen_yogurt', 'garlic_bread', 'gnocchi', 'greek_salad', 'grilled_cheese_sandwich',
                'grilled_salmon', 'guacamole', 'gyoza', 'hamburger', 'hot_and_sour_soup',
                'hot_dog', 'huevos_rancheros', 'hummus', 'ice_cream', 'lasagna',
                'lobster_bisque', 'lobster_roll_sandwich', 'macaroni_and_cheese', 'macarons', 'miso_soup',
                'mussels', 'nachos', 'omelette', 'onion_rings', 'oysters',
                'pad_thai', 'paella', 'pancakes', 'panna_cotta', 'peking_duck',
                'pho', 'pizza', 'pork_chop', 'poutine', 'prime_rib',
                'pulled_pork_sandwich', 'ramen', 'ravioli', 'red_velvet_cake', 'risotto',
                'samosa', 'sashimi', 'scallops', 'seaweed_salad', 'shrimp_and_grits',
                'spaghetti_bolognese', 'spaghetti_carbonara', 'spring_rolls', 'steak', 'strawberry_shortcake',
                'sushi', 'tacos', 'takoyaki', 'tiramisu', 'tuna_tartare', 'waffles'
            ]
    
    def predict(self, preprocessed_image):
        """
        Predict food class from preprocessed image
        Returns: (predicted_class, confidence_score)
        """
        if self.model is not None:
            try:
                # Real model prediction
                predictions = self.model.predict(preprocessed_image, verbose=0)
                predicted_class_idx = np.argmax(predictions[0])
                confidence = float(predictions[0][predicted_class_idx])
                
                if predicted_class_idx < len(self.labels):
                    predicted_class = self.labels[predicted_class_idx]
                else:
                    predicted_class = "unknown_food"
                
                return predicted_class, confidence * 100
            except Exception as e:
                print(f"Prediction error: {e}, falling back to mock")
                return self._mock_prediction()
        else:
            return self._mock_prediction()
    
    def _mock_prediction(self):
        """Mock prediction for testing when model is not available"""
        mock_foods = [
            ('pizza', 92.5),
            ('hamburger', 87.3),
            ('sushi', 94.1),
            ('chocolate_cake', 89.7),
            ('french_fries', 91.2),
            ('chicken_wings', 86.8),
            ('caesar_salad', 83.4),
            ('ice_cream', 95.6)
        ]
        
        # Return a random prediction for testing
        import random
        return random.choice(mock_foods)