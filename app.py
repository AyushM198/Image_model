from flask import Flask, request, jsonify, render_template, url_for
import os
from werkzeug.utils import secure_filename
from model import HybridDeepFakeDetector

app = Flask(__name__)

# --- Configuration ---
UPLOAD_FOLDER = 'static/uploads'
PROCESSED_FOLDER = 'static/processed'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

# Create necessary folders if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# --- Model Initialization ---
# Load the detector model once when the application starts
detector = HybridDeepFakeDetector()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Handles the file upload and analysis, returning JSON."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request.'}), 400
    
    file = request.files['file']
    analysis_type = request.form.get('analysis_type')

    if file.filename == '':
        return jsonify({'error': 'No file selected.'}), 400

    if not analysis_type:
        return jsonify({'error': 'No analysis type selected.'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)
        
        file_extension = filename.rsplit('.', 1)[1].lower()

        try:
            # --- PDF Analysis Logic ---
            if file_extension == 'pdf':
                if analysis_type == 'image':
                    return jsonify({'error': 'DeepFake analysis is for images (JPG, PNG), not PDFs.'}), 400
                
                pdf_results = detector.analyze_pdf_forgery(upload_path, app.config['PROCESSED_FOLDER'])
                
                # Convert local paths to URLs for the frontend
                for result in pdf_results:
                    if result.get('original_page_image_path'):
                        result['original_image_url'] = url_for('static', filename=f"processed/{os.path.basename(result['original_page_image_path'])}")
                    if result.get('analyzed_image_path'):
                        result['analyzed_image_url'] = url_for('static', filename=f"processed/{os.path.basename(result['analyzed_image_path'])}")

                return jsonify({
                    'analysis_type': 'pdf',
                    'results': pdf_results,
                    'original_filename': filename
                })

            # --- Image Analysis Logic ---
            elif analysis_type == 'image':
                probability, highlighted_path = detector.predict_image_deepfake(upload_path, app.config['PROCESSED_FOLDER'])
                
                real_score = (1 - probability) * 100
                fake_score = probability * 100
                verdict = "DeepFake Detected" if probability > 0.5 else "Likely Authentic"
                explanation = "The model detected subtle artifacts consistent with AI-generated images." if probability > 0.5 else "The model did not find significant evidence of AI manipulation."
                
                return jsonify({
                    'verdict': verdict,
                    'real_score': f"{real_score:.2f}",
                    'fake_score': f"{fake_score:.2f}",
                    'explanation': explanation,
                    'analysis_type': 'image',
                    'original_image_url': url_for('static', filename=f'uploads/{filename}'),
                    'analyzed_image_url': url_for('static', filename=f'processed/{os.path.basename(highlighted_path)}') if highlighted_path else None
                })

            elif analysis_type == 'document':
                forgery_score, verdict, analyzed_path = detector.analyze_document_forgery(upload_path, app.config['PROCESSED_FOLDER'])
                
                explanation = "ELA detected inconsistencies in JPEG compression levels, suggesting a potential digital modification." if verdict == "Suspicious Forgery" else "The document's compression levels appear consistent, indicating it is likely unmodified."

                return jsonify({
                    'verdict': verdict,
                    'forgery_score': f"{forgery_score:.2f}",
                    'explanation': explanation,
                    'analysis_type': 'document',
                    'original_image_url': url_for('static', filename=f'uploads/{filename}'),
                    'analyzed_image_url': url_for('static', filename=f'processed/{os.path.basename(analyzed_path)}') if analyzed_path else None
                })
            
            else:
                return jsonify({'error': 'Invalid analysis type specified.'}), 400

        except Exception as e:
            print(f"An error occurred during analysis: {e}")
            return jsonify({'error': 'An internal error occurred during processing. Please try again.'}), 500
    
    return jsonify({'error': 'Invalid file type.'}), 400


if __name__ == '__main__':
    app.run(debug=True)

# from fastapi import FastAPI, File, UploadFile, Form, HTTPException
# from fastapi.responses import JSONResponse, FileResponse
# from fastapi.staticfiles import StaticFiles
# from pydantic import BaseModel
# from typing import List
# import os
# import shutil
# from werkzeug.utils import secure_filename
# from pathlib import Path
# from model import HybridDeepFakeDetector # Assuming this is the path to your class

# # --- Configuration ---
# # Use absolute paths relative to the project root for Vercel
# BASE_DIR = Path(__file__).resolve().parent.parent
# STATIC_DIR = BASE_DIR / 'static'
# UPLOAD_FOLDER = STATIC_DIR / 'uploads'
# PROCESSED_FOLDER = STATIC_DIR / 'processed'
# ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

# # Create necessary folders if they don't exist
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# # --- FastAPI App Initialization ---
# app = FastAPI()

# # Mount the static directory for serving files (important for the frontend)
# app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# # --- Model Initialization ---
# # Load the detector model once when the application starts
# try:
#     detector = HybridDeepFakeDetector()
# except Exception as e:
#     print(f"ERROR: Could not load the model: {e}")
#     detector = None

# def allowed_file(filename: str) -> bool:
#     """Checks if the file extension is allowed."""
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# # --- Pydantic Schema for Response ---
# class ImageAnalysisResponse(BaseModel):
#     verdict: str
#     real_score: str
#     fake_score: str | None = None
#     forgery_score: str | None = None
#     explanation: str
#     analysis_type: str
#     original_image_url: str
#     analyzed_image_url: str | None

# class PDFAnalysisResult(BaseModel):
#     original_image_url: str | None
#     analyzed_image_url: str | None
#     page_number: int
#     forgery_score: str
#     verdict: str

# class PDFAnalysisResponse(BaseModel):
#     analysis_type: str
#     results: List[PDFAnalysisResult] # Note: You'll need `from typing import List`
#     original_filename: str

# # --- Routes ---
# @app.get("/")
# async def root():
#     """Simple root endpoint for health check."""
#     return {"message": "DeepFake/Forgery Detection API is running"}

# @app.post("/analyze", response_model=ImageAnalysisResponse | PDFAnalysisResponse)
# async def analyze_file(
#     file: UploadFile = File(...),
#     analysis_type: str = Form(..., description="Specify 'image', 'document', or leave empty for PDF detection")
# ):
#     """Handles the file upload and analysis."""
#    
#     if not file.filename:
#         raise HTTPException(status_code=400, detail="No file selected.")
#    
#     if not analysis_type:
#         raise HTTPException(status_code=400, detail="No analysis type selected.")

#     if not allowed_file(file.filename):
#         raise HTTPException(status_code=400, detail="Invalid file type.")

#     if detector is None:
#         raise HTTPException(status_code=500, detail="Model failed to load.")

#     # 1. Save the uploaded file
#     filename = secure_filename(file.filename)
#     upload_path = UPLOAD_FOLDER / filename
#    
#     try:
#         # FastAPI's UploadFile is async
#         with open(upload_path, "wb") as buffer:
#             shutil.copyfileobj(file.file, buffer)
#            
#     except Exception:
#         raise HTTPException(status_code=500, detail="Could not save the uploaded file.")

#     file_extension = filename.rsplit('.', 1)[1].lower()

#     try:
#         # --- PDF Analysis Logic ---
#         if file_extension == 'pdf':
#             if analysis_type == 'image':
#                raise HTTPException(status_code=400, detail="DeepFake analysis is for images (JPG, PNG), not PDFs.")
#            
#             pdf_results = detector.analyze_pdf_forgery(str(upload_path), str(PROCESSED_FOLDER))
#            
#             # Convert local paths to URLs for the frontend
#             formatted_results = []
#             for result in pdf_results:
#                 original_url = f"/static/processed/{os.path.basename(result['original_page_image_path'])}" if result.get('original_page_image_path') else None
#                 analyzed_url = f"/static/processed/{os.path.basename(result['analyzed_image_path'])}" if result.get('analyzed_image_path') else None

#                 formatted_results.append({
#                     'original_image_url': original_url,
#                     'analyzed_image_url': analyzed_url,
#                     'page_number': result['page_number'],
#                     'forgery_score': f"{result['forgery_score']:.2f}",
#                     'verdict': result['verdict']
#                 })

#             return JSONResponse({
#                 'analysis_type': 'pdf',
#                 'results': formatted_results,
#                 'original_filename': filename
#             })

#         # --- Image/Document Analysis Logic ---
#        
#         elif analysis_type == 'image':
#             probability, highlighted_path = detector.predict_image_deepfake(str(upload_path), str(PROCESSED_FOLDER))
#            
#             real_score = (1 - probability) * 100
#             fake_score = probability * 100
#             verdict = "DeepFake Detected" if probability > 0.5 else "Likely Authentic"
#             explanation = "The model detected subtle artifacts consistent with AI-generated images." if probability > 0.5 else "The model did not find significant evidence of AI manipulation."
#            
#             analyzed_url = f"/static/processed/{os.path.basename(highlighted_path)}" if highlighted_path else None

#             return JSONResponse({
#                 'verdict': verdict,
#                 'real_score': f"{real_score:.2f}",
#                 'fake_score': f"{fake_score:.2f}",
#                 'explanation': explanation,
#                 'analysis_type': 'image',
#                 'original_image_url': f"/static/uploads/{filename}",
#                 'analyzed_image_url': analyzed_url
#             })

#         elif analysis_type == 'document':
#             forgery_score, verdict, analyzed_path = detector.analyze_document_forgery(str(upload_path), str(PROCESSED_FOLDER))
#            
#             explanation = "ELA detected inconsistencies in JPEG compression levels, suggesting a potential digital modification." if verdict == "Suspicious Forgery" else "The document's compression levels appear consistent, indicating it is likely unmodified."

#             analyzed_url = f"/static/processed/{os.path.basename(analyzed_path)}" if analyzed_path else None

#             return JSONResponse({
#                 'verdict': verdict,
#                 'forgery_score': f"{forgery_score:.2f}",
#                 'explanation': explanation,
#                 'analysis_type': 'document',
#                 'original_image_url': f"/static/uploads/{filename}",
#                 'analyzed_image_url': analyzed_url
#             })
#        
#         else:
#             raise HTTPException(status_code=400, detail="Invalid analysis type specified.")

#     except Exception as e:
#         print(f"An error occurred during analysis: {e}")
#         # Clean up the file if an error occurred
#         if upload_path.exists():
#              os.remove(upload_path)
#         raise HTTPException(status_code=500, detail="An internal error occurred during processing. Please try again.")

# # @app.get("/") is for the API only. For the HTML frontend, see the Vercel.json notes below.
