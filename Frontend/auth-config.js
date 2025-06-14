// Auth0 Configuration
window.AUTH0_CONFIG = {
    domain: 'dev-mc721bw3z72t3xex.us.auth0.com',
    clientId: 'LbzsusVrT7HqFFWf3hkmrRMKKdRqEojc', // Replace with your actual Auth0 client ID
    audience: 'https://cloud-api.rakai/',
    redirectUri: window.location.origin,
    scope: 'openid profile email'
};

// Note: To get your Auth0 Client ID:
// 1. Go to https://manage.auth0.com/
// 2. Navigate to Applications > Single Page Applications
// 3. Create a new SPA application or use existing one
// 4. Copy the Client ID and replace 'YOUR_CLIENT_ID_HERE' above
// 5. Add your domain (http://localhost:80) to Allowed Callback URLs, Allowed Web Origins, and Allowed Logout URLs
console.log('Auth0 config loaded:', window.AUTH0_CONFIG);
