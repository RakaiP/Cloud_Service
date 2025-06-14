# Authentication in Cloud File Service

This document explains how authentication works in our cloud file service architecture.

## Authentication Architecture

We use Auth0 for authentication with a zero-trust model where:

1. **Client SDK** handles the login flow and obtains the JWT token
2. **Each microservice** independently verifies the token

This approach provides several benefits:
- No single point of failure for authentication
- Reduced network overhead (no internal auth service calls)
- Simplified deployment (no extra auth service to maintain)
- Better security (zero-trust model)

## How It Works

### Client Side (SDK)

1. User initiates login through the SDK
2. SDK opens a browser for Auth0 login
3. Auth0 redirects back with a token
4. SDK stores the token locally
5. SDK attaches the token to all API requests

### Server Side (Microservices)

1. Each endpoint protected with `dependencies=[Depends(get_current_user)]`
2. When a request arrives, the token is extracted from the Authorization header
3. Token is verified against Auth0's JWKS endpoint
4. If valid, the request proceeds; if invalid, a 401 error is returned

## Setting Up Auth0

1. Sign up for an Auth0 account
2. Create a new API in the Auth0 dashboard:
   - Name: Cloud File Service API
   - Identifier: https://cloud-api.rakai/ (this is your API_AUDIENCE)
   - Signing Algorithm: RS256

3. Create a new Application in Auth0:
   - Name: Cloud File Service Client
   - Application Type: Regular Web Application
   - Allowed Callback URLs: http://localhost:3000/callback (adjust as needed)

4. Update your `.env` files with your Auth0 configuration:
   ```
   AUTH0_DOMAIN=your-tenant.auth0.com
   API_AUDIENCE=https://cloud-api.rakai/
   ALGORITHMS=RS256
   ```

## Testing Authentication

### Using Swagger UI

1. Navigate to `/docs` on any service
2. Click the "Authorize" button
3. Enter your token in the format: `Bearer YOUR_TOKEN_HERE`
4. Try accessing protected endpoints

### Using cURL

```bash
curl -X GET "http://localhost:8000/files" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Getting a Test Token

To get a token for testing:

1. Use the Auth0 Dashboard > APIs > Your API > Test
2. Or use the Auth0 CLI to get a test token
3. Or implement a small utility that uses the Auth0 Machine-to-Machine flow

## Troubleshooting

If you're having issues with authentication:

1. Check that your AUTH0_DOMAIN and API_AUDIENCE values match what's in Auth0
2. Verify the token hasn't expired (JWTs have an expiration time)
3. Make sure the token is being sent with the correct format: `Bearer YOUR_TOKEN_HERE`
4. Check Auth0 logs for any authentication failures

## Security Considerations

- Never commit your Auth0 credentials to source control
- For production, use environment variables or a secure secrets manager
- Consider implementing additional authorization logic to restrict access to resources based on user claims
