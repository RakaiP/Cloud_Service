"""
Authentication module for the Cloud File Service SDK.
"""
import os
import json
import webbrowser
import time
import http.server
import socketserver
import threading
from urllib.parse import urlparse, parse_qs
import requests
import logging

logger = logging.getLogger(__name__)

# Default token file location
TOKEN_FILE = os.path.expanduser("~/.cloudservice/token.json")

class CallbackHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler for Auth0 callback"""
    code = None
    
    def do_GET(self):
        """Handle GET request with the authorization code"""
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        
        query = urlparse(self.path).query
        params = parse_qs(query)
        
        if "code" in params:
            self.__class__.code = params["code"][0]
            self.wfile.write(b"""
            <html>
            <head><title>Login Successful</title></head>
            <body>
                <h1>Login Successful!</h1>
                <p>You can now close this window and return to the application.</p>
                <script>window.close();</script>
            </body>
            </html>
            """)
        else:
            self.wfile.write(b"""
            <html>
            <head><title>Login Failed</title></head>
            <body>
                <h1>Login Failed</h1>
                <p>Authentication was not successful. Please try again.</p>
            </body>
            </html>
            """)
    
    def log_message(self, format, *args):
        """Suppress server logs"""
        return


class Auth0Client:
    """Client for Auth0 authentication"""
    
    def __init__(self, domain, client_id, audience, redirect_uri="http://localhost:3000/callback"):
        """
        Initialize Auth0 client
        
        Args:
            domain: Auth0 domain (e.g., 'your-tenant.auth0.com')
            client_id: Auth0 client ID
            audience: API audience
            redirect_uri: Callback URI for Auth0
        """
        self.domain = domain
        self.client_id = client_id
        self.audience = audience
        self.redirect_uri = redirect_uri
        self.token = None
        
        # Create directory for token file if it doesn't exist
        os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
    
    def get_login_url(self):
        """
        Get the Auth0 login URL
        
        Returns:
            str: URL to open in browser for authentication
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "openid profile email",
            "audience": self.audience,
            "response_type": "code"
        }
        
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"https://{self.domain}/authorize?{query_string}"
    
    def exchange_code_for_token(self, code):
        """
        Exchange authorization code for an access token
        
        Args:
            code: Authorization code from Auth0
            
        Returns:
            dict: Token response
        """
        payload = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "code": code,
            "redirect_uri": self.redirect_uri
        }
        
        response = requests.post(
            f"https://{self.domain}/oauth/token",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        response.raise_for_status()
        return response.json()
    
    def save_token(self, token_data):
        """
        Save token to file
        
        Args:
            token_data: Token data from Auth0
        """
        with open(TOKEN_FILE, "w") as f:
            json.dump(token_data, f)
        
        self.token = token_data
    
    def load_token(self):
        """
        Load token from file
        
        Returns:
            bool: True if token was loaded successfully, False otherwise
        """
        try:
            if os.path.exists(TOKEN_FILE):
                with open(TOKEN_FILE, "r") as f:
                    self.token = json.load(f)
                return self.is_token_valid()
            return False
        except Exception as e:
            logger.error(f"Error loading token: {e}")
            return False
    
    def is_token_valid(self):
        """
        Check if token is valid
        
        Returns:
            bool: True if token is valid, False otherwise
        """
        if not self.token:
            return False
        
        # Check if token has expired
        expires_at = self.token.get("expires_at")
        if not expires_at:
            # If no expires_at, calculate it from expires_in
            if "expires_in" in self.token:
                # If we don't have an expires_at field but do have expires_in,
                # this might be a fresh token that hasn't been saved yet
                return True
            return False
        
        return time.time() < expires_at
    
    def login(self):
        """
        Perform Auth0 login flow
        
        Returns:
            bool: True if login was successful, False otherwise
        """
        # First try loading existing token
        if self.load_token():
            logger.info("Using existing token")
            return True
        
        # Start local server to handle callback
        server = socketserver.TCPServer(("localhost", 3000), CallbackHandler)
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        try:
            # Open browser for login
            login_url = self.get_login_url()
            webbrowser.open(login_url)
            
            logger.info("Browser opened for authentication. Waiting for callback...")
            
            # Wait for callback to receive code
            timeout = 120  # 2 minutes
            start_time = time.time()
            
            while not CallbackHandler.code and time.time() - start_time < timeout:
                time.sleep(0.5)
            
            if not CallbackHandler.code:
                logger.error("Authentication timed out")
                return False
            
            # Exchange code for token
            token_data = self.exchange_code_for_token(CallbackHandler.code)
            
            # Add expiration time for later validation
            token_data["expires_at"] = time.time() + token_data.get("expires_in", 86400)
            
            # Save token
            self.save_token(token_data)
            
            logger.info("Authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
        finally:
            # Shutdown server
            server.shutdown()
            server.server_close()
    
    def logout(self):
        """
        Log out by removing saved token
        """
        self.token = None
        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)
        logger.info("Logged out")
    
    def get_access_token(self):
        """
        Get access token
        
        Returns:
            str: Access token or None if not authenticated
        """
        if not self.token and not self.load_token():
            if not self.login():
                return None
        
        return self.token.get("access_token")
