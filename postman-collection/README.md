# Rithmo API Postman Collections

This directory contains comprehensive Postman collections for the Rithmo Period Tracker API.

## 📋 Available Collections

### 🎯 Master Collection
- **File**: `master_collection.json`
- **Description**: Complete API collection with all endpoints (72 endpoints)
- **Use Case**: Full API testing and development

### 🔐 Authentication Collection
- **File**: `auth_collection.json`
- **Description**: User management and JWT authentication (11 endpoints)
- **Includes**:
  - User registration with sex field
  - Account activation
  - JWT login/refresh/verify
  - Password management
  - User profile CRUD

### 👤 User Profile Collection
- **File**: `user_profile_collection.json`
- **Description**: User profile and partner management (8 endpoints)
- **Includes**:
  - Profile management
  - Partner invitation system
  - Partner linking/unlinking

### 🩸 Cycle Tracker Collection
- **File**: `cycle_tracker_collection.json`
- **Description**: Period tracking and cycle analysis (21 endpoints)
- **Includes**:
  - Period CRUD operations
  - Cycle analysis and insights
  - Ovulation predictions
  - Wellness logging
  - Partner cycle viewing

### 🔔 Notifications & Messaging Collection
- **File**: `notifications_collection.json`
- **Description**: Notifications and partner messaging (25 endpoints)
- **Includes**:
  - Notification management
  - Partner messaging system
  - Push notification tokens
  - Notification preferences

### 🤖 AI Suggestions Collection
- **File**: `ml_suggestions_collection.json`
- **Description**: AI-powered health suggestions (7 endpoints)
- **Includes**:
  - Personalized health suggestions
  - Feedback system
  - Suggestion history
  - Model status monitoring

## 🚀 Quick Start

### 1. Import Collections
1. Open Postman
2. Click **Import** button
3. Select desired JSON file(s)
4. Collections will be imported with proper folder structure

### 2. Set Up Environment
The collections include these variables:
- `base_url`: https://api.rithmo.ir
- `access_token`: (auto-populated after login)
- `refresh_token`: (auto-populated after login)
- `user_id`: (set manually if needed)
- `partner_id`: (set manually for partner operations)

### 3. Authentication Flow
1. **Login**: Use "Login (Get JWT Token)" with existing credentials - tokens auto-saved
2. **Test**: Use "Test Authentication" to verify login worked
3. **Use APIs**: All other endpoints will automatically use the saved token
4. **Refresh**: Use "Refresh JWT Token" when access token expires

**Test Credentials** (if needed):
- Username: `Zara`
- Password: `Aa12345678@`

## 📊 API Overview

### Base URL
```
https://api.rithmo.ir
```

**Important**: The base URL is `https://api.rithmo.ir` (without `/api/` suffix) because the Django URLs already include the `/api/` prefix.

### Authentication
- **Type**: JWT Bearer Token
- **Header**: `Authorization: Bearer {access_token}`
- **Token Lifetime**: Access tokens expire, use refresh token

### Key Features

#### 🔐 Authentication & User Management
- Djoser-based user management
- JWT authentication
- Email activation
- Password reset functionality

#### 👥 Partner System
- Invitation code system
- Secure partner linking
- Partner data sharing
- Partner removal with confirmation

#### 🩸 Period Tracking
- Comprehensive period logging
- Cycle regularity analysis
- Ovulation predictions
- Symptom and medication tracking

#### 💪 Wellness Tracking
- Daily wellness logs
- Mood, energy, stress tracking
- Exercise and nutrition logging
- Cycle-wellness correlation analysis

#### 🤖 AI Health Suggestions
- Personalized recommendations
- Machine learning-based insights
- Feedback system for model improvement
- Rule-based fallbacks

#### 🔔 Smart Notifications
- Cycle-based notifications
- Partner messaging
- Push notification support
- Customizable preferences

## 📱 Mobile App Integration

### Push Notifications
Support for multiple platforms:
- **iOS**: Native iOS push tokens
- **Android**: Firebase/Expo push tokens
- **Web**: Web push notifications

### Partner Features
- Real-time messaging
- Cycle sharing (limited data for privacy)
- Support tips based on partner's cycle phase

## 🔧 Development Notes

### Error Handling
All endpoints return consistent error responses:
```json
{
  "error": "Error message",
  "details": "Additional details if available"
}
```

### Data Validation
- Cycle length: 21-45 days
- Period duration: 2-10 days
- Wellness metrics: Specific ranges per field

### Privacy & Security
- Partner data sharing is limited
- JWT tokens for secure authentication
- User data isolation

## 📈 Testing Scenarios

### Basic Flow
1. Register → Login → Update Profile → Add Period → Get Suggestions

### Partner Flow
1. User A generates invitation code
2. User B accepts invitation code
3. Both users can view limited partner data
4. Partner messaging functionality

### Wellness Tracking
1. Daily wellness logging
2. Correlation analysis with cycle phases
3. AI suggestions based on wellness data

## 🐛 Debugging

### Common Issues
1. **401 Unauthorized**: Token expired, use refresh endpoint
2. **400 Bad Request**: Check request body format
3. **404 Not Found**: Verify endpoint URL and user data

### Debug Endpoints
- `GET /api/ai/debug-suggestions/`: Check user's AI suggestions
- `GET /api/ai/model-status/`: Check AI model status

## 📝 Notes

- All timestamps are in ISO format
- Dates are in YYYY-MM-DD format
- Collections include example data for testing
- Auto-generated on: 2025-01-17
- Total endpoints covered: 72

## 🔄 Updates

To regenerate collections:
```bash
python3 generate_postman_collection.py
```

This will update all collections with the latest API structure.