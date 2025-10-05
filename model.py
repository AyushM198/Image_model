import torch
import timm
import cv2
import numpy as np
from torchvision import transforms
from PIL import Image, ImageChops, ImageEnhance
import os
import fitz  # PyMuPDF

class HybridDeepFakeDetector:
    def __init__(self):
        """Initializes the AI model for deepfake image detection."""
        self.model = timm.create_model('tf_efficientnet_b7_ns', pretrained=True, num_classes=1)
        self.model.eval()
        self.transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

    def predict_image_deepfake(self, image_path, processed_folder):
        """
        Analyzes an image for deepfakes and applies a full-image color overlay based on the result.
        """
        try:
            probability = 0.0
            with Image.open(image_path) as image:
                # Ensure image has 3 channels (RGB)
                rgb_image = image.convert('RGB')
                img_tensor = self.transform(rgb_image).unsqueeze(0)
                with torch.no_grad():
                    output = torch.sigmoid(self.model(img_tensor))
                    probability = output.item()
            
            # Red for fake (probability > 0.5), Green for authentic
            color = (0, 0, 255) if probability > 0.5 else (0, 255, 0)
            highlighted_image_path = self._apply_color_overlay(image_path, processed_folder, color)

            return probability, highlighted_image_path
        except Exception as e:
            print(f"Error in deepfake prediction: {e}")
            return 0.0, None

    def analyze_document_forgery(self, image_path, processed_folder):
        """
        Analyzes a single document image for forgery using ELA and applies a full-image color overlay.
        """
        try:
            TEMP_ELA_FILE = os.path.join(processed_folder, f"ela_temp_{os.path.basename(image_path)}.jpg")
            
            with Image.open(image_path) as original_image:
                original_image.convert('RGB').save(TEMP_ELA_FILE, 'JPEG', quality=95)

            with Image.open(TEMP_ELA_FILE) as resaved_image:
                ela_image = ImageChops.difference(original_image.convert('RGB'), resaved_image)

            extrema = ela_image.getextrema()
            max_diff = max([ex[1] for ex in extrema]) if extrema else 1
            if max_diff == 0: max_diff = 1 # Avoid division by zero
                
            scale = 255.0 / max_diff
            ela_image = ImageEnhance.Brightness(ela_image).enhance(scale)
            ela_array = np.array(ela_image)
            # Scale score to be more intuitive
            forgery_score = min(np.mean(ela_array) / 255.0 * 100 * 2.5, 100.0)

            verdict = "Suspicious Forgery" if forgery_score > 35 else "Authentic"
            # Red for forgery, Green for authentic
            color = (0, 0, 255) if verdict == "Suspicious Forgery" else (0, 255, 0)
            analyzed_image_path = self._apply_color_overlay(image_path, processed_folder, color)
            
            if os.path.exists(TEMP_ELA_FILE):
                os.remove(TEMP_ELA_FILE)

            return forgery_score, verdict, analyzed_image_path
        except Exception as e:
            print(f"Error in document analysis: {e}")
            return 0.0, "Error", None
            
    def analyze_pdf_forgery(self, pdf_path, processed_folder):
        """
        Extracts pages from a PDF, analyzes each page for forgery, and returns a list of results.
        """
        results = []
        try:
            doc = fitz.open(pdf_path)
            base_filename = os.path.splitext(os.path.basename(pdf_path))[0]
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                # Render page to a high-resolution PNG
                pix = page.get_pixmap(dpi=200)
                
                # Define a unique path for the extracted page image
                image_filename = f"{base_filename}_page_{page_num + 1}.png"
                image_path = os.path.join(processed_folder, image_filename)
                pix.save(image_path)
                
                # Analyze the newly created page image
                forgery_score, verdict, analyzed_image_path = self.analyze_document_forgery(image_path, processed_folder)
                
                results.append({
                    'page_number': page_num + 1,
                    'forgery_score': forgery_score,
                    'verdict': verdict,
                    'original_page_image_path': image_path, # Path to the extracted page
                    'analyzed_image_path': analyzed_image_path # Path to the highlighted page
                })
            doc.close()
        except Exception as e:
            print(f"Error processing PDF {pdf_path}: {e}")
        return results

    def _apply_color_overlay(self, image_path, processed_folder, color):
        """Applies a transparent color overlay to the entire image and saves it."""
        try:
            original = cv2.imread(image_path)
            if original is None: 
                print(f"Warning: Could not read image at {image_path}")
                return None
            
            # Create a colored layer of the same size as the original
            color_layer = np.full(original.shape, color, dtype=np.uint8)
            
            # Blend the original image with the colored layer
            alpha = 0.3 
            highlighted_image = cv2.addWeighted(color_layer, alpha, original, 1 - alpha, 0)
            
            # Save the result
            filename = os.path.basename(image_path)
            output_path = os.path.join(processed_folder, f"highlighted_{filename}")
            cv2.imwrite(output_path, highlighted_image)
            return output_path
        except Exception as e:
            print(f"Error applying color overlay: {e}")
            return None

