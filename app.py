import os
import requests
import hashlib
import base64
import secrets
from flask import Flask, request, redirect, session, render_template, jsonify

# Flask App Setup
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Secret key for session management

# OAuth Credentials (Replace with your actual Kick API credentials)
CLIENT_ID = "01JN5ASN4DBEWWPJV52C2Q0702"
CLIENT_SECRET = "eeb3ddcfb785bb82936bebd07968a9744e7c9fcc69cf925ee8167643554b6fdf"
REDIRECT_URI = "https://kickmeter.onrender.com/callback"  # Ensure this matches your Kick API settings
AUTH_URL = "https://id.kick.com/oauth/authorize"
TOKEN_URL = "https://id.kick.com/oauth/token"
KICK_API_BASE_URL = "https://api.kick.com"

# Generate PKCE Code Verifier & Challenge
def generate_pkce_pair():
    code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode('utf-8').rstrip('=')
    sha256 = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(sha256).decode('utf-8').rstrip('=')
    return code_verifier, code_challenge

@app.route('/')
def home():
    return render_template('index.html')  # Renders the input form

@app.route('/login')
def login():
    code_verifier, code_challenge = generate_pkce_pair()
    session['code_verifier'] = code_verifier  # Store for later use

    auth_url = (
        f"https://kick.com/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=read_stream&response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=USER_READ"
        f"&code_challenge={code_challenge}"
        f"&code_challenge_method=S256"
        f"&state={secrets.token_urlsafe(16)}"
    )
    return redirect(auth_url)

@app.route('/callback')
def callback():
    # Retrieve the code and state from the callback URL
    code = request.args.get('code')
    state = request.args.get('state')  # Get the state parameter
    print(f"Callback received with code: {code} and state: {state}")

    if not code:
        return "Authorization failed! No code returned from Kick.", 400

    # Check if the state matches the one we sent in the login request
    if state != session.get('state'):
        return "State mismatch! Potential CSRF attack.", 400

    code_verifier = session.pop('code_verifier', None)  # Retrieve stored verifier
    if not code_verifier:
        return "Code verifier missing!", 400

    # Exchange the code for an access token
    token_response = requests.post(TOKEN_URL, data={
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": code_verifier
    }).json()

    print(f"Token response: {token_response}")  # Log the token response for debugging

    if 'access_token' not in token_response:
        return f"Error fetching access token: {token_response}", 400

    session['access_token'] = token_response['access_token']
    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/viewer-count', methods=['GET'])
def viewer_count():
    stream_id = request.args.get('stream_id')
    if not stream_id:
        return jsonify({"error": "Stream ID is required"}), 400

    access_token = session.get('access_token')
    if not access_token:
        return redirect('/login')

    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{KICK_API_BASE_URL}/streams/{stream_id}", headers=headers)

    if response.status_code == 200:
        data = response.json()
        viewer_count = data.get("viewer_count", "Unknown")
        return jsonify({"stream_id": stream_id, "viewer_count": viewer_count})
    else:
        return jsonify({"error": "Failed to fetch viewer count"}), response.status_code

if __name__ == '__main__':
    app.run(debug=True)
