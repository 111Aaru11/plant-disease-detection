🌱 AI-Powered Plant Disease Detection System

An intelligent full-stack AI web application that allows farmers and users to upload plant images and receive real-time disease diagnosis, severity analysis, and treatment recommendations.

🔗 Live Demo:
👉 https://petaled-cecil-gleesome.ngrok-free.dev

📌 Problem Statement

Farmers often struggle to identify plant diseases early due to lack of expert access. Misdiagnosis can lead to crop loss and economic damage.

This project aims to provide:

Instant disease identification

Severity analysis

Practical treatment recommendations

Non-plant image validation handling

All through a simple mobile-friendly interface.

🚀 Features

📸 Mobile Camera & Image Upload Support

🧠 AI-based Disease Classification (Vision LLM Integration)

🌿 Automatic Non-Plant Image Detection

📊 Severity Level Analysis (Low / Medium / High / Healthy)

💡 Dynamic Treatment Recommendations

🖼️ Image Annotation with Bounding Box

📦 Structured JSON Response Output

🌍 Live Deployment via Public URL

🏗️ System Architecture

User Upload
↓
Flask Backend (Python)
↓
Gemini Vision API (Disease Understanding)
↓
Post-processing (Severity + Recommendations Engine)
↓
Annotated Image + Structured JSON Output

🛠️ Tech Stack

Python • Flask • Google Gemini Vision API • OpenCV • Pillow • Bootstrap • JavaScript • ngrok • REST APIs

🧠 Machine Learning Journey

Initially, this project used:

CNN-based Classification Model

YOLOv8 Object Detection Model

Challenges faced:

Large-scale bounding box annotation

Dataset bias & class imbalance

Inability to detect non-plant images

CNN predicting diseases for invalid inputs

To improve reliability, the system evolved into a hybrid AI architecture:

Primary ML model for vision processing

Vision LLM for semantic validation & disease reasoning

This improved robustness and real-world applicability.

📊 Performance & Reliability

~90–95% correct disease identification for clear plant images

Automatic detection of non-plant images

Real-time response (2–5 seconds depending on API latency)

Structured JSON output for API consumption

📂 Project Structure
plant-disease-detection/
│
├── uploads/
├── app.py
├── requirements.txt
├── .env
└── README.md

⚙️ Installation (Local Setup)
1️⃣ Clone Repository
git clone https://github.com/your-username/plant-disease-detection.git
cd plant-disease-detection

2️⃣ Create Virtual Environment
python -m venv tf_venv
source tf_venv/bin/activate  # Linux/Mac
tf_venv\Scripts\activate     # Windows

3️⃣ Install Dependencies
pip install -r requirements.txt

4️⃣ Add Gemini API Key

Create a .env file:

GOOGLE_API_KEY=your_api_key_here

5️⃣ Run Server
python app.py


Server runs at:

http://127.0.0.1:5123

🌍 Deployment

Development deployment was done using:

Flask development server

ngrok tunnel for public internet access

Future production-ready deployment plan:

Gunicorn

Nginx

Cloud VM / VPS

🎯 Real-World Impact

This system demonstrates:

Practical smart agriculture application

End-to-end AI product design

ML + Backend + UI integration

Error handling & fallback strategy

Production-ready API architecture

🔮 Future Improvements

Replace external Vision API with custom-trained lightweight model

Add disease confidence scoring

Multi-leaf detection

Database logging of predictions

Farmer dashboard analytics

👩‍💻 Author

Aarushi
AI & Full-Stack Developer
Focused on Applied AI for Real-World Impact
