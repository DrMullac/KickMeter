from fastapi import FastAPI
import requests
import os

app = FastAPI()

KICK_API_URL = "https://kick.com/api/v2/channels/"

# ✅ Root Route - Prevents "Not Found" error
@app.get("/")
def home():
    return {
        "message": "KickMeter API is running. Use /viewer_count/{username} to get live viewer counts.",
        "example": "/viewer_count/xqc"
    }

# ✅ Endpoint to fetch viewer count from Kick API
@app.get("/viewer_count/{username}")
def get_viewer_count(username: str):
    """Fetch current viewer count from Kick API"""
    try:
        response = requests.get(f"{KICK_API_URL}{username}")
        if response.status_code == 200:
            data = response.json()
            return {
                "username": username,
                "viewers": data["livestream"]["viewer_count"] if data["livestream"] else 0
            }
        else:
            return {"error": "User not found"}
    except requests.RequestException:
        return {"error": "Failed to connect to Kick API"}

# ✅ Ensure the app binds to the correct port for Render deployment
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))  # Render assigns a dynamic port
    uvicorn.run(app, host="0.0.0.0", port=port)