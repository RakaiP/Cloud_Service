// Auth0 Configuration
window.AUTH0_CONFIG = {
    domain: 'dev-mc721bw3z72t3xex.us.auth0.com',
    clientId: 'LbzsusVrT7HqFFWf3hkmrRMKKdRqEojc', // ✅ Your actual Client ID
    audience: 'https://cloud-api.rakai/',
    redirectUri: window.location.origin,
    scope: 'openid profile email'
};

// Auth0 Application Configuration Guide:
// 1. Go to https://manage.auth0.com/
// 2. Navigate to Applications > Single Page Applications
// 3. Select your application (Client ID: LbzsusVrT7HqFFWf3hkmrRMKKdRqEojc)
// 4. In Settings, configure:
//    - Application Type: Single Page Application
//    - Allowed Callback URLs: http://localhost, http://localhost:80
//    - Allowed Logout URLs: http://localhost, http://localhost:80
//    - Allowed Web Origins: http://localhost, http://localhost:80
//    - Allowed Origins (CORS): http://localhost, http://localhost:80
// 5. In Advanced Settings > Grant Types, enable:
//    - Authorization Code
//    - Refresh Token
//    - Implicit (optional)

console.log('Auth0 config loaded with Client ID:', window.AUTH0_CONFIG.clientId);
