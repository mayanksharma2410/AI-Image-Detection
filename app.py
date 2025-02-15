from fastapi import FastAPI, Request, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="AI Image Detector & WhatsApp Webhook API")

# API Keys and URLs
INTERAKT_API_URL = "https://api.interakt.ai/v1/messages"
INTERAKT_API_KEY = os.getenv("INTERAKT_API_KEY")  # Set this in .env
AI_DETECTION_API_URL = "https://api.aiornot.com/v1/reports/image"
AI_DETECTION_API_KEY = os.getenv("AI_API_KEY")  # Set this in .env

# Function to detect AI-generated images
def detect_ai_image(file: UploadFile):
    headers = {'Authorization': f'Bearer {AI_DETECTION_API_KEY}', 'Accept': 'application/json'}
    files = {'object': (file.filename, file.file, file.content_type)}

    response = requests.post(AI_DETECTION_API_URL, headers=headers, files=files)
    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(status_code=response.status_code, detail=f"Error: {response.text}")

# ✅ API Endpoint to Detect AI-Generated Images
@app.post("/detect", summary="Detect AI-generated images")
async def detect_image(file: UploadFile = File(...)):
    if file.content_type not in ["image/png", "image/jpeg", "image/jpg"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PNG, JPG, and JPEG are supported."
        )

    try:
        detection_result = detect_ai_image(file)

        report = detection_result["report"]
        verdict = "AI-Generated" if report["verdict"] == "ai" else "Human-Made"
        ai_confidence = report["ai"]["confidence"]
        human_confidence = report["human"]["confidence"]
        generator_data = report["generator"]

        return JSONResponse(
            content={
                "verdict": verdict,
                "confidence": {
                    "ai": f"{ai_confidence:.2%}",
                    "human": f"{human_confidence:.2%}"
                },
                "generators": {
                    generator: f"{details['confidence']:.2%}" 
                    for generator, details in generator_data.items()
                }
            },
            status_code=200
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# ✅ Function to send message back to WhatsApp
def send_whatsapp_message(to, message):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {INTERAKT_API_KEY}"
    }
    
    payload = {
        "receiver": to,
        "type": "text",
        "message": message
    }
    
    response = requests.post(INTERAKT_API_URL, headers=headers, json=payload)
    return response.json()

# ✅ WhatsApp Webhook to Handle Image Messages
@app.post("/webhook", summary="WhatsApp Webhook for AI Detection")
async def whatsapp_webhook(request: Request):
    data = await request.json()

    if "type" in data and data["type"] == "image":
        sender_number = data["from"]
        image_url = data["image"]["url"]

        # Download the image
        image_response = requests.get(image_url)
        if image_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to download image")

        files = {"file": ("image.jpg", image_response.content, "image/jpeg")}

        # Send image to AI detection function
        detection_response = requests.post("http://127.0.0.1:8000/detect", files=files)  # Call local /detect endpoint

        if detection_response.status_code == 200:
            result = detection_response.json()

            verdict = result.get("verdict", "Unknown")
            ai_confidence = result["confidence"]["ai"]
            human_confidence = result["confidence"]["human"]
            generators = result.get("generators", {})

            message = (f"🔍 *AI Detection Result:*\n"
                       f"🧐 Verdict: {verdict}\n"
                       f"🤖 AI Confidence: {ai_confidence}\n"
                       f"👤 Human Confidence: {human_confidence}\n"
                       f"🖌 Likely Generators: {', '.join([f'{k}: {v}' for k, v in generators.items()])}")

            # Send response to WhatsApp user
            send_whatsapp_message(sender_number, message)
            return {"status": "success"}
        else:
            return {"error": "Failed to process image"}

    return {"message": "No image received"}
