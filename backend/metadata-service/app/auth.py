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
    """Verify the JWT token against Auth0 with enhanced user info extraction"""
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
                
                # ✅ ENHANCED: Extract user info with fallbacks
                user_id = payload.get('sub')
                
                # Try multiple fields for email
                email = (
                    payload.get('email') or 
                    payload.get('https://cloud-api.rakai/email') or  # Custom claim
                    payload.get('email_verified') and payload.get('email') or
                    None
                )
                
                # Try multiple fields for name
                name = (
                    payload.get('name') or 
                    payload.get('https://cloud-api.rakai/name') or  # Custom claim
                    payload.get('nickname') or
                    payload.get('given_name') or
                    None
                )
                
                # ✅ ENHANCED: If no email in token, try to get from Auth0 userinfo
                if not email and user_id:
                    try:
                        logger.info(f"🔍 No email in token, fetching from Auth0 for user: {user_id}")
                        userinfo_response = requests.get(
                            f"https://{AUTH0_DOMAIN}/userinfo",
                            headers={"Authorization": f"Bearer {token}"},
                            timeout=5.0
                        )
                        if userinfo_response.status_code == 200:
                            userinfo = userinfo_response.json()
                            email = userinfo.get('email')
                            if not name:
                                name = userinfo.get('name') or userinfo.get('nickname')
                            logger.info(f"✅ Got user info from Auth0: email={email}, name={name}")
                        else:
                            logger.warning(f"⚠️ Failed to get userinfo: {userinfo_response.status_code}")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to fetch userinfo from Auth0: {e}")
                
                # ✅ ENHANCED: Add extra user info to payload
                enhanced_payload = {
                    **payload,
                    'email': email,
                    'name': name,
                    'nickname': payload.get('nickname'),
                    'picture': payload.get('picture'),
                    'email_verified': payload.get('email_verified', False)
                }
                
                logger.info(f"🔐 Token verified for user: {user_id} (email: {email}, name: {name})")
                return enhanced_payload
                
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
