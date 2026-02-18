# app.py
import os
import traceback
import json
from flask import Flask, request, jsonify, send_file
from dotenv import load_dotenv
from PIL import Image

# ----------------------
# Config / env
# ----------------------
load_dotenv()
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Import new Gemini SDK
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except Exception:
    genai = None
    types = None
    GEMINI_AVAILABLE = False

# Configure Gemini client
GOOGLE_API_KEY = ""
client = None

if GOOGLE_API_KEY and GEMINI_AVAILABLE:
    try:
        client = genai.Client(api_key=GOOGLE_API_KEY)
        GEMINI_MODEL_NAME = "gemini-2.5-flash"
        print("Gemini configured.")
        gemini_ready = True
    except Exception as e:
        print("Gemini configure failed:", e)
        gemini_ready = False
else:
    gemini_ready = False
    if not GEMINI_AVAILABLE:
        print("google-genai package not installed; Gemini disabled.")

# Cleanup function to properly close client
def cleanup_gemini():
    global client
    if client:
        try:
            # Properly close the client if it has a close method
            if hasattr(client, 'close'):
                client.close()
            elif hasattr(client, 'aclose'):
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(client.aclose())
                    else:
                        asyncio.run(client.aclose())
                except:
                    pass
            client = None
        except Exception as e:
            print(f"Error closing Gemini client: {e}")

import atexit
atexit.register(cleanup_gemini)

app = Flask(__name__)

# ----------------------
# Helper utilities
# ----------------------
def classify_with_gemini(image_path):
    if not gemini_ready:
        return "unknown"

    prompt = (
        "You are an expert plant pathologist. Look at the image and give a single short label "
        "naming the most likely disease and the plant it belongs to "
        "(e.g. 'Wheat : Karnal_bunt', 'Rice : Healthy', 'Tomato : Late_blight'). "
        "Always return exactly '<Plant> : <Disease>' or '<Plant> : healthy'. "
        "If the image does not contain a plant, say 'This image contains no plants. Therefore, I cannot provide a diagnosis.'"
    )

    try:
        img = Image.open(image_path).convert("RGB")

        response = client.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=[prompt, img],
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0)  # disable "thinking" for speed
            ),
        )

        text = response.text.strip()
        return text.splitlines()[0]

    except Exception as e:
        print("Gemini call error:", e)
        return "unknown"

def get_disease_info(disease_classification):
    """Extract structured information from disease classification"""
    if ":" in disease_classification:
        parts = disease_classification.split(":", 1)
        plant = parts[0].strip()
        disease = parts[1].strip()
        severity = "Unknown"
        
        # Determine severity based on disease name
        if disease.lower() == "healthy":
            severity = "Healthy"
        elif any(word in disease.lower() for word in ["blight", "rot", "wilt", "canker"]):
            severity = "High"
        elif any(word in disease.lower() for word in ["spot", "rust", "mildew"]):
            severity = "Medium"
        else:
            severity = "Low to Medium"
            
        return {
            "plant_type": plant,
            "disease_name": disease,
            "severity_level": severity,
            "confidence": "High" if gemini_ready else "Low"
        }
    else:
        return {
            "plant_type": "Unknown",
            "disease_name": disease_classification,
            "severity_level": "Unknown",
            "confidence": "Low"
        }

# ----------------------
# Routes
# ----------------------

@app.route("/")
def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🌱 Plant Disease Detection</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
            :root {
                --primary-green: #2d5016;
                --light-green: #4a7c59;
                --bg-green: #f8fdf8;
                --accent-green: #7cb342;
                --success-green: #4caf50;
                --warning-orange: #ff9800;
                --error-red: #f44336;
            }
            
            body { 
                background: linear-gradient(135deg, var(--bg-green) 0%, #e8f5e8 100%);
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                min-height: 100vh;
            }
            
            .main-container { 
                max-width: 800px; 
                margin: 20px auto; 
                padding: 0 15px;
            }
            
            .header-card {
                background: linear-gradient(135deg, var(--primary-green) 0%, var(--light-green) 100%);
                color: white;
                border-radius: 20px;
                padding: 30px;
                text-align: center;
                margin-bottom: 30px;
                box-shadow: 0 10px 30px rgba(45, 80, 22, 0.3);
            }
            
            .main-card { 
                border-radius: 20px; 
                box-shadow: 0 10px 40px rgba(0,0,0,0.1); 
                background: white;
                overflow: hidden;
            }
            
            .upload-section {
                background: linear-gradient(45deg, #f8f9fa, #e9ecef);
                padding: 30px;
                border-radius: 15px;
                margin: 20px;
                border: 2px dashed var(--accent-green);
                transition: all 0.3s ease;
            }
            
            .upload-section:hover {
                border-color: var(--primary-green);
                background: linear-gradient(45deg, #f1f3f4, #e2e6ea);
            }
            
            #preview { 
                max-width: 100%; 
                max-height: 300px;
                margin-top: 20px; 
                display: none; 
                border-radius: 15px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            }
            
            #loading { 
                display: none; 
                padding: 30px;
                text-align: center;
            }
            
            video { 
                border-radius: 15px; 
                margin-top: 20px; 
                width: 100%; 
                max-height: 300px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            }
            
            .btn-custom {
                border-radius: 50px;
                padding: 12px 30px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 1px;
                transition: all 0.3s ease;
                border: none;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            }
            
            .btn-camera {
                background: linear-gradient(135deg, var(--accent-green), var(--success-green));
                color: white;
            }
            
            .btn-camera:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4);
            }
            
            .btn-analyze {
                background: linear-gradient(135deg, var(--primary-green), var(--light-green));
                color: white;
            }
            
            .btn-analyze:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(45, 80, 22, 0.4);
            }
            
            .file-input-wrapper {
                position: relative;
                overflow: hidden;
                display: inline-block;
                width: 100%;
            }
            
            .file-input-wrapper input[type=file] {
                position: absolute;
                left: -9999px;
            }
            
            .file-input-label {
                display: block;
                padding: 15px;
                background: white;
                border: 2px solid var(--accent-green);
                border-radius: 10px;
                text-align: center;
                cursor: pointer;
                transition: all 0.3s ease;
                color: var(--primary-green);
                font-weight: 500;
            }
            
            .file-input-label:hover {
                background: var(--accent-green);
                color: white;
            }
            
            .result-card {
                margin: 20px;
                border-radius: 15px;
                overflow: hidden;
                animation: slideUp 0.5s ease;
            }
            
            @keyframes slideUp {
                from { opacity: 0; transform: translateY(30px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .disease-header {
                background: linear-gradient(135deg, var(--success-green), var(--accent-green));
                color: white;
                padding: 20px;
                text-align: center;
            }
            
            .disease-header.warning {
                background: linear-gradient(135deg, var(--warning-orange), #ffa726);
            }
            
            .disease-header.error {
                background: linear-gradient(135deg, var(--error-red), #e57373);
            }
            
            .info-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                padding: 20px;
                background: #f8f9fa;
            }
            
            .info-item {
                background: white;
                padding: 15px;
                border-radius: 10px;
                text-align: center;
                border-left: 4px solid var(--accent-green);
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            
            .info-item h6 {
                color: #6c757d;
                font-size: 0.8rem;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 5px;
            }
            
            .info-item .value {
                color: var(--primary-green);
                font-weight: 600;
                font-size: 1.1rem;
            }
            
            .severity-high { border-left-color: var(--error-red); }
            .severity-medium { border-left-color: var(--warning-orange); }
            .severity-low { border-left-color: var(--success-green); }
            .severity-healthy { border-left-color: var(--success-green); }
            
            .json-section {
                background: #2d3748;
                color: #e2e8f0;
                padding: 20px;
                margin: 20px;
                border-radius: 15px;
                position: relative;
            }
            
            .json-toggle {
                position: absolute;
                top: 15px;
                right: 15px;
                background: #4a5568;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 5px;
                font-size: 0.8rem;
                cursor: pointer;
            }
            
            .json-content {
                font-family: 'Courier New', monospace;
                font-size: 0.9rem;
                line-height: 1.4;
                white-space: pre-wrap;
                max-height: 300px;
                overflow-y: auto;
            }
            
            .json-collapsed {
                max-height: 100px;
                overflow: hidden;
            }
            
            .spinner-custom {
                width: 3rem;
                height: 3rem;
                border: 0.4rem solid #f3f3f3;
                border-top: 0.4rem solid var(--accent-green);
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .no-camera {
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                color: #856404;
                padding: 15px;
                border-radius: 10px;
                text-align: center;
                margin-bottom: 20px;
            }
            
            @media (max-width: 768px) {
                .main-container { margin: 10px; padding: 0 10px; }
                .header-card { padding: 20px; margin-bottom: 20px; }
                .upload-section { margin: 15px; padding: 20px; }
                .info-grid { grid-template-columns: 1fr; }
            }
        </style>
    </head>
    <body>
        <div class="main-container">
            <div class="header-card">
                <h1><i class="fas fa-leaf"></i> Plant Disease Detection</h1>
                <p class="mb-0">AI-powered plant health analysis using advanced image recognition</p>
            </div>

            <div class="main-card">
                <div class="upload-section">
                    <h4 class="text-center mb-4"><i class="fas fa-camera"></i> Capture or Upload Image</h4>
                    
                    <!-- Camera Section -->
                    <div id="cameraSection">
                        <video id="video" autoplay playsinline class="d-block mx-auto"></video>
                        <div class="text-center mt-3">
                            <button type="button" id="snap" class="btn btn-camera btn-custom">
                                <i class="fas fa-camera"></i> Capture Photo
                            </button>
                        </div>
                    </div>
                    
                    <div id="noCameraMessage" class="no-camera" style="display: none;">
                        <i class="fas fa-exclamation-triangle"></i> Camera access unavailable. Please use file upload below.
                    </div>
                    
                    <canvas id="canvas" style="display:none;"></canvas>

                    <!-- File Upload Section -->
                    <form id="uploadForm" action="/analyze" method="post" enctype="multipart/form-data" class="mt-4">
                        <div class="file-input-wrapper">
                            <input type="file" id="fileInput" name="file" accept="image/*" onchange="previewFile(event)">
                            <label for="fileInput" class="file-input-label">
                                <i class="fas fa-cloud-upload-alt fa-2x mb-2"></i><br>
                                <strong>Choose Image File</strong><br>
                                <small>or drag and drop here</small>
                            </label>
                        </div>
                        
                        <div class="text-center mt-3">
                            <img id="preview" class="img-fluid">
                        </div>
                        
                        <div class="text-center mt-4">
                            <button class="btn btn-analyze btn-custom" type="submit">
                                <i class="fas fa-search"></i> Analyze Plant
                            </button>
                        </div>
                    </form>
                </div>

                <div id="loading" class="text-center">
                    <div class="spinner-custom mx-auto"></div>
                    <h5 class="mt-3"><i class="fas fa-microscope"></i> Analyzing Plant Health...</h5>
                    <p class="text-muted">This may take a few seconds</p>
                </div>
                
                <div id="result"></div>
            </div>
        </div>

        <script>
            const video = document.getElementById('video');
            const canvas = document.getElementById('canvas');
            const snap = document.getElementById('snap');
            const preview = document.getElementById('preview');
            const form = document.getElementById("uploadForm");
            const fileInput = document.getElementById("fileInput");
            const cameraSection = document.getElementById('cameraSection');
            const noCameraMessage = document.getElementById('noCameraMessage');

            let capturedFile = null;

            // Access camera
            navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } })
                .then(stream => { 
                    video.srcObject = stream; 
                })
                .catch(err => { 
                    console.error("Camera access denied:", err);
                    cameraSection.style.display = 'none';
                    noCameraMessage.style.display = 'block';
                });

            // Capture photo
            snap.addEventListener('click', () => {
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                canvas.getContext('2d').drawImage(video, 0, 0);

                canvas.toBlob(blob => {
                    capturedFile = new File([blob], "capture.jpg", { type: "image/jpeg" });
                    preview.src = URL.createObjectURL(capturedFile);
                    preview.style.display = "block";
                    fileInput.value = '';
                }, 'image/jpeg');
            });

            // File input preview
            function previewFile(event) {
                const file = event.target.files[0];
                if (file) {
                    preview.src = URL.createObjectURL(file);
                    preview.style.display = "block";
                    capturedFile = null;
                }
            }

            // Drag and drop functionality
            const uploadSection = document.querySelector('.upload-section');
            
            uploadSection.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadSection.style.borderColor = 'var(--primary-green)';
                uploadSection.style.background = 'linear-gradient(45deg, #e8f5e8, #d4edda)';
            });
            
            uploadSection.addEventListener('dragleave', (e) => {
                e.preventDefault();
                uploadSection.style.borderColor = 'var(--accent-green)';
                uploadSection.style.background = 'linear-gradient(45deg, #f8f9fa, #e9ecef)';
            });
            
            uploadSection.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadSection.style.borderColor = 'var(--accent-green)';
                uploadSection.style.background = 'linear-gradient(45deg, #f8f9fa, #e9ecef)';
                
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    fileInput.files = files;
                    previewFile({ target: { files: files } });
                }
            });

            // Form submit
            form.addEventListener("submit", function(e) {
                e.preventDefault();
                
                const fileFromInput = fileInput.files[0];
                const fileToSend = capturedFile || fileFromInput;
                
                if (!fileToSend) {
                    alert("Please select a file or capture a photo first.");
                    return;
                }
                
                document.getElementById("loading").style.display = "block";
                document.getElementById("result").innerHTML = "";

                const fd = new FormData();
                fd.append('file', fileToSend);

                fetch("/analyze", { method: "POST", body: fd })
                    .then(res => {
                        if (!res.ok) {
                            throw new Error(`HTTP ${res.status}: ${res.statusText}`);
                        }
                        return res.text();
                    })
                    .then(html => {
                        document.getElementById("loading").style.display = "none";
                        document.getElementById("result").innerHTML = html;
                    })
                    .catch(err => {
                        console.error("Upload error:", err);
                        document.getElementById("loading").style.display = "none";
                        document.getElementById("result").innerHTML = 
                            `<div class="result-card">
                                <div class="alert alert-danger m-3">
                                    <i class="fas fa-exclamation-circle"></i> Error: ${err.message}
                                </div>
                            </div>`;
                    });
            });
            
            // JSON toggle functionality
            function toggleJson(button) {
                const content = button.nextElementSibling;
                const isCollapsed = content.classList.contains('json-collapsed');
                
                if (isCollapsed) {
                    content.classList.remove('json-collapsed');
                    button.textContent = 'Collapse';
                } else {
                    content.classList.add('json-collapsed');
                    button.textContent = 'Expand';
                }
            }
        </script>
    </body>
    </html>
    """

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        print("Request files:", request.files)
        print("Request form:", request.form)
        
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]
        print(f"File object: {file}")
        print(f"Filename: {file.filename}")
        print(f"Content type: {file.content_type}")
        
        if not file or file.filename == "":
            return jsonify({"error": "Empty filename or no file selected"}), 400

        # Generate a unique filename to avoid conflicts
        import uuid
        file_extension = os.path.splitext(file.filename)[1] or '.jpg'
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        print(f"Saving file to: {filepath}")
        file.save(filepath)

        if not os.path.exists(filepath):
            return jsonify({"error": "Failed to save uploaded file"}), 500

        disease_name = classify_with_gemini(filepath) or "unknown"
        print(f"Disease classification: {disease_name}")
        
        # Get structured disease information
        disease_info = get_disease_info(disease_name)

        # If no plant, return only message + JSON
        if "no plant" in disease_name.lower() or "cannot provide a diagnosis" in disease_name.lower():
            response_json = {
                "status": "no_plant_detected",
                "message": disease_name,
                "detection": [],
                "annotated_image": None,
                "analysis": disease_info
            }
            
            if request.args.get("format") == "json" or request.headers.get("Accept","").lower().find("application/json") != -1:
                return jsonify(response_json)
                
            html = f"""
            <div class="result-card">
                <div class="disease-header error">
                    <h3><i class="fas fa-exclamation-triangle"></i> No Plant Detected</h3>
                    <p class="mb-0">{disease_name}</p>
                </div>
                <div class="p-4 text-center">
                    <i class="fas fa-seedling fa-3x text-muted mb-3"></i>
                    <h5>Please upload an image containing a plant for analysis</h5>
                    <p class="text-muted">Make sure the plant is clearly visible and well-lit in the image.</p>
                </div>
                <div class="json-section">
                    <button class="json-toggle" onclick="toggleJson(this)">Expand</button>
                    <div class="json-content json-collapsed">{json.dumps(response_json, indent=2)}</div>
                </div>
            </div>
            """
            return html

        # For plant images, annotate full image
        annotated_image_path = None
        detections = []
        
        try:
            import cv2
            img_cv = cv2.imread(filepath)
            if img_cv is None:
                raise Exception("Could not read image file")
                
            h, w = img_cv.shape[:2]
            x1, y1, x2, y2 = 20, 20, w - 20, h - 20

            # Draw bounding box + label
            cv2.rectangle(img_cv, (x1, y1), (x2, y2), (0, 255, 0), 3)
            from cv2 import FONT_HERSHEY_SIMPLEX, LINE_AA, putText, getTextSize, rectangle
            text = disease_name
            (tw, th), baseline = getTextSize(text, FONT_HERSHEY_SIMPLEX, 0.8, 2)
            rectangle(img_cv, (x1, y1 - th - 10), (x1 + tw + 10, y1), (0, 255, 0), -1)
            putText(img_cv, text, (x1 + 5, y1 - 5), FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2, LINE_AA)

            output_name = "result_" + unique_filename
            output_path = os.path.join(UPLOAD_FOLDER, output_name)
            cv2.imwrite(output_path, img_cv)
            annotated_image_path = f"/uploads/{output_name}"
            detections = [{"bbox_xyxy": [float(x1), float(y1), float(x2), float(y2)], "disease": disease_name}]
        except Exception as cv_error:
            print(f"OpenCV error: {cv_error}")

        # JSON output
        response_json = {
            "status": "success",
            "disease": disease_name,
            "detection": detections,
            "annotated_image": annotated_image_path,
            "analysis": disease_info,
            "recommendations": get_recommendations(disease_info)
        }

        # Determine severity class for styling
        severity_class = ""
        header_class = ""
        if disease_info["severity_level"] == "Healthy":
            severity_class = "severity-healthy"
            header_class = ""
        elif disease_info["severity_level"] == "High":
            severity_class = "severity-high"
            header_class = "warning"
        elif disease_info["severity_level"] == "Medium":
            severity_class = "severity-medium"
            header_class = "warning"
        else:
            severity_class = "severity-low"
            header_class = ""

        # HTML output with improved UI
        html = f"""
        <div class="result-card">
            <div class="disease-header {header_class}">
                <h3><i class="fas fa-microscope"></i> Analysis Complete</h3>
                <h4>{disease_name}</h4>
            </div>
            
            <div class="info-grid">
                <div class="info-item">
                    <h6><i class="fas fa-seedling"></i> Plant Type</h6>
                    <div class="value">{disease_info['plant_type']}</div>
                </div>
                <div class="info-item">
                    <h6><i class="fas fa-virus"></i> Condition</h6>
                    <div class="value">{disease_info['disease_name']}</div>
                </div>
                <div class="info-item {severity_class}">
                    <h6><i class="fas fa-exclamation-circle"></i> Severity</h6>
                    <div class="value">{disease_info['severity_level']}</div>
                </div>
                <div class="info-item">
                    <h6><i class="fas fa-chart-line"></i> Confidence</h6>
                    <div class="value">{disease_info['confidence']}</div>
                </div>
            </div>
            
            {"<div class='text-center p-3'><img src='"+annotated_image_path+"' class='img-fluid rounded shadow' style='max-width: 100%; max-height: 400px;'></div>" if annotated_image_path else ""}
            
            <div class="p-3">
                <h5><i class="fas fa-lightbulb"></i> Recommendations</h5>
                <div class="alert alert-info">
                    {"<br>".join(get_recommendations(disease_info))}
                </div>
            </div>
            
            <div class="json-section">
                <button class="json-toggle" onclick="toggleJson(this)">Expand</button>
                <div class="json-content json-collapsed">{json.dumps(response_json, indent=2)}</div>
            </div>
        </div>
        """
        return html

    except Exception as e:
        print("Error in analyze route:")
        traceback.print_exc()
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500

def get_recommendations(disease_info):
    """Generate recommendations based on disease analysis"""
    recommendations = []
    
    plant_type = disease_info['plant_type'].lower()
    disease_name = disease_info['disease_name'].lower()
    severity = disease_info['severity_level'].lower()
    
    if disease_name == "healthy":
        recommendations = [
            "🌿 Great! Your plant appears to be healthy.",
            "💧 Continue regular watering and maintenance schedule.",
            "☀️ Ensure adequate sunlight and proper ventilation.",
            "🔍 Monitor regularly for any changes in appearance."
        ]
    elif "blight" in disease_name:
        recommendations = [
            "🚨 Immediate action required - this is a serious fungal disease.",
            "✂️ Remove and destroy affected plant parts immediately.",
            "💊 Apply appropriate fungicide treatment.",
            "🌬️ Improve air circulation around the plant.",
            "💧 Avoid overhead watering to reduce humidity."
        ]
    elif "spot" in disease_name or "rust" in disease_name:
        recommendations = [
            "🔍 Monitor the affected areas closely.",
            "✂️ Remove affected leaves to prevent spread.",
            "💊 Consider applying fungicide if spreading continues.",
            "💧 Water at soil level to avoid wet leaves.",
            "🌱 Ensure proper plant spacing for air circulation."
        ]
    elif "wilt" in disease_name:
        recommendations = [
            "💧 Check soil moisture - may indicate watering issues.",
            "🌡️ Ensure proper temperature conditions.",
            "🦠 May require bacterial or fungal treatment.",
            "✂️ Remove severely affected parts.",
            "🏥 Quarantine from other plants if infectious."
        ]
    else:
        recommendations = [
            "🔍 Continue monitoring the plant's condition.",
            "📚 Research specific treatment for this condition.",
            "🌱 Maintain good plant hygiene practices.",
            "💧 Ensure proper watering schedule.",
            "🌞 Check if plant is getting adequate light.",
            "🏥 Consult with local agricultural extension service if symptoms persist."
        ]
    
    return recommendations
if __name__ == "__main__":
    print("Starting Flask server...")
    app.run(host="0.0.0.0", port=5123, debug=True)
