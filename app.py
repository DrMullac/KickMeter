import requests
from fastapi import FastAPI, Query
from fastapi.responses import RedirectResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os

# ✅ Define FastAPI app
app = FastAPI()

# ✅ Add CORS support to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to your actual domain for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Kick API Credentials (Replace with your actual values)
CLIENT_ID = "01JN5ASN4DBEWWPJV52C2Q0702"
CLIENT_SECRET = "eeb3ddcfb785bb82936bebd07968a9744e7c9fcc69cf925ee8167643554b6fdf"
REDIRECT_URI = "https://kickmeter.onrender.com/callback"
TOKEN_URL = "https://kick.com/oauth2/token"
AUTH_URL = (
    f"https://kick.com/oauth2/authorize?response_type=code"
    f"&client_id={CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}"
    "&scope=public"
)
KICK_API_URL = "https://kick.com/api/v2/channels/"

# ✅ Headers to mimic a real browser request
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://kick.com/",
    "Accept": "application/json",
}

# ✅ Store the access token globally
access_token = None

@app.get("/")
def serve_homepage():
    """Serve the frontend UI."""
    return FileResponse("index.html")

@app.get("/login")
def login():
    """Redirects users to Kick login."""
    return RedirectResponse(AUTH_URL)

@app.get("/callback")
def callback(code: str = Query(None)):
    """Handles OAuth callback and exchanges code for an access token."""
    global access_token

    if not code:
        return JSONResponse({
            "error": "Authorization code missing",
            "message": "Kick did not provide an authorization code. Please try logging in again.",
            "fix": "Make sure your redirect URI in Kick Developer settings is correct."
        }, status_code=400)

    # ✅ Exchange the authorization code for an access token
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }

    response = requests.post(TOKEN_URL, data=data, headers=HEADERS)

    if response.status_code == 200:
        access_token = response.json().get("access_token")
        print(f"✅ Authentication successful! Access Token: {access_token}")
        return JSONResponse({"message": "Authentication successful! You can now use the API."})

    return JSONResponse({
        "error": "Failed to get access token",
        "details": response.text
    }, status_code=400)

@app.get("/viewer_count/{username}")
def get_viewer_count(username: str):
    """Fetch the viewer count for a given Kick streamer."""
    global access_token
    if not access_token:
        return RedirectResponse("/login")  # ✅ Redirects to login page

    auth_headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = requests.get(f"{KICK_API_URL}{username}", headers=auth_headers, timeout=5)

        if response.status_code == 200 and response.text.strip():
            data = response.json()
            if "slug" in data:
                return {"username": username, "viewers": data["livestream"]["viewer_count"] if data["livestream"] else 0}
            else:
                return JSONResponse({"error": "User not found"}, status_code=404)

        elif response.status_code == 401:
            return RedirectResponse("/login")  # ✅ Redirect to login if token expired

        elif response.status_code == 403:
            return JSONResponse({"error": "Kick API is blocking requests. Try again later."}, status_code=403)

        else:
            return JSONResponse({"error": f"Unexpected error (Status: {response.status_code})", "details": response.text}, status_code=500)

    except requests.exceptions.RequestException as e:
        return JSONResponse({"error": "Failed to connect to Kick API", "details": str(e)}, status_code=500)

# ✅ Ensure app is defined before running
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
