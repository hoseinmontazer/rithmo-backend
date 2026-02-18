# Production Environment Setup for Rithmo API

## 🚀 Quick Setup

### 1. Import Environment
1. Open Postman
2. Click **Environments** (left sidebar)
3. Click **Import**
4. Select `production_environment.json`
5. Select the **Rithmo Production** environment

### 2. Import Collection
1. Click **Import** (top left)
2. Select `master_collection.json` (or any specific collection)
3. Collection will be imported with all endpoints

### 3. Login and Test
1. Select **Rithmo Production** environment (top right dropdown)
2. Go to **Authentication** folder
3. Run **Login (Get JWT Token)**
4. Tokens are automatically saved to environment variables
5. Test any protected endpoint

## 🔧 Environment Variables

The production environment includes these variables:

| Variable | Description | Auto-Updated |
|----------|-------------|--------------|
| `base_url` | API base URL | No |
| `access_token` | JWT access token | Yes (after login) |
| `refresh_token` | JWT refresh token | Yes (after login) |
| `user_id` | Current user ID | Manual |
| `partner_id` | Partner user ID | Manual |

## 📝 Updated Login Script

The login script now saves tokens to **both** collection and environment variables:

```javascript
if (pm.response.code === 200) {
    var jsonData = pm.response.json();
    
    // Save to both collection and environment variables
    pm.collectionVariables.set('access_token', jsonData.access);
    pm.collectionVariables.set('refresh_token', jsonData.refresh);
    
    // Also save to environment variables (for production)
    pm.environment.set('access_token', jsonData.access);
    pm.environment.set('refresh_token', jsonData.refresh);
    
    console.log('✅ Tokens saved to both collection and environment variables');
    console.log('🔑 Access Token:', jsonData.access.substring(0, 30) + '...');
    console.log('📍 Environment:', pm.environment.name || 'No environment selected');
} else {
    console.log('❌ Login failed with status:', pm.response.code);
    console.log('📝 Response:', pm.response.text());
    
    // Clear tokens on failed login
    pm.collectionVariables.unset('access_token');
    pm.environment.unset('access_token');
}
```

## 🔄 Token Refresh Script

The refresh script also updates both variable types:

```javascript
if (pm.response.code === 200) {
    var jsonData = pm.response.json();
    
    // Update access token in both collection and environment
    pm.collectionVariables.set('access_token', jsonData.access);
    pm.environment.set('access_token', jsonData.access);
    
    console.log('✅ Access token refreshed successfully');
    console.log('📍 Environment:', pm.environment.name || 'No environment selected');
} else {
    console.log('❌ Token refresh failed');
    // Clear invalid tokens
    pm.collectionVariables.unset('access_token');
    pm.environment.unset('access_token');
}
```

## 🌍 Multiple Environments

You can set up multiple environments for different stages:

### Production Environment
- **Name**: Rithmo Production
- **base_url**: `https://api.rithmo.ir`
- **Use for**: Live production API

### Development Environment  
- **Name**: Rithmo Development
- **base_url**: `http://localhost:8000`
- **Use for**: Local development

### Staging Environment (if needed)
- **Name**: Rithmo Staging
- **base_url**: `https://staging-api.rithmo.ir`
- **Use for**: Testing before production

## 🔐 Security Best Practices

### Token Management
1. **Never commit tokens** to version control
2. **Use environment variables** for production
3. **Rotate tokens regularly**
4. **Clear tokens** when switching environments

### Environment Isolation
1. **Separate environments** for dev/staging/prod
2. **Different credentials** for each environment
3. **Test in staging** before production deployment

## 🧪 Testing Workflow

### 1. Development Testing
```bash
# Switch to Development environment
# Run tests against localhost:8000
```

### 2. Staging Testing
```bash
# Switch to Staging environment  
# Run full test suite
# Validate all endpoints
```

### 3. Production Testing
```bash
# Switch to Production environment
# Run smoke tests only
# Monitor for issues
```

## 📊 Variable Priority

Postman resolves variables in this order:
1. **Environment variables** (highest priority)
2. **Collection variables**
3. **Global variables** (lowest priority)

Since we save to both environment and collection variables, environment variables will take precedence when an environment is selected.

## 🔧 Troubleshooting

### Tokens Not Saving
1. **Check environment selection** (top right dropdown)
2. **Verify login response** (should be 200 status)
3. **Check console output** for error messages

### Wrong Environment
1. **Select correct environment** from dropdown
2. **Verify base_url** matches expected server
3. **Clear old tokens** if switching environments

### Authentication Errors
1. **Check token expiration** (use refresh endpoint)
2. **Verify environment variables** are set
3. **Re-login** if refresh fails

## 📋 Environment Setup Checklist

- [ ] Import production environment JSON
- [ ] Import collection JSON  
- [ ] Select production environment
- [ ] Run login request
- [ ] Verify tokens are saved
- [ ] Test protected endpoint
- [ ] Bookmark frequently used requests

## 🎯 Quick Commands

### Switch Environment
```
Top right dropdown → Select "Rithmo Production"
```

### Check Variables
```
Environment tab → View current values
```

### Clear Tokens
```javascript
// Run in Postman console
pm.environment.unset('access_token');
pm.environment.unset('refresh_token');
```

### Test Authentication
```
Run: Authentication → Test Authentication
Should return current user info
```

## 📞 Support

If you encounter issues:
1. Check console output for error messages
2. Verify environment selection
3. Test login endpoint manually
4. Check API server status

The updated collections now provide better logging and error handling for production use! 🚀