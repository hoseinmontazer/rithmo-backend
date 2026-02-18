#!/usr/bin/env python3
"""
Dynamic Postman Collection Generator for Period Tracker API
Analyzes Django project structure and generates comprehensive Postman collections

Run: python3 generate_postman_collection.py
Output: 
- postman-collection/master_collection.json (Complete API)
- postman-collection/auth_collection.json (Authentication only)
- postman-collection/cycle_tracker_collection.json (Period tracking)
- postman-collection/notifications_collection.json (Notifications & messaging)
- postman-collection/ml_suggestions_collection.json (AI suggestions)
- postman-collection/user_profile_collection.json (User management)
"""

import json
import os
from datetime import datetime

# Configuration
BASE_URL = "https://api.rithmo.ir"
OUTPUT_DIR = "postman-collection"

class PostmanCollectionGenerator:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.collections = {}
        
    def create_base_collection(self, name, description):
        """Create a base collection structure"""
        return {
            "info": {
                "name": name,
                "description": description,
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
                "_postman_id": f"generated-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                "version": "1.0.0"
            },
            "auth": {
                "type": "bearer",
                "bearer": [
                    {
                        "key": "token",
                        "value": "{{access_token}}",
                        "type": "string"
                    }
                ]
            },
            "variable": [
                {
                    "key": "base_url",
                    "value": self.base_url,
                    "type": "string",
                    "description": "Base URL for the API"
                },
                {
                    "key": "access_token",
                    "value": "",
                    "type": "string",
                    "description": "JWT access token (auto-populated after login)"
                },
                {
                    "key": "refresh_token",
                    "value": "",
                    "type": "string",
                    "description": "JWT refresh token (auto-populated after login)"
                },
                {
                    "key": "user_id",
                    "value": "",
                    "type": "string",
                    "description": "Current user ID (set manually if needed)"
                },
                {
                    "key": "partner_id",
                    "value": "",
                    "type": "string",
                    "description": "Partner user ID (set manually for partner operations)"
                }
            ],
            "item": []
        }
    
    def create_request(self, name, method, path, body=None, query_params=None, description="", headers=None, auth_required=True):
        """Create a Postman request object"""
        if headers is None:
            headers = []
        
        if method in ["POST", "PUT", "PATCH"] and body and "Content-Type" not in [h["key"] for h in headers]:
            headers.append({"key": "Content-Type", "value": "application/json"})
        
        # Parse path to create URL structure
        path_parts = [p for p in path.strip('/').split('/') if p]
        
        request = {
            "name": name,
            "request": {
                "method": method,
                "header": headers,
                "url": {
                    "raw": f"{{{{base_url}}}}/{'/'.join(path_parts)}/",
                    "host": ["{{base_url}}"],
                    "path": path_parts + [""]
                }
            }
        }
        
        # Add authentication for protected endpoints
        if auth_required:
            request["request"]["auth"] = {
                "type": "bearer",
                "bearer": [
                    {
                        "key": "token",
                        "value": "{{access_token}}",
                        "type": "string"
                    }
                ]
            }
        else:
            # Explicitly set no auth for public endpoints
            request["request"]["auth"] = {
                "type": "noauth"
            }
        
        if description:
            request["request"]["description"] = description
        
        if body:
            request["request"]["body"] = {
                "mode": "raw",
                "raw": json.dumps(body, indent=2)
            }
        
        if query_params:
            request["request"]["url"]["query"] = [
                {"key": k, "value": v} for k, v in query_params.items()
            ]
            query_string = "&".join([f"{k}={v}" for k, v in query_params.items()])
            request["request"]["url"]["raw"] += f"?{query_string}"
        
        return request

    def generate_auth_collection(self):
        """Generate authentication endpoints"""
        collection = self.create_base_collection(
            "Rithmo API - Authentication", 
            "Authentication endpoints for Rithmo Period Tracker API"
        )
        
        # Djoser endpoints
        djoser_folder = {
            "name": "User Management (Djoser)",
            "item": [
                self.create_request(
                    "Register User",
                    "POST",
                    "/api/auth/users/",
                    body={
                        "username": "testuser",
                        "email": "test@example.com",
                        "password": "SecurePass123!",
                        "re_password": "SecurePass123!",
                        "sex": "female"
                    },
                    description="Register a new user account with sex field",
                    auth_required=False
                ),
                self.create_request(
                    "Activate User",
                    "POST",
                    "/api/auth/users/activation/",
                    body={
                        "uid": "user_id_from_email",
                        "token": "activation_token_from_email"
                    },
                    description="Activate user account using email token",
                    auth_required=False
                ),
                self.create_request(
                    "Get Current User",
                    "GET",
                    "/api/auth/users/me/",
                    description="Get current authenticated user details"
                ),
                self.create_request(
                    "Update Current User",
                    "PUT",
                    "/api/auth/users/me/",
                    body={
                        "first_name": "John",
                        "last_name": "Doe",
                        "email": "newemail@example.com"
                    },
                    description="Update current user information"
                ),
                self.create_request(
                    "Change Password",
                    "POST",
                    "/api/auth/users/set_password/",
                    body={
                        "new_password": "NewSecurePass123!",
                        "re_new_password": "NewSecurePass123!",
                        "current_password": "SecurePass123!"
                    },
                    description="Change user password"
                ),
                self.create_request(
                    "Reset Password",
                    "POST",
                    "/api/auth/users/reset_password/",
                    body={
                        "email": "test@example.com"
                    },
                    description="Request password reset email",
                    auth_required=False
                ),
                self.create_request(
                    "Confirm Password Reset",
                    "POST",
                    "/api/auth/users/reset_password_confirm/",
                    body={
                        "uid": "user_id_from_email",
                        "token": "reset_token_from_email",
                        "new_password": "NewSecurePass123!",
                        "re_new_password": "NewSecurePass123!"
                    },
                    description="Confirm password reset with token",
                    auth_required=False
                ),
                self.create_request(
                    "Delete User Account",
                    "DELETE",
                    "/api/auth/users/me/",
                    body={
                        "current_password": "SecurePass123!"
                    },
                    description="Delete current user account"
                )
            ]
        }
        
        # JWT endpoints
        jwt_folder = {
            "name": "JWT Authentication",
            "item": [
                {
                    "name": "Login (Get JWT Token)",
                    "event": [
                        {
                            "listen": "test",
                            "script": {
                                "exec": [
                                    "if (pm.response.code === 200) {",
                                    "    var jsonData = pm.response.json();",
                                    "    ",
                                    "    // Save to both collection and environment variables",
                                    "    // This works for both development and production environments",
                                    "    pm.collectionVariables.set('access_token', jsonData.access);",
                                    "    pm.collectionVariables.set('refresh_token', jsonData.refresh);",
                                    "    ",
                                    "    // Also save to environment variables (for production)",
                                    "    pm.environment.set('access_token', jsonData.access);",
                                    "    pm.environment.set('refresh_token', jsonData.refresh);",
                                    "    ",
                                    "    // Save user info if available",
                                    "    if (jsonData.user_id) {",
                                    "        pm.collectionVariables.set('user_id', jsonData.user_id);",
                                    "        pm.environment.set('user_id', jsonData.user_id);",
                                    "    }",
                                    "    ",
                                    "    console.log('✅ Tokens saved successfully to both collection and environment variables');",
                                    "    console.log('🔑 Access Token:', jsonData.access.substring(0, 30) + '...');",
                                    "    console.log('🔄 Refresh Token:', jsonData.refresh.substring(0, 30) + '...');",
                                    "    console.log('📍 Environment:', pm.environment.name || 'No environment selected');",
                                    "} else {",
                                    "    console.log('❌ Login failed with status:', pm.response.code);",
                                    "    console.log('📝 Response:', pm.response.text());",
                                    "    ",
                                    "    // Clear tokens on failed login",
                                    "    pm.collectionVariables.unset('access_token');",
                                    "    pm.collectionVariables.unset('refresh_token');",
                                    "    pm.environment.unset('access_token');",
                                    "    pm.environment.unset('refresh_token');",
                                    "}"
                                ],
                                "type": "text/javascript"
                            }
                        }
                    ],
                    "request": {
                        "method": "POST",
                        "header": [{"key": "Content-Type", "value": "application/json"}],
                        "auth": {"type": "noauth"},
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({
                                "username": "Zara",
                                "password": "Aa12345678@"
                            }, indent=2)
                        },
                        "url": {
                            "raw": "{{base_url}}/api/auth/jwt/create/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "auth", "jwt", "create", ""]
                        },
                        "description": "Login with username and password to get JWT tokens. Tokens are automatically saved to collection variables."
                    }
                },
                {
                    "name": "Refresh JWT Token",
                    "event": [
                        {
                            "listen": "test",
                            "script": {
                                "exec": [
                                    "if (pm.response.code === 200) {",
                                    "    var jsonData = pm.response.json();",
                                    "    ",
                                    "    // Update access token in both collection and environment",
                                    "    pm.collectionVariables.set('access_token', jsonData.access);",
                                    "    pm.environment.set('access_token', jsonData.access);",
                                    "    ",
                                    "    console.log('✅ Access token refreshed successfully');",
                                    "    console.log('🔑 New Access Token:', jsonData.access.substring(0, 30) + '...');",
                                    "    console.log('📍 Environment:', pm.environment.name || 'No environment selected');",
                                    "} else {",
                                    "    console.log('❌ Token refresh failed with status:', pm.response.code);",
                                    "    console.log('📝 Response:', pm.response.text());",
                                    "    console.log('🔄 Please login again to get new tokens');",
                                    "    ",
                                    "    // Clear invalid tokens",
                                    "    pm.collectionVariables.unset('access_token');",
                                    "    pm.collectionVariables.unset('refresh_token');",
                                    "    pm.environment.unset('access_token');",
                                    "    pm.environment.unset('refresh_token');",
                                    "}"
                                ],
                                "type": "text/javascript"
                            }
                        }
                    ],
                    "request": {
                        "method": "POST",
                        "header": [{"key": "Content-Type", "value": "application/json"}],
                        "auth": {"type": "noauth"},
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({
                                "refresh": "{{refresh_token}}"
                            }, indent=2)
                        },
                        "url": {
                            "raw": "{{base_url}}/api/auth/jwt/refresh/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "auth", "jwt", "refresh", ""]
                        },
                        "description": "Refresh access token using refresh token. New access token is automatically saved."
                    }
                },
                self.create_request(
                    "Verify JWT Token",
                    "POST",
                    "/api/auth/jwt/verify/",
                    body={
                        "token": "{{access_token}}"
                    },
                    description="Verify if JWT token is valid",
                    auth_required=False
                ),
                self.create_request(
                    "Test Authentication",
                    "GET",
                    "/api/auth/users/me/",
                    description="Test if authentication is working by getting current user info"
                )
            ]
        }
        
        collection["item"] = [djoser_folder, jwt_folder]
        return collection

    def generate_user_profile_collection(self):
        """Generate user profile endpoints"""
        collection = self.create_base_collection(
            "Rithmo API - User Profile", 
            "User profile management endpoints"
        )
        
        profile_folder = {
            "name": "Profile Management",
            "item": [
                self.create_request(
                    "Get User Profile",
                    "GET",
                    "/api/user/profile/",
                    description="Get current user's profile information including partners"
                ),
                self.create_request(
                    "Update User Profile",
                    "PUT",
                    "/api/user/profile/",
                    body={
                        "first_name": "Jane",
                        "last_name": "Doe",
                        "sex": "female",
                        "cycle_length": 28,
                        "period_duration": 5
                    },
                    description="Update user profile information"
                ),
                self.create_request(
                    "Partial Update Profile",
                    "PATCH",
                    "/api/user/profile/",
                    body={
                        "cycle_length": 30
                    },
                    description="Partially update user profile"
                )
            ]
        }
        
        partner_folder = {
            "name": "Partner Management",
            "item": [
                self.create_request(
                    "Get Invitation Code",
                    "GET",
                    "/api/user/invitation/",
                    description="Get current active invitation code if exists"
                ),
                self.create_request(
                    "Generate Invitation Code",
                    "POST",
                    "/api/user/invitation/",
                    body={},
                    description="Generate new invitation code for partner linking"
                ),
                self.create_request(
                    "Accept Invitation Code",
                    "POST",
                    "/api/user/invitation/",
                    body={
                        "code_to_accept": "12345"
                    },
                    description="Accept partner's invitation code to link accounts"
                ),
                self.create_request(
                    "Generate Remove Code",
                    "POST",
                    "/api/user/partner/remove/",
                    body={},
                    description="Generate code to remove current partner"
                ),
                self.create_request(
                    "Remove Partner",
                    "POST",
                    "/api/user/partner/remove/",
                    body={
                        "remove_code": "54321"
                    },
                    description="Remove current partner using remove code"
                )
            ]
        }
        
        collection["item"] = [profile_folder, partner_folder]
        return collection

    def generate_cycle_tracker_collection(self):
        """Generate cycle tracking endpoints"""
        collection = self.create_base_collection(
            "Rithmo API - Cycle Tracker", 
            "Period and cycle tracking endpoints"
        )
        
        periods_folder = {


            "name": "Period Management",
            "item": [
                self.create_request(
                    "List All Periods",
                    "GET",
                    "/api/periods/",
                    description="Get all periods for authenticated user"
                ),
                self.create_request(
                    "List Partner's Periods",
                    "GET",
                    "/api/periods/",
                    query_params={"role": "partner"},
                    description="Get partner's periods (if linked)"
                ),
                self.create_request(
                    "Create New Period",
                    "POST",
                    "/api/periods/",
                    body={
                        "start_date": "2025-01-15",
                        "end_date": "2025-01-20",
                        "symptoms": "cramps,headache,fatigue",
                        "medication": "ibuprofen,heating pad",
                        "cycle_length": 28,
                        "period_duration": 5
                    },
                    description="Create a new period entry"
                ),
                self.create_request(
                    "Get Specific Period",
                    "GET",
                    "/api/periods/1/",
                    description="Get details of a specific period"
                ),
                self.create_request(
                    "Update Specific Period",
                    "PUT",
                    "/api/periods/1/",
                    body={
                        "start_date": "2025-01-15",
                        "end_date": "2025-01-21",
                        "symptoms": "cramps,headache,fatigue,bloating",
                        "medication": "ibuprofen"
                    },
                    description="Update a specific period completely"
                ),
                self.create_request(
                    "Partial Update Period",
                    "PATCH",
                    "/api/periods/1/",
                    body={
                        "end_date": "2025-01-21",
                        "symptoms": "cramps,headache,fatigue,bloating"
                    },
                    description="Partially update a specific period"
                ),
                self.create_request(
                    "Update Latest Period",
                    "PATCH",
                    "/api/periods/update/",
                    body={
                        "period_id": 1,
                        "end_date": "2025-01-21",
                        "symptoms": "cramps,headache,fatigue",
                        "medication": "ibuprofen"
                    },
                    description="Update the latest period using custom endpoint"
                ),
                self.create_request(
                    "Delete Period",
                    "DELETE",
                    "/api/periods/1/",
                    description="Delete a specific period"
                )
            ]
        }
        
        analysis_folder = {
            "name": "Cycle Analysis",
            "item": [
                self.create_request(
                    "Get Cycle Analysis",
                    "GET",
                    "/api/periods/cycle_analysis/",
                    description="Get comprehensive cycle analysis for user"
                ),
                self.create_request(
                    "Get Partner Cycle Analysis",
                    "GET",
                    "/api/periods/cycle_analysis/",
                    query_params={"role": "partner"},
                    description="Get partner's cycle analysis (limited data)"
                ),
                self.create_request(
                    "Get Cycle Insights",
                    "GET",
                    "/api/periods/cycle_insights/",
                    description="Get personalized cycle insights and predictions"
                ),
                self.create_request(
                    "Get Wellness Correlation",
                    "GET",
                    "/api/periods/wellness_correlation/",
                    description="Analyze correlation between wellness metrics and cycle phases"
                ),
                self.create_request(
                    "Get Symptom Patterns",
                    "GET",
                    "/api/periods/symptom_patterns/",
                    description="Analyze symptom patterns across cycles"
                )
            ]
        }
        
        ovulation_folder = {
            "name": "Ovulation Tracking",
            "item": [
                self.create_request(
                    "Get Latest Ovulation Prediction",
                    "GET",
                    "/api/ovulation/",
                    description="Get ovulation prediction for latest period"
                ),
                self.create_request(
                    "Get Ovulation for Specific Period",
                    "GET",
                    "/api/ovulation/1/",
                    description="Get ovulation prediction for specific period ID"
                )
            ]
        }
        
        wellness_folder = {
            "name": "Wellness Logs",
            "item": [
                self.create_request(
                    "List Wellness Logs",
                    "GET",
                    "/api/wellness/",
                    description="Get all wellness logs for user"
                ),
                self.create_request(
                    "Create/Update Daily Wellness Log",
                    "POST",
                    "/api/wellness/",
                    body={
                        "stress_level": 3,
                        "sleep_hours": 7.5,
                        "mood_level": 1,
                        "energy_level": 6,
                        "pain_level": 2,
                        "exercise_minutes": 30,
                        "nutrition_quality": 4,
                        "caffeine_intake": 2,
                        "alcohol_intake": 0,
                        "smoking": 0,
                        "anxiety_level": 2,
                        "focus_level": 7,
                        "notes": "Feeling good today, had a productive workout"
                    },
                    description="Create or update wellness log for today (auto-creates/updates based on date)"
                ),
                self.create_request(
                    "Get Specific Wellness Log",
                    "GET",
                    "/api/wellness/1/",
                    description="Get specific wellness log entry"
                ),
                self.create_request(
                    "Update Wellness Log",
                    "PUT",
                    "/api/wellness/1/",
                    body={
                        "stress_level": 2,
                        "sleep_hours": 8.0,
                        "mood_level": 2,
                        "energy_level": 8,
                        "notes": "Updated - feeling much better after good sleep"
                    },
                    description="Update specific wellness log"
                ),
                self.create_request(
                    "Delete Wellness Log",
                    "DELETE",
                    "/api/wellness/1/",
                    description="Delete specific wellness log"
                )
            ]
        }
        
        notifications_gen_folder = {
            "name": "Notification Generation",
            "item": [
                self.create_request(
                    "Generate Smart Notifications",
                    "POST",
                    "/api/generate-notifications/",
                    description="Generate smart notifications based on cycle data and preferences"
                )
            ]
        }
        
        collection["item"] = [periods_folder, analysis_folder, ovulation_folder, wellness_folder, notifications_gen_folder]
        return collection

    def generate_notifications_collection(self):
        """Generate notifications and messaging endpoints"""
        collection = self.create_base_collection(
            "Rithmo API - Notifications & Messaging", 
            "Notification management and partner messaging endpoints"
        )
        
        notifications_folder = {
            "name": "Notifications Management",
            "item": [
                self.create_request(
                    "List All Notifications",
                    "GET",
                    "/api/notifications/notifications/",
                    description="Get all notifications for user"
                ),
                self.create_request(
                    "Get Unread Notifications",
                    "GET",
                    "/api/notifications/notifications/unread/",
                    description="Get only unread notifications with count"
                ),
                self.create_request(
                    "Create Notification",
                    "POST",
                    "/api/notifications/notifications/",
                    body={
                        "notification_type": "system",
                        "title": "Test Notification",
                        "message": "This is a test notification"
                    },
                    description="Create a new notification"
                ),
                self.create_request(
                    "Get Specific Notification",
                    "GET",
                    "/api/notifications/notifications/1/",
                    description="Get details of specific notification"
                ),
                self.create_request(
                    "Mark Notification as Read",
                    "POST",
                    "/api/notifications/notifications/1/mark_read/",
                    description="Mark specific notification as read"
                ),
                self.create_request(
                    "Mark All Notifications as Read",
                    "POST",
                    "/api/notifications/notifications/mark_all_read/",
                    description="Mark all notifications as read"
                ),
                self.create_request(
                    "Update Notification",
                    "PUT",
                    "/api/notifications/notifications/1/",
                    body={
                        "title": "Updated Notification",
                        "message": "Updated message"
                    },
                    description="Update notification"
                ),
                self.create_request(
                    "Delete Notification",
                    "DELETE",
                    "/api/notifications/notifications/1/",
                    description="Delete notification"
                )
            ]
        }
        
        messages_folder = {
            "name": "Partner Messaging",
            "item": [
                self.create_request(
                    "List All Messages",
                    "GET",
                    "/api/notifications/messages/",
                    description="Get all partner messages"
                ),
                self.create_request(
                    "Send Message to Partner",
                    "POST",
                    "/api/notifications/messages/",
                    body={
                        "receiver": "{{partner_id}}",
                        "message": "How are you feeling today? 💕"
                    },
                    description="Send message to partner"
                ),
                self.create_request(
                    "Get Conversation with Partner",
                    "GET",
                    "/api/notifications/messages/conversation/",
                    query_params={"partner_id": "{{partner_id}}"},
                    description="Get conversation history with specific partner"
                ),
                self.create_request(
                    "Get Unread Messages",
                    "GET",
                    "/api/notifications/messages/unread/",
                    description="Get unread messages with count"
                ),
                self.create_request(
                    "Get Specific Message",
                    "GET",
                    "/api/notifications/messages/1/",
                    description="Get specific message details"
                ),
                self.create_request(
                    "Update Message",
                    "PUT",
                    "/api/notifications/messages/1/",
                    body={
                        "message": "Updated message content"
                    },
                    description="Update message content"
                ),
                self.create_request(
                    "Delete Message",
                    "DELETE",
                    "/api/notifications/messages/1/",
                    description="Delete message"
                )
            ]
        }
        
        preferences_folder = {
            "name": "Notification Preferences",
            "item": [
                self.create_request(
                    "Get Notification Preferences",
                    "GET",
                    "/api/notifications/preferences/",
                    description="Get user's notification preferences"
                ),
                self.create_request(
                    "Update Preferences (POST)",
                    "POST",
                    "/api/notifications/preferences/",
                    body={
                        "email_period_reminder": True,
                        "email_ovulation": True,
                        "email_partner_message": True,
                        "email_wellness_reminder": False,
                        "push_period_reminder": True,
                        "push_ovulation": True,
                        "push_partner_message": True,
                        "push_wellness_reminder": True,
                        "inapp_period_reminder": True,
                        "inapp_ovulation": True,
                        "inapp_partner_message": True,
                        "inapp_wellness_reminder": True,
                        "reminder_days_before": 2,
                        "reminder_time": "09:00:00"
                    },
                    description="Create or update notification preferences"
                ),
                self.create_request(
                    "Update Preferences (PUT)",
                    "PUT",
                    "/api/notifications/preferences/update_preferences/",
                    body={
                        "push_period_reminder": False,
                        "reminder_days_before": 3,
                        "reminder_time": "08:00:00"
                    },
                    description="Update notification preferences using PUT method"
                )
            ]
        }
        
        push_tokens_folder = {
            "name": "Push Notification Tokens",
            "item": [
                self.create_request(
                    "List Push Tokens",
                    "GET",
                    "/api/notifications/push-tokens/",
                    description="Get all registered push tokens for user"
                ),
                self.create_request(
                    "Register Push Token",
                    "POST",
                    "/api/notifications/push-tokens/",
                    body={
                        "device_type": "android",
                        "token": "ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]"
                    },
                    description="Register new push notification token"
                ),
                self.create_request(
                    "Register iOS Push Token",
                    "POST",
                    "/api/notifications/push-tokens/",
                    body={
                        "device_type": "ios",
                        "token": "ios_device_token_here"
                    },
                    description="Register iOS push notification token"
                ),
                self.create_request(
                    "Register Web Push Token",
                    "POST",
                    "/api/notifications/push-tokens/",
                    body={
                        "device_type": "web",
                        "token": "web_push_token_here"
                    },
                    description="Register web push notification token"
                ),
                self.create_request(
                    "Get Specific Push Token",
                    "GET",
                    "/api/notifications/push-tokens/1/",
                    description="Get specific push token details"
                ),
                self.create_request(
                    "Update Push Token",
                    "PUT",
                    "/api/notifications/push-tokens/1/",
                    body={
                        "token": "updated_token_here",
                        "is_active": True
                    },
                    description="Update push token"
                ),
                self.create_request(
                    "Delete Push Token",
                    "DELETE",
                    "/api/notifications/push-tokens/1/",
                    description="Delete push token"
                )
            ]
        }
        
        collection["item"] = [notifications_folder, messages_folder, preferences_folder, push_tokens_folder]
        return collection

    def generate_ml_suggestions_collection(self):
        """Generate AI/ML suggestions endpoints"""
        collection = self.create_base_collection(
            "Rithmo API - AI Suggestions", 
            "AI-powered health suggestions and feedback endpoints"
        )
        
        suggestions_folder = {
            "name": "AI Suggestions",
            "item": [
                self.create_request(
                    "Get AI Health Suggestion",
                    "GET",
                    "/api/ai/suggestions/",
                    description="Get personalized AI health suggestion based on current cycle and wellness data"
                ),
                self.create_request(
                    "Get Suggestion History",
                    "GET",
                    "/api/ai/suggestion-history/",
                    description="Get history of AI suggestions with feedback"
                ),
                self.create_request(
                    "Give Positive Feedback",
                    "POST",
                    "/api/ai/feedback/1/",
                    body={
                        "feedback": True,
                        "corrected_label": "",
                        "response_text": ""
                    },
                    description="Give positive feedback on AI suggestion"
                ),
                self.create_request(
                    "Give Negative Feedback with Correction",
                    "POST",
                    "/api/ai/feedback/1/",
                    body={
                        "feedback": False,
                        "corrected_label": "High stress: meditation recommended",
                        "response_text": "Try 10 minutes of meditation instead"
                    },
                    description="Give negative feedback with corrected suggestion"
                ),
                self.create_request(
                    "Update Suggestion Response",
                    "POST",
                    "/api/ai/feedback/1/",
                    body={
                        "response_text": "Try 30 minutes of light exercise like walking or yoga"
                    },
                    description="Update the response text for a suggestion"
                )
            ]
        }
        
        model_folder = {
            "name": "Model Management",
            "item": [
                self.create_request(
                    "Get Model Status",
                    "GET",
                    "/api/ai/model-status/",
                    description="Check AI model status and information",
                    auth_required=False
                ),
                self.create_request(
                    "Debug Suggestions",
                    "GET",
                    "/api/ai/debug-suggestions/",
                    description="Debug endpoint to check user's suggestions (development only)"
                )
            ]
        }
        
        collection["item"] = [suggestions_folder, model_folder]
        return collection

    def generate_master_collection(self):
        """Generate master collection with all endpoints"""
        collection = self.create_base_collection(
            "Rithmo API - Complete Collection", 
            "Complete API collection for Rithmo Period Tracker application with all endpoints"
        )
        
        # Get all individual collections
        auth_collection = self.generate_auth_collection()
        profile_collection = self.generate_user_profile_collection()
        cycle_collection = self.generate_cycle_tracker_collection()
        notifications_collection = self.generate_notifications_collection()
        ml_collection = self.generate_ml_suggestions_collection()
        
        # Combine all items
        collection["item"] = (
            auth_collection["item"] + 
            profile_collection["item"] + 
            cycle_collection["item"] + 
            notifications_collection["item"] + 
            ml_collection["item"]
        )
        
        return collection

    def save_collection(self, collection, filename):
        """Save collection to file"""
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(collection, f, indent=2, ensure_ascii=False)
        
        return filepath

    def generate_all_collections(self):
        """Generate all collections and save them"""
        collections = {
            "master_collection.json": self.generate_master_collection(),
            "auth_collection.json": self.generate_auth_collection(),
            "user_profile_collection.json": self.generate_user_profile_collection(),
            "cycle_tracker_collection.json": self.generate_cycle_tracker_collection(),
            "notifications_collection.json": self.generate_notifications_collection(),
            "ml_suggestions_collection.json": self.generate_ml_suggestions_collection()
        }
        
        generated_files = []
        total_endpoints = 0
        
        for filename, collection in collections.items():
            filepath = self.save_collection(collection, filename)
            endpoint_count = sum(len(folder.get('item', [])) for folder in collection['item'])
            total_endpoints += endpoint_count
            
            generated_files.append({
                'file': filepath,
                'name': collection['info']['name'],
                'endpoints': endpoint_count
            })
        
        return generated_files, total_endpoints


def main():
    """Main function to generate all Postman collections"""
    print("🚀 Generating Rithmo API Postman Collections...")
    print(f"📍 Base URL: {BASE_URL}")
    print(f"📁 Output Directory: {OUTPUT_DIR}")
    print("-" * 60)
    
    generator = PostmanCollectionGenerator(BASE_URL)
    generated_files, total_endpoints = generator.generate_all_collections()
    
    print("✅ Collections Generated Successfully!")
    print("-" * 60)
    
    for file_info in generated_files:
        print(f"📄 {file_info['name']}")
        print(f"   📁 File: {file_info['file']}")
        print(f"   🔗 Endpoints: {file_info['endpoints']}")
        print()
    
    print(f"📊 Total Endpoints: {total_endpoints}")
    print("-" * 60)
    print("📋 Import Instructions:")
    print("1. Open Postman")
    print("2. Click 'Import' button")
    print("3. Select any of the generated JSON files")
    print("4. Use 'master_collection.json' for complete API")
    print("5. Use individual collections for specific features")
    print("6. After login, tokens will be automatically saved")
    print("\n🔑 Authentication:")
    print("- First run 'Login (Get JWT Token)' from Authentication folder")
    print("- Access token will be automatically set for all requests")
    print("- Use refresh token endpoint when access token expires")


if __name__ == "__main__":
    main()