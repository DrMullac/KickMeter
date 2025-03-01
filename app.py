import requests
import os
import hashlib
import base64
import secrets
from fastapi import FastAPI, Query, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# ✅ Define FastAPI app
app = FastAPI()

# ✅ Check if 'static/' directory exists before mounting
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")
else:
    print("⚠️ Warning: 'static/' directory does not exist. Skipping mount.")

# ✅ Serve Templates
templates = Jinja2Templates(directory="templates")

# ✅ Add CORS support to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to your actual domain for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Kick API Credentials (User OAuth Only)
CLIENT_ID = "YOUR_CORRECT_CLIENT_ID"  # ✅ Replace with your correct Kick client ID
CLIENT_SECRET = "YOUR_CORRECT_CLIENT_SECRET"  # ✅ Replace with your correct Kick secret
REDIRECT_URI = "https://kickmeter.onrender.com/callback"  # ✅ Must match Kick Developer Portal

# ✅ PKCE Code Verifier & Challenge
CODE_VERIFIER = secrets.token_urlsafe(64)  # Generate a secure random string
CODE_CHALLENGE = base64.urlsafe_b64encode(
    hashlib.sha256(CODE_VERIFIER.encode()).digest()
).decode().rstrip("=")  # SHA-256 hash & Base64 encode (without padding)

STATE = secrets.token_urlsafe(16)  # Random state for CSRF protection

# ✅ OAuth URLs (Using `id.kick.com`)
AUTH_URL = (
    f"https://id.kick.com/oauth/authorize"
    f"?response_type=code"
    f"&client_id={CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}"
    f"&scope=chat:read user:read"
    f"&code_challenge={CODE_CHALLENGE}"
    f"&code_challenge_method=S256"
    f"&state={STATE}"
)

TOKEN_URL = "https://id.kick.com/oauth/token"  # ✅ Corrected Token URL
KICK_API_URL = "https://kick.com/api/v2/channels/"  # ✅ API requests still use `kick.com`

# ✅ Headers to mimic a real browser request
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

# ✅ Store user access token
access_token = None

@app.get("/")
def serve_homepage(request: Request):
    """Serve the KickMeter homepage (HTML UI)."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login")
def login():
    """Redirects users to Kick login."""
    return RedirectResponse(AUTH_URL)

@app.get("/callback")
def callback(code: str = Query(None), state: str = Query(None)):
    """Handles OAuth callback and exchanges code for a user access token."""
    global access_token

    if not code:
        return JSONResponse({
            "error": "Authorization code missing",
            "message": "Kick did not provide an authorization code. Please try logging in again.",
            "fix": "Ensure your redirect URI in Kick Developer settings is correct."
        }, status_code=400)

    if state != STATE:
        return JSONResponse({
            "error": "State mismatch",
            "message": "The state parameter does not match. Possible CSRF attack."
        }, status_code=400)

    # ✅ Fix: Include `client_secret` in token request
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,  # ✅ Must include client_secret
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": CODE_VERIFIER,
    }

    response = requests.post(TOKEN_URL, data=data, headers=headers)

    try:
        response_json = response.json()
    except requests.exceptions.JSONDecodeError:
        response_json = {"error": "Invalid JSON response from Kick", "raw_response": response.text}

    print(f"🔴 Kick Token Exchange Response: {response.status_code} | {response_json}")

    if response.status_code == 200 and "access_token" in response_json:
        access_token = response_json["access_token"]
        print(f"✅ Authentication successful! Access Token: {access_token}")

        # ✅ Force redirect back to the homepage after login
        return RedirectResponse(url="https://kickmeter.onrender.com/")  

    return JSONResponse({
        "error": "Failed to get access token",
        "status": response.status_code,
        "kick_response": response_json  # ✅ Return full Kick response for debugging
    }, status_code=400)

@app.get("/viewer_count/{username}")
def get_viewer_count(username: str):
    """Fetch the viewer count for a given Kick streamer."""
    global access_token

    if not access_token:
        return RedirectResponse("/login")  # ✅ Forces login if not authenticated

    auth_headers = {
        **HEADERS,
        "Authorization": f"Bearer {access_token}"  # ✅ Use user access token
    }
    
    try:
        response = requests.get(f"{KICK_API_URL}{username}", headers=auth_headers, timeout=5)

        if response.status_code == 200 and response.text.strip():
            data = response.json()
            if "slug" in data:
                return {"username": username, "viewers": data["livestream"]["viewer_count"] if data["livestream"] else 0}
            else:
                return JSONResponse({"error": "User not found"}, status_code=404)

        elif response.status_code == 401:
            print("🔄 Token expired. Redirecting to login...")
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
