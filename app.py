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
