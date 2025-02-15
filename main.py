from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import requests
import uvicorn

app = FastAPI(title="AI Image Detector API")

def detect_ai_image(file: UploadFile):
    url = "https://api.aiornot.com/v1/reports/image"
    api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjJhMGM4YmI0LTYxOWEtNDY2MC04NjgwLWFjZjhkMmUzNDVmYSIsInVzZXJfaWQiOiIyYTBjOGJiNC02MTlhLTQ2NjAtODY4MC1hY2Y4ZDJlMzQ1ZmEiLCJhdWQiOiJhY2Nlc3MiLCJleHAiOjAuMH0.q_WmfHbQjuPxw8nxKCrmW0bUkGbQ9ILbdGYzHVystsY"

    headers = {'Authorization': f'Bearer {api_key}', 'Accept': 'application/json'}
    files = {'object': (file.filename, file.file, file.content_type)}

    response = requests.post(url, headers=headers, files=files)
    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(status_code=response.status_code, detail=f"Error: {response.text}")

@app.post("/detect")
async def detect_image(file: UploadFile = File(...)):
    if file.content_type not in ["image/png", "image/jpeg", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Invalid file type.")
    
    try:
        result = detect_ai_image(file)
        return JSONResponse(content=result, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Uncomment if running locally
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)
