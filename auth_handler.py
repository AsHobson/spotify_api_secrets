import os
import json
import time
import requests
from dotenv import load_dotenv
import base64
import webbrowser
import secrets
from urllib.parse import urlencode, urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler

load_dotenv()

# This class handles the incoming "redirect" from Spotify
class SpotifyCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. Parse the URL to get the 'code'
        query_components = parse_qs(urlparse(self.path).query)
        if "state" in query_components:
            self.server.return_state = query_components["state"][0]
        if "code" in query_components:
            # Store the code in the server object so we can grab it later
            self.server.auth_code = query_components["code"][0]
            
            # 2. Send a friendly response to your browser
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Success!</h1><p>You can close this window now.</p>")
        else:
            self.send_response(400)
            self.end_headers()

class SpotifyUserAuth:
    def __init__(self):
        self.client_id = os.getenv("CLIENT_KEY")
        self.client_secret = os.getenv("CLIENT_SECRET")
        self.redirect_uri = "http://127.0.0.1:8888"
        self.scope = "user-read-recently-played"
        self.auth_url = "https://accounts.spotify.com/authorize"
        self.token_url = "https://accounts.spotify.com/api/token"
        self.state = secrets.token_urlsafe(32)

    def get_auth_token(self, token_data):
        if token_data is not None:

            if time.time() < token_data['expires_at']:
                print('returning cached token')
                return token_data['access_token'], token_data
            else:
                print('need to refresh')
                return self._refresh_access_token(token_data['refresh_token'])
        
        print('No Token Found')
        return self._do_full_login()

    def _do_full_login(self):
        """Starts a local server and opens the browser to login."""
        # 1. Setup the temporary local server
        server_address = ('', 8888)
        httpd = HTTPServer(server_address, SpotifyCallbackHandler)
        httpd.auth_code = None  # Placeholder for the code we're about to get
        httpd.return_state = None # Placeholder for returned state string we're about to get

        # 2. Build the Spotify URL
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": self.scope,
            "state": self.state,
            "show_dialog": True 
        }
        url = f"{self.auth_url}?{urlencode(params)}"
        
        print(f"Opening browser for Spotify login...")
        webbrowser.open(url)

        # 3. Wait for exactly one request (the callback)
        print("Waiting for authorization...")
        httpd.handle_request() # This blocks the script until Spotify hits the URL

        if httpd.return_state != self.state:
            raise Exception("State Mismatch.")

        if httpd.auth_code:
            print("Authorization code received!")
            return self._exchange_code_for_token(httpd.auth_code)
        else:
            raise Exception("Failed to get authorization code.")

    def _exchange_code_for_token(self, code):
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_header = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri
        }

        response = requests.post(self.token_url, data=payload, headers=headers)
        return self._handle_token_response(response.json())

    def _refresh_access_token(self, refresh_token):
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_header = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }

        response = requests.post(self.token_url, data=payload, headers=headers)
        return self._handle_token_response(response.json(), existing_refresh_token=refresh_token)

    def _handle_token_response(self, data, existing_refresh_token=None):
        refresh_token = data.get('refresh_token', existing_refresh_token)
        
        token_info = {
            "access_token": data['access_token'],
            "refresh_token": refresh_token,
            "expires_at": data['expires_in'] - 60
        }
            
        return token_info['access_token'], token_info