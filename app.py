import requests

response = requests.post(
    "https://api.kick.com/public/v1/chat",
    headers={"Authorization":"text","Content-Type":"application/json"},
    data=json.dumps({
      "broadcaster_user_id": 1,
      "content": "text",
      "reply_to_message_id": "text",
      "type": "user"
    })
)

data = response.json()
