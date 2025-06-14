import os
from jose import jwt
import requests
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
API_AUDIENCE = os.getenv("API_AUDIENCE")
ALGORITHMS = os.getenv("ALGORITHMS", "RS256").split(",")

token_auth_scheme = HTTPBearer()

def get_jwks():
    """Fetch the JWKS (JSON Web Key Set) from Auth0"""
    url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
    return requests.get(url).json()

def verify_jwt(token: str):
    """Verify the JWT token against Auth0"""
    try:
        jwks = get_jwks()
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}
        
        # Find the matching key in the JWKS
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }

        if rsa_key:
            try:
                # Decode and verify the token
                payload = jwt.decode(
                    token,
                    rsa_key,
                    algorithms=ALGORITHMS,
                    audience=API_AUDIENCE,
                    issuer=f"https://{AUTH0_DOMAIN}/"
                )
                return payload
            except jwt.ExpiredSignatureError:
                raise HTTPException(status_code=401, detail="Token has expired")
            except jwt.JWTClaimsError:
                raise HTTPException(status_code=401, detail="Invalid claims (audience or issuer)")
            except Exception as e:
                raise HTTPException(status_code=401, detail=f"Token invalid: {str(e)}")
        
        raise HTTPException(status_code=401, detail="Unable to find appropriate key")
    except Exception as e:
        logger.error(f"Error verifying token: {str(e)}")
        raise HTTPException(status_code=401, detail="Authentication error")

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(token_auth_scheme)):
    """FastAPI dependency that extracts and validates the JWT token"""
    return verify_jwt(credentials.credentials)
