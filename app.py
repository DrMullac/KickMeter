import requests
from fastapi import FastAPI, Query
from fastapi.responses import RedirectResponse, JSONResponse
import os

app = FastAPI()

# ✅ Replace with your actual Kick API credentials
CLIENT_ID = "01JN5ASN4DBEWWPJV52C2Q0702"
CLIENT_SECRET = "eeb3ddcfb785bb82936bebd07968a9744e7c9fcc69cf925ee8167643554b6fdf"
REDIRECT_URI = "https://kickmeter.onrender.com/callback"
TOKEN_URL = "https://kick.com/oauth2/token"
AUTH_URL = f"https://kick.com/oauth2/authorize?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=public"
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
def homepage():
    """Redirects to login if not authenticated."""
    global access_token
    if not access_token:
        return RedirectResponse(AUTH_URL)
    return JSONResponse({"message": "You are logged in. Use /viewer_count/{username} to get viewer counts."})

# ✅ Step 1: Redirect user to Kick login
@app.get("/login")
def login():
    return RedirectResponse(AUTH_URL)

# ✅ Step 2: Handle OAuth callback & get access token
@app.get("/callback")
def callback(code: str = Query(None)):
    global access_token
    if not code:
        return JSONResponse({"error": "Authorization code missing"}, status_code=400)

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
    else:
        return JSONResponse({"error": "Failed to get access token", "details": response.text}, status_code=400)

# ✅ Step 3: Use Access Token to Fetch Viewer Count
@app.get("/viewer_count/{username}")
def get_viewer_count(username: str):
    global access_token
    if not access_token:
        return RedirectResponse(AUTH_URL)  # Redirect to login if not authenticated

    auth_headers = {**HEADERS, "Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{KICK_API_URL}{username}", headers=auth_headers, timeout=5)

    if response.status_code == 200 and response.text.strip():
        data = response.json()
        if "slug" in data:
            return {"username": username, "viewers": data["livestream"]["viewer_count"] if data["livestream"] else 0}
        else:
            return JSONResponse({"error": "User not found"}, status_code=404)
    elif response.status_code == 401:
        print("🔄 Token expired. Re-authenticating...")
        return RedirectResponse(AUTH_URL)  # Redirect to login to refresh token
    elif response.status_code == 403:
        return JSONResponse({"error": "Kick API still blocking requests. Try re-authenticating."}, status_code=403)
    else:
        return JSONResponse({"error": f"Unexpected response (Status: {response.status_code})"}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
