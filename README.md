AUTOMATIC DETECTION OF FRAUDULENT IMAGE AND DOCUMENTS USING DEEP LEARNING:-

An intelligent, web-based tool designed to analyze and detect digital media manipulation. This application leverages a hybrid model to provide robust analysis for both AI-generated deepfake images and forged documents, including multi-page PDFs.

Key Features:-

* Hybrid Analysis Model: Utilizes a powerful deep learning model (EfficientNet-B7) for detecting deepfake images and a forensic technique (Error Level Analysis - ELA) for document forgery.

* Multi-Format Support: Analyze a wide range of file types, including JPG, PNG, and multi-page PDF documents.

* Interactive Single-Page App (SPA): A modern, user-friendly interface that provides a seamless analysis experience without page reloads.

* Clear Visual Feedback: Analysis results are presented with a full-image color overlay—green for authentic and red for suspicious—making the verdict instantly clear.

* Detailed Reporting: Provides quantitative confidence scores (e.g., DeepFake Score, Forgery Score) and a methodological explanation for each analysis.

* PDF Page-by-Page Analysis: When a PDF is uploaded, the tool analyzes each page individually and presents a detailed report for every page.

Technologies Used
This project is built with a combination of powerful backend and frontend technologies.

Backend
* Python: Core programming language.

* Flask: A lightweight web framework to serve the application and handle API requests.

* PyTorch: The deep learning framework used to run the deepfake detection model.

* timm (PyTorch Image Models): A library for easy access to state-of-the-art pre-trained image models like EfficientNet.

* OpenCV & Pillow (PIL): Essential libraries for advanced image processing, manipulation, and analysis.

* PyMuPDF (fitz): A high-performance library for opening, rendering, and extracting data from PDF documents.

* NumPy: Used for efficient numerical operations on image data.

Frontend
* HTML5: The structure of the web application.

* CSS3: Custom styling for the user interface, animations, and color themes.

* Vanilla JavaScript: Handles all client-side interactivity, API communication (fetch), and dynamic DOM manipulation to create the single-page experience.

Setup and Installation
To run this project locally, please follow these steps.

* Prerequisites
Python 3.8 or newer.

pip (Python package installer).

1. Clone the Repository
git clone (https://github.com/your-username/your-repo-name.git)
cd your-repo-name

2. Create and Activate a Virtual Environment
It is highly recommended to use a virtual environment to manage project dependencies.

Windows:

python -m venv venv
.\venv\Scripts\Activate

3. Install Dependencies
The requirements.txt file contains all the necessary Python packages.

pip install -r requirements.txt

Note: The torch and torchvision libraries are large and may take several minutes to download and install. A stable internet connection is required.

4. Run the Application
Once the dependencies are installed, you can start the Flask server.

python app.py
