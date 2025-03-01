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
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Kick API Credentials
CLIENT_ID = "01JN5ASN4DBEWWPJV52C2Q0702"  
CLIENT_SECRET = "eeb3ddcfb785bb82936bebd07968a9744e7c9fcc69cf925ee8167643554b6fdf"  
REDIRECT_URI = "https://kickmeter.onrender.com/callback"  

# ✅ PKCE Code Verifier & Challenge
CODE_VERIFIER = secrets.token_urlsafe(64)  
CODE_CHALLENGE = base64.urlsafe_b64encode(
    hashlib.sha256(CODE_VERIFIER.encode()).digest()
).decode().rstrip("=")  

STATE = secrets.token_urlsafe(16)  

# ✅ OAuth URLs
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

TOKEN_URL = "https://id.kick.com/oauth/token"  
KICK_API_URL = "https://kick.com/api/v2/channels/"  
GRAPHQL_URL = "https://kick.com/graphql"  # ✅ GraphQL API endpoint

# ✅ Headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

# ✅ Store user access token
access_token = None

@app.get("/")
def serve_homepage(request: Request):
    """Serve the KickMeter homepage."""
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
        return JSONResponse({"error": "Authorization code missing"}, status_code=400)

    if state != STATE:
        return JSONResponse({"error": "State mismatch"}, status_code=400)

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,  
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": CODE_VERIFIER,
    }

    response = requests.post(TOKEN_URL, data=data, headers=headers)

    try:
        response_json = response.json()
    except requests.exceptions.JSONDecodeError:
        response_json = {"error": "Invalid JSON response from Kick"}

    if response.status_code == 200 and "access_token" in response_json:
        access_token = response_json["access_token"]
        return RedirectResponse(url="https://kickmeter.onrender.com/")  

    return JSONResponse({"error": "Failed to get access token"}, status_code=400)

def get_graphql_viewer_count(username):
    """Fetch real-time viewer count from Kick's GraphQL API."""
    query = {
        "operationName": "StreamInfo",
        "variables": {"slug": username},
        "query": "query StreamInfo($slug: String!) { stream(slug: $slug) { viewerCount } }"
    }
    
    response = requests.post(GRAPHQL_URL, json=query, headers=HEADERS)

    if response.status_code == 200:
        data = response.json()
        if "data" in data and "stream" in data["data"] and data["data"]["stream"]:
            return data["data"]["stream"]["viewerCount"]
    return None

@app.get("/viewer_count/{username}")
def get_viewer_count(username: str):
    """Fetch both Kick API and GraphQL viewer counts."""
    global access_token

    if not access_token:
        return RedirectResponse("/login")  

    auth_headers = {
        **HEADERS,
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        # ✅ Fetch viewer count from Kick API
        api_response = requests.get(f"{KICK_API_URL}{username}", headers=auth_headers, timeout=5)

        if api_response.status_code == 200 and api_response.text.strip():
            api_data = api_response.json()
            api_viewers = api_data["livestream"]["viewer_count"] if api_data["livestream"] else 0
        else:
            api_viewers = None

        # ✅ Fetch viewer count from GraphQL API
        graphql_viewers = get_graphql_viewer_count(username)

        return {
            "username": username,
            "kick_api_viewers": api_viewers,
            "kick_graphql_viewers": graphql_viewers,
        }

    except requests.exceptions.RequestException as e:
        return JSONResponse({"error": "Failed to connect to Kick API", "details": str(e)}, status_code=500)

# ✅ Ensure app is defined before running
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
