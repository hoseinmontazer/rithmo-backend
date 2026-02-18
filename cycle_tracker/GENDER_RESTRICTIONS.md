# Cycle Tracker Gender-Based Access Control

## Overview
The cycle tracker has been updated to implement gender-based restrictions:

- **Female users**: Can track their own menstrual cycles, periods, ovulation, and wellness data
- **Male users**: Can only view their partner's cycle data (read-only access to partner's information)
- **Users without gender set**: Cannot access cycle tracking features

## Changes Made

### 1. Models (`cycle_tracker/models.py`)
- Added gender validation in `Period.save()` method
- Prevents period creation for non-female users at the database level
- Raises `ValidationError` if a male user attempts to create a period entry

### 2. Serializers (`cycle_tracker/serializers.py`)
- Added `validate()` method in `PeriodSerializer`
- Checks user gender before allowing period creation
- Returns clear error messages for non-female users

### 3. Views (`cycle_tracker/views.py`)

#### PeriodViewSet
- Added gender checks in `create()`, `update()`, and `partial_update()` methods
- Updated `get_queryset()` to handle different scenarios:
  - Female users: Returns their own periods
  - Male users: Returns partner's periods (if partner is linked)
  - No gender/none: Returns empty queryset

#### OvulationDetailView
- Added gender-based logic:
  - Female users: View their own ovulation data
  - Male users: View partner's ovulation data (if partner is linked)
  - Includes partner name in response for male users

#### Other Endpoints
- All analysis endpoints (`cycle_analysis`, `wellness_correlation`, `cycle_insights`, `symptom_patterns`) already check for female gender
- Male users viewing partner data get appropriate support tips and information

## API Behavior

### For Female Users
```json
POST /api/periods/
{
  "start_date": "2024-01-15",
  "symptoms": "cramps, fatigue"
}
// ✅ Success - Period created
```

### For Male Users
```json
POST /api/periods/
{
  "start_date": "2024-01-15"
}
// ❌ Error 403
{
  "error": "Period tracking is only available for female users.",
  "message": "Male users can track their partner's cycle by linking a partner in their profile."
}
```

```json
GET /api/periods/
// ✅ Success - Returns partner's periods (if partner is linked)
// ❌ Empty array if no partner is linked
```

### Partner Tracking for Male Users
Male users can:
- View partner's period history (GET /api/periods/)
- View partner's cycle analysis (GET /api/periods/cycle_analysis/)
- View partner's ovulation data (GET /api/ovulation/)
- Receive notifications about partner's cycle phases
- Get support tips based on partner's current cycle phase

Male users cannot:
- Create new period entries
- Update or delete period entries
- Access wellness correlation or symptom patterns (female-only features)

## Partner Linking
To enable partner tracking for male users:
1. User must have gender set to 'male' in their profile
2. User must link a female partner in their UserProfile
3. Partner must have period data tracked

## Error Messages
- `"Period tracking is only available for female users."` - Attempting to create/update periods as male
- `"No partner linked. Please link a partner to view ovulation data."` - Male user without partner
- `"Cycle insights are only available for female users"` - Accessing female-only analysis endpoints
