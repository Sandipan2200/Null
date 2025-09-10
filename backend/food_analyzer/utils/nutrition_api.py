import requests
import os
from dotenv import load_dotenv

load_dotenv()

class NutritionAPI:
    def __init__(self):
        self.usda_api_key = os.getenv('USDA_API_KEY')
        self.usda_base_url = 'https://api.nal.usda.gov/fdc/v1'
    
    def search_nutrition(self, food_name):
        """
        Search for nutrition data using USDA FoodData Central API
        """
        if not self.usda_api_key:
            return self._mock_nutrition_data(food_name)
        
        try:
            # Search for food item
            search_url = f"{self.usda_base_url}/foods/search"
            search_params = {
                'query': food_name,
                'pageSize': 5,
                'api_key': self.usda_api_key
            }
            
            response = requests.get(search_url, params=search_params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('foods') and len(data['foods']) > 0:
                    # Get the first result
                    food_item = data['foods'][0]
                    fdc_id = food_item.get('fdcId')
                    
                    # Get detailed nutrition data
                    return self._get_detailed_nutrition(fdc_id)
                else:
                    return self._mock_nutrition_data(food_name)
            else:
                print(f"USDA API error: {response.status_code}")
                return self._mock_nutrition_data(food_name)
                
        except Exception as e:
            print(f"Nutrition API error: {e}")
            return self._mock_nutrition_data(food_name)
    
    def _get_detailed_nutrition(self, fdc_id):
        """Get detailed nutrition data for a specific food item"""
        try:
            detail_url = f"{self.usda_base_url}/food/{fdc_id}"
            params = {'api_key': self.usda_api_key}
            
            response = requests.get(detail_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_nutrition_data(data)
            else:
                return None
                
        except Exception as e:
            print(f"Detailed nutrition API error: {e}")
            return None
    
    def _parse_nutrition_data(self, usda_data):
        """Parse USDA nutrition data into our format"""
        nutrition = {
            'calories_kcal': 0,
            'protein_g': 0,
            'fat_g': 0,
            'carbs_g': 0,
            'serving_size': '100g'
        }
        
        if 'foodNutrients' in usda_data:
            for nutrient in usda_data['foodNutrients']:
                nutrient_name = nutrient.get('nutrient', {}).get('name', '').lower()
                value = nutrient.get('amount', 0)
                
                if 'energy' in nutrient_name and 'kcal' in nutrient_name:
                    nutrition['calories_kcal'] = value
                elif 'protein' in nutrient_name:
                    nutrition['protein_g'] = value
                elif 'total lipid' in nutrient_name or 'fat' in nutrient_name:
                    nutrition['fat_g'] = value
                elif 'carbohydrate' in nutrient_name:
                    nutrition['carbs_g'] = value
        
        return nutrition
    
    def _mock_nutrition_data(self, food_name):
        """Provide mock nutrition data for testing"""
        mock_data = {
            'pizza': {'calories_kcal': 266, 'protein_g': 11, 'fat_g': 10, 'carbs_g': 33, 'serving_size': '100g'},
            'hamburger': {'calories_kcal': 540, 'protein_g': 25, 'fat_g': 31, 'carbs_g': 40, 'serving_size': '1 burger'},
            'sushi': {'calories_kcal': 200, 'protein_g': 9, 'fat_g': 7, 'carbs_g': 28, 'serving_size': '6 pieces'},
            'chocolate_cake': {'calories_kcal': 371, 'protein_g': 4, 'fat_g': 16, 'carbs_g': 56, 'serving_size': '1 slice'},
            'french_fries': {'calories_kcal': 365, 'protein_g': 4, 'fat_g': 17, 'carbs_g': 48, 'serving_size': '100g'},
            'chicken_wings': {'calories_kcal': 203, 'protein_g': 30, 'fat_g': 8, 'carbs_g': 0, 'serving_size': '100g'},
            'caesar_salad': {'calories_kcal': 158, 'protein_g': 8, 'fat_g': 13, 'carbs_g': 5, 'serving_size': '1 bowl'},
            'ice_cream': {'calories_kcal': 207, 'protein_g': 4, 'fat_g': 11, 'carbs_g': 24, 'serving_size': '100g'},
        }
        
        # Clean food name for lookup
        clean_name = food_name.lower().replace('_', ' ')
        for key, value in mock_data.items():
            if key in clean_name or clean_name in key:
                return value
        
        # Default fallback
        return {
            'calories_kcal': 200,
            'protein_g': 10,
            'fat_g': 8,
            'carbs_g': 25,
            'serving_size': '100g'
        }