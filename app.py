from flask import Flask, request, redirect, jsonify, render_template_string, session
import requests
import os

app = Flask(app)

# Set your Kick API credentials
KICK_CLIENT_ID = os.getenv('KICK_CLIENT_ID')
KICK_CLIENT_SECRET = os.getenv('KICK_CLIENT_SECRET')
KICK_REDIRECT_URI = os.getenv('KICK_REDIRECT_URI')

# Flask session secret key
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your_secret_key')

# Step 1: Start OAuth flow
@app.route('/')
def home():
    return f'<a href="https://kick.com/oauth/authorize?response_type=code&client_id={KICK_CLIENT_ID}&redirect_uri={KICK_REDIRECT_URI}">Login with Kick</a>'

    # Step 2: OAuth callback
    @app.route('/callback')
    def callback():
        code = request.args.get('code')
        if not code:
                    return "Authorization failed", 400

                        # Exchange authorization code for access token
                    token_url = 'https://kick.com/oauth/token'
                    data = {
                                        'grant_type': 'authorization_code',
                                                'client_id': KICK_CLIENT_ID,
                                                        'client_secret': KICK_CLIENT_SECRET,
                                                                'redirect_uri': KICK_REDIRECT_URI,
                                                                        'code': code
                                                                            }
                    response = requests.post(token_url, data=data)
                                                                                    
                    if response.status_code != 200:
                                                                                                return "Error getting access token", 400

                                                                                                    # Get the access token
                                                                                                token_data = response.json()
                                                                                                access_token = token_data['access_token']

                                                                                                                # Save the access token in session
                                                                                                session['access_token'] = access_token

                                                                                                return redirect('/enter-stream-id')

                                                                                                                        # Step 3: Get Stream ID from user
                                                                                                @app.route('/enter-stream-id', methods=['GET', 'POST'])
                                                                                                def enter_stream_id():
                                                                                                                            if request.method == 'POST':
                                                                                                                                    stream_id = request.form['stream_id']
                                                                                                                            return redirect(f'/viewer-count/{stream_id}')
                                                                                                                                                
                                                                                                                            return render_template_string("""
                                                                                                                                                            <form method="POST">
                                                                                                                                                                        <label for="stream_id">Enter Stream ID:</label>
                                                                                                                                                                                    <input type="text" id="stream_id" name="stream_id" required>
                                                                                                                                                                                                <button type="submit">Submit</button>
                                                                                                                                                                                                        </form>
                                                                                                                                                                                                            """)

                                                                                                                                                                                                            # Step 4: Fetch viewer count for a specific stream
                                                                                                                            @app.route('/viewer-count/<stream_id>')
                                                                                                                            def viewer_count(stream_id):
                                                                                                                                                                                                                access_token = session.get('access_token')
                                                                                                                                                                                                                if not access_token:
                                                                                                                                                                                                                            return redirect('/')  # If no token, redirect to login

                                                                                                                                                                                                                            headers = {
                                                                                                                                                                                                                                        'Authorization': f'Bearer {access_token}'
                                                                                                                                                                                                                                            }

                                                                                                                                                                                                                                                # Kick API endpoint for stream info
                                                                                                                                                                                                                            url = f'https://api.kick.com/streams/{stream_id}'  # Example endpoint
                                                                                                                                                                                                                            response = requests.get(url, headers=headers)

                                                                                                                                                                                                                            if response.status_code != 200:
                                                                                                                                                                                                                                                                    return "Error fetching viewer count", 400

                                                                                                                                                                                                                                                                    data = response.json()
                                                                                                                                                                                                                                                                    viewer_count = data['viewer_count']  # Modify based on actual API response structure
                                                                                                                                                                                                                                                                                
                                                                                                                                                                                                                                                                    return jsonify({
                                                                                                                                                                                                                                                                                            'stream_id': stream_id,
                                                                                                                                                                                                                                                                                                    'viewer_count': viewer_count
                                                                                                                                                                                                                                                                                                        })

                                                                                                                                                                                                                                                                    if __name__ == '__main__':
                                                                                                                                                                                                                                                                                                            app.run(debug=True, host='0.0.0.0', port=10000)
