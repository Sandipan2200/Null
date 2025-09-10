import cv2
import numpy as np
from PIL import Image
import io

class ImageProcessor:
    @staticmethod
    def preprocess_image(image_file, target_size=(224, 224)):
        """
        Preprocess uploaded image for model prediction
        """
        try:
            # Read image from uploaded file
            image_bytes = image_file.read()
            image_file.seek(0)  # Reset file pointer
            
            # Convert to PIL Image
            pil_image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # Convert PIL to OpenCV format
            opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            # Resize image
            resized = cv2.resize(opencv_image, target_size)
            
            # Normalize pixel values to [0, 1]
            normalized = resized.astype(np.float32) / 255.0
            
            # Add batch dimension
            processed = np.expand_dims(normalized, axis=0)
            
            return processed
            
        except Exception as e:
            raise Exception(f"Image preprocessing failed: {str(e)}")
    
    @staticmethod
    def enhance_image(image_array):
        """
        Apply image enhancement techniques
        """
        # Convert back to uint8 for OpenCV operations
        img_uint8 = (image_array[0] * 255).astype(np.uint8)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        lab = cv2.cvtColor(img_uint8, cv2.COLOR_BGR2LAB)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        lab[:,:,0] = clahe.apply(lab[:,:,0])
        enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        # Normalize back to [0, 1] and add batch dimension
        normalized = enhanced.astype(np.float32) / 255.0
        return np.expand_dims(normalized, axis=0)