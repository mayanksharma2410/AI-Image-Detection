from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import requests
import uvicorn
import os

app = FastAPI(title="AI Image Detector API")

def detect_ai_image(file: UploadFile):
    url = "https://api.aiornot.com/v1/reports/image"
    api_key = os.environ("API_KEY")

    headers = {'Authorization': f'Bearer {api_key}', 'Accept': 'application/json'}
    files = {'object': (file.filename, file.file, file.content_type)}

    response = requests.post(url, headers=headers, files=files)
    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(status_code=response.status_code, detail=f"Error: {response.text}")

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

# Uncomment if running locally
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)
