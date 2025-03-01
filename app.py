from fastapi import FastAPI
import requests

app = FastAPI()

KICK_API_URL = "https://kick.com/api/v2/channels/"

@app.get("/viewer_count/{username}")
def get_viewer_count(username: str):
    """Fetch viewer count for a Kick streamer"""
    try:
        response = requests.get(f"{KICK_API_URL}{username}")
        if response.status_code == 200:
            data = response.json()
            return {"username": username, "viewers": data["livestream"]["viewer_count"] if data["livestream"] else 0}
        else:
            return {"error": "User not found"}
    except requests.RequestException:
        return {"error": "Failed to connect to Kick API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
