import requests
import json
from auth_handler import SpotifyUserAuth

# Get Access Token from Spotify
auth = SpotifyUserAuth()

token = auth.get_auth_token()

print(f"Ready to work with token: {token[:3]}...{token[-3:]}")

# Get Last 50 Played Tracks
api_url = "https://api.spotify.com/v1/me/player/recently-played"
api_headers = {
    "Authorization": f"Bearer {token}"
}
api_response = requests.get(
    api_url,
    headers=api_headers
)

if api_response.status_code != 200:
            raise Exception(f"Authentication failed: {api_response.json()}")
#api_response.raise_for_status()

data = api_response.json()

spotify_ids = []

for track in data["items"]:
    i = track["track"]["id"]
    if i not in spotify_ids:
        spotify_ids.append(i)


# Get Track Audio Features
features_api_url = "https://api.spotify.com/v1/audio-features?ids="
features_api_headers = {
    "Authorization": f"Bearer {token}"
}
features_api_response = requests.get(
    features_api_url,
    headers = features_api_headers,
    params = {"ids": ",".join(spotify_ids)}
)

if features_api_response.status_code != 200:
            raise Exception(f"Authentication failed: {features_api_response.json()}")
#api_response.raise_for_status()

features_data = features_api_response.json()

with open('features.json', "w") as f:
            json.dump(features_data, f)