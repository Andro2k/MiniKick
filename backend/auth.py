import os, json, requests, webbrowser, base64, hashlib
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer

TOKEN_FILE = "token.json"

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        if 'code' in query:
            self.server.auth_code = query['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open("success.html", "rb") as f: self.wfile.write(f.read())
    def log_message(self, *args): pass

class AuthManager:
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def get_tokens(self):
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, "r") as f: return json.load(f)
        return self.new_login()

    def new_login(self):
        verifier = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8').rstrip('=')
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode('utf-8').rstrip('=')
        
        url = (f"https://id.kick.com/oauth/authorize?response_type=code&client_id={self.client_id}"
               f"&redirect_uri={self.redirect_uri}&scope=user:read&code_challenge={challenge}"
               f"&code_challenge_method=S256&state=random")

        port = int(urlparse(self.redirect_uri).port or 8080)
        httpd = HTTPServer(('', port), OAuthCallbackHandler)
        httpd.auth_code = None
        webbrowser.open(url)
        while httpd.auth_code is None: httpd.handle_request()
        httpd.server_close()

        data = {"grant_type": "authorization_code", "client_id": self.client_id, 
                "client_secret": self.client_secret, "code": httpd.auth_code, 
                "code_verifier": verifier, "redirect_uri": self.redirect_uri}
        
        resp = requests.post("https://id.kick.com/oauth/token", data=data).json()
        with open(TOKEN_FILE, "w") as f: json.dump(resp, f)
        return resp