from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import requests
import json
from typing import Dict

# Initialize FastAPI app
app = FastAPI(
    title="AI Image Detector API",
    description="Upload an image to check if it was AI-generated or human-made.",
    version="1.0.0"
)

# Function to make API call
def detect_ai_image(file: UploadFile) -> Dict:
    url = "https://api.aiornot.com/v1/reports/image"
    api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjJhMGM4YmI0LTYxOWEtNDY2MC04NjgwLWFjZjhkMmUzNDVmYSIsInVzZXJfaWQiOiIyYTBjOGJiNC02MTlhLTQ2NjAtODY4MC1hY2Y4ZDJlMzQ1ZmEiLCJhdWQiOiJhY2Nlc3MiLCJleHAiOjAuMH0.q_WmfHbQjuPxw8nxKCrmW0bUkGbQ9ILbdGYzHVystsY"

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json'
    }
    files = {
        'object': (file.filename, file.file, file.content_type)
    }

    response = requests.post(url, headers=headers, files=files)

    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Error from AI or Not API: {response.text}"
        )

# Endpoint for uploading and detecting AI-generated images
@app.post("/detect", summary="Detect AI-generated images")
async def detect_image(file: UploadFile = File(...)):
    # Validate file type
    if file.content_type not in ["image/png", "image/jpeg", "image/jpg"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PNG, JPG, and JPEG are supported."
        )
    
    try:
        # Call the detection API
        detection_result = detect_ai_image(file)

        # Extract required information from response
        report = detection_result["report"]
        verdict = report["verdict"]
        ai_confidence = report["ai"]["confidence"]
        human_confidence = report["human"]["confidence"]
        generator_data = report["generator"]

        # Prepare response
        return JSONResponse(
            content={
                "verdict": "AI-Generated" if verdict == "ai" else "Human-Made",
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
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}"
        )
