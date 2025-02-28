from flask import Flask, request, render_template_string, jsonify, redirect
import requests
import os

app = Flask(__name__)

# Replace with your public API key or OAuth token if needed
ACCESS_TOKEN = os.getenv('KICK_ACCESS_TOKEN', 'your_oauth_token_here')

# Step 1: Get Stream ID from user
@app.route('/enter-stream-id', methods=['GET', 'POST'])
def enter_stream_id():
    if request.method == 'POST':
        # Get the stream_id from the form
        stream_id = request.form['stream_id']
        return redirect(f'/viewer-count/{stream_id}')
    
    return render_template_string("""
        <form method="POST">
            <label for="stream_id">Enter Stream ID:</label>
            <input type="text" id="stream_id" name="stream_id" required>
            <button type="submit">Submit</button>
        </form>
    """)

# Step 2: Fetch viewer count for a specific stream (No login required)
@app.route('/viewer-count/<stream_id>')
def viewer_count(stream_id):
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}'
    }

    # Assuming Kick API has a public endpoint to get stream info
    url = f'https://api.kick.com/streams/{stream_id}'  # Example endpoint (adjust accordingly)
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return "Error fetching viewer count", 400

    data = response.json()
    print(f"API Response: {data}")  # Debugging print
    viewer_count = data.get('viewer_count', 'No viewer data')  # Modify based on actual API response structure

    return jsonify({
        'stream_id': stream_id,
        'viewer_count': viewer_count
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)
