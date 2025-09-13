import requests
import os
import logging
import urllib.parse
import re
import json
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
logger = logging.getLogger(__name__)

class EnhancedNutritionAPI:
    """Enhanced nutrition API with multiple data sources"""
    
    def __init__(self):
        self.usda_api_key = os.getenv('USDA_API_KEY')
        self.usda_base_url = 'https://api.nal.usda.gov/fdc/v1'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.timeout = 10
        
        # Cache for web scraping results
        self.scraping_cache = {}
    
    def search_nutrition_usda(self, food_name):
        """Search USDA FoodData Central API"""
        if not self.usda_api_key:
            logger.warning("USDA API key not found, skipping USDA search")
            return None
        
        try:
            # Search for food item
            search_url = f"{self.usda_base_url}/foods/search"
            search_params = {
                'query': food_name,
                'pageSize': 5,
                'api_key': self.usda_api_key
            }
            
            response = requests.get(search_url, params=search_params, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('foods') and len(data['foods']) > 0:
                    # Get the first result
                    food_item = data['foods'][0]
                    fdc_id = food_item.get('fdcId')
                    
                    # Get detailed nutrition data
                    return self._get_detailed_nutrition_usda(fdc_id)
                else:
                    return None
            else:
                logger.error(f"USDA API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"USDA nutrition API error: {e}")
            return None
    
    def _get_detailed_nutrition_usda(self, fdc_id):
        """Get detailed nutrition data for a specific food item from USDA"""
        try:
            detail_url = f"{self.usda_base_url}/food/{fdc_id}"
            params = {'api_key': self.usda_api_key}
            
            response = requests.get(detail_url, params=params, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_usda_nutrition_data(data)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Detailed nutrition API error: {e}")
            return None
    
    def _parse_usda_nutrition_data(self, usda_data):
        """Parse USDA nutrition data into our format"""
        nutrition = {
            'calories': 0,
            'protein': 0,
            'fat': 0,
            'carbs': 0,
            'fiber': 0,
            'sugar': 0,
            'sodium': 0,
            'source': 'usda'
        }
        
        if 'foodNutrients' in usda_data:
            for nutrient in usda_data['foodNutrients']:
                nutrient_name = nutrient.get('nutrient', {}).get('name', '').lower()
                value = nutrient.get('amount', 0)
                
                if 'energy' in nutrient_name and 'kcal' in nutrient_name:
                    nutrition['calories'] = value
                elif 'protein' in nutrient_name:
                    nutrition['protein'] = value
                elif 'total lipid' in nutrient_name or 'fat' in nutrient_name:
                    nutrition['fat'] = value
                elif 'carbohydrate' in nutrient_name:
                    nutrition['carbs'] = value
                elif 'fiber' in nutrient_name:
                    nutrition['fiber'] = value
                elif 'sugar' in nutrient_name:
                    nutrition['sugar'] = value
                elif 'sodium' in nutrient_name:
                    nutrition['sodium'] = value
        
        return nutrition
    
    def search_nutrition_openfoodfacts(self, food_name):
        """Search OpenFoodFacts for nutrition data"""
        try:
            clean = urllib.parse.quote_plus(food_name)
            url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={clean}&search_simple=1&action=process&json=1&page_size=6"
            
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            if response.status_code != 200:
                return None

            data = response.json()
            products = data.get('products', [])
            if not products:
                return None

            # Try to find the best product with nutrition info per 100g
            for product in products:
                nutriments = product.get('nutriments', {})
                if not nutriments:
                    continue

                # Extract nutrition values
                calories = nutriments.get('energy-kcal_100g') or nutriments.get('energy_100g')
                protein = nutriments.get('proteins_100g')
                carbs = nutriments.get('carbohydrates_100g')
                fat = nutriments.get('fat_100g')
                fiber = nutriments.get('fiber_100g')
                sugar = nutriments.get('sugars_100g')
                salt = nutriments.get('salt_100g')

                if any(v is not None for v in [calories, protein, carbs, fat]):
                    def safe_float(x):
                        try:
                            return float(x) if x is not None else 0
                        except (ValueError, TypeError):
                            return 0

                    sodium = 0
                    if salt:
                        try:
                            # Convert salt to sodium (rough conversion: 1g salt ~ 400mg sodium)
                            sodium = safe_float(salt) * 400
                        except:
                            sodium = 0

                    return {
                        'calories': safe_float(calories),
                        'protein': safe_float(protein),
                        'carbs': safe_float(carbs),
                        'fat': safe_float(fat),
                        'fiber': safe_float(fiber),
                        'sugar': safe_float(sugar),
                        'sodium': sodium,
                        'source': 'openfoodfacts'
                    }

            return None
            
        except Exception as e:
            logger.error(f"OpenFoodFacts search failed for {food_name}: {e}")
            return None
    
    def search_nutrition_google(self, food_name):
        """Search nutrition data from Google search results"""
        try:
            clean_name = food_name.lower().strip()
            query = f"{clean_name} nutrition facts calories protein carbs fat per 100g"
            encoded_query = urllib.parse.quote(query)
            
            google_url = f"https://www.google.com/search?q={encoded_query}"
            
            response = requests.get(google_url, headers=self.headers, timeout=self.timeout)
            if response.status_code != 200:
                return None
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for nutrition information in Google's knowledge panel
            nutrition_data = {}
            
            # Try to find calories
            calories_pattern = r'(\d+)\s*(?:calories|kcal|cal)'
            calories_match = re.search(calories_pattern, response.text, re.IGNORECASE)
            if calories_match:
                nutrition_data['calories'] = float(calories_match.group(1))
            
            # Try to find protein
            protein_pattern = r'(\d+(?:\.\d+)?)\s*g?\s*protein'
            protein_match = re.search(protein_pattern, response.text, re.IGNORECASE)
            if protein_match:
                nutrition_data['protein'] = float(protein_match.group(1))
            
            # Try to find carbs
            carbs_pattern = r'(\d+(?:\.\d+)?)\s*g?\s*(?:carb|carbohydrate)'
            carbs_match = re.search(carbs_pattern, response.text, re.IGNORECASE)
            if carbs_match:
                nutrition_data['carbs'] = float(carbs_match.group(1))
            
            # Try to find fat
            fat_pattern = r'(\d+(?:\.\d+)?)\s*g?\s*(?:fat|lipid)'
            fat_match = re.search(fat_pattern, response.text, re.IGNORECASE)
            if fat_match:
                nutrition_data['fat'] = float(fat_match.group(1))
            
            if len(nutrition_data) >= 2:  # If we found at least 2 nutrients
                # Fill in missing values with 0
                nutrition_data.update({
                    'fiber': nutrition_data.get('fiber', 0),
                    'sugar': nutrition_data.get('sugar', 0),
                    'sodium': nutrition_data.get('sodium', 0),
                    'source': 'google_search'
                })
                return nutrition_data
            
        except Exception as e:
            logger.error(f"Google search failed for {food_name}: {e}")
            
        return None
    
    def get_comprehensive_nutrition(self, food_name):
        """Get nutrition data from multiple sources with caching"""
        food_name_clean = food_name.lower().strip()
        
        # Check cache first
        if food_name_clean in self.scraping_cache:
            cache_entry = self.scraping_cache[food_name_clean]
            # Check if cache is fresh (less than 7 days old)
            try:
                cache_time = datetime.fromisoformat(cache_entry['timestamp'])
                if (datetime.now() - cache_time).days < 7:
                    logger.info(f"Using cached nutrition data for: {food_name}")
                    return cache_entry['data']
            except:
                pass
        
        logger.info(f"Searching comprehensive nutrition data for: {food_name}")
        
        # Try different sources in order of preference
        sources = [
            ('USDA', self.search_nutrition_usda),
            ('OpenFoodFacts', self.search_nutrition_openfoodfacts),
            ('Google', self.search_nutrition_google),
        ]
        
        for source_name, source_func in sources:
            try:
                nutrition_data = source_func(food_name)
                if nutrition_data and nutrition_data.get('calories', 0) > 0:
                    logger.info(f"Found nutrition data from {source_name}")
                    
                    # Cache the result
                    self.scraping_cache[food_name_clean] = {
                        'data': nutrition_data,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    return nutrition_data
            except Exception as e:
                logger.error(f"{source_name} source failed: {e}")
                continue
        
        logger.warning(f"No nutrition data found for: {food_name}")
        return self._get_mock_nutrition_data(food_name)
    
    def _get_mock_nutrition_data(self, food_name):
        """Provide mock nutrition data for testing when no data is found"""
        mock_data = {
            'pizza': {'calories': 266, 'protein': 11, 'fat': 10, 'carbs': 33, 'fiber': 2.3, 'sugar': 3.6, 'sodium': 598},
            'hamburger': {'calories': 295, 'protein': 17, 'fat': 14, 'carbs': 28, 'fiber': 2.1, 'sugar': 4.0, 'sodium': 396},
            'burger': {'calories': 295, 'protein': 17, 'fat': 14, 'carbs': 28, 'fiber': 2.1, 'sugar': 4.0, 'sodium': 396},
            'sushi': {'calories': 200, 'protein': 9, 'fat': 7, 'carbs': 28, 'fiber': 1.0, 'sugar': 2.0, 'sodium': 400},
            'chocolate cake': {'calories': 371, 'protein': 4, 'fat': 16, 'carbs': 56, 'fiber': 3.0, 'sugar': 45, 'sodium': 320},
            'cake': {'calories': 371, 'protein': 4, 'fat': 16, 'carbs': 56, 'fiber': 3.0, 'sugar': 45, 'sodium': 320},
            'french fries': {'calories': 365, 'protein': 4, 'fat': 17, 'carbs': 48, 'fiber': 4.0, 'sugar': 0.3, 'sodium': 400},
            'fries': {'calories': 365, 'protein': 4, 'fat': 17, 'carbs': 48, 'fiber': 4.0, 'sugar': 0.3, 'sodium': 400},
            'chicken': {'calories': 239, 'protein': 27, 'fat': 14, 'carbs': 0, 'fiber': 0, 'sugar': 0, 'sodium': 82},
            'ice cream': {'calories': 207, 'protein': 4, 'fat': 11, 'carbs': 24, 'fiber': 0.5, 'sugar': 21, 'sodium': 80},
            'apple': {'calories': 52, 'protein': 0.3, 'fat': 0.2, 'carbs': 14, 'fiber': 2.4, 'sugar': 10.4, 'sodium': 1},
            'banana': {'calories': 89, 'protein': 1.1, 'fat': 0.3, 'carbs': 23, 'fiber': 2.6, 'sugar': 12.2, 'sodium': 1},
            'rice': {'calories': 130, 'protein': 2.7, 'fat': 0.3, 'carbs': 28, 'fiber': 0.4, 'sugar': 0.1, 'sodium': 5},
            'bread': {'calories': 265, 'protein': 9, 'fat': 3.2, 'carbs': 49, 'fiber': 2.7, 'sugar': 5.7, 'sodium': 491},
            'pasta': {'calories': 131, 'protein': 5, 'fat': 1.1, 'carbs': 25, 'fiber': 1.8, 'sugar': 0.8, 'sodium': 6},
            'salad': {'calories': 15, 'protein': 1.4, 'fat': 0.1, 'carbs': 3, 'fiber': 1.3, 'sugar': 1.5, 'sodium': 28},
        }
        
        # Clean food name for lookup
        clean_name = food_name.lower().replace('_', ' ').strip()
        
        # Direct match
        if clean_name in mock_data:
            data = mock_data[clean_name].copy()
            data['source'] = 'mock_data'
            return data
        
        # Partial match
        for key, value in mock_data.items():
            if key in clean_name or clean_name in key:
                data = value.copy()
                data['source'] = 'mock_data'
                return data
        
        # Default fallback
        return {
            'calories': 200,
            'protein': 10,
            'fat': 8,
            'carbs': 25,
            'fiber': 2,
            'sugar': 5,
            'sodium': 100,
            'source': 'default_fallback'
        }