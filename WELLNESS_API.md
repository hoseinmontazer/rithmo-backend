# Wellness API Documentation

## Overview
Comprehensive wellness tracking and analytics API that allows users to log daily wellness data and get computed insights.

## Endpoints

### 1. Create/Update Wellness Log
**POST** `/api/wellness/`

Creates or updates today's wellness log with automatic score calculation.

**Request Body:**
```json
{
  "stress_level": 5,
  "sleep_hours": 7.5,
  "mood_level": 7,
  "energy_level": 8,
  "pain_level": 2,
  "exercise_minutes": 30,
  "nutrition_quality": 4,
  "caffeine_intake": 2,
  "alcohol_intake": 0,
  "smoking": 0,
  "anxiety_level": 3,
  "focus_level": 7,
  "steps": 8500,
  "calories_burned": 350,
  "calories_intake": 2000,
  "water_intake_ml": 2500,
  "notes": "Felt great today!"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Wellness log created",
  "data": {
    "id": 1,
    "date": "2026-02-21",
    "wellness_score": 78.5,
    "sleep_score": 85.0,
    "activity_score": 85.0,
    "mental_score": 68.0,
    ...
  }
}
```

---

### 2. Get Wellness Analytics
**GET** `/api/wellness/analytics/?days=30`

Get comprehensive wellness analytics for a specified period.

**Query Parameters:**
- `days` (optional): Number of days to analyze (default: 30)

**Response:**
```json
{
  "status": "success",
  "data": {
    "period": {
      "start_date": "2026-01-22",
      "end_date": "2026-02-21",
      "days": 30,
      "logs_count": 25
    },
    "averages": {
      "wellness_score": 75.3,
      "sleep_hours": 7.2,
      "mood_level": 6.8,
      "energy_level": 7.1,
      "stress_level": 4.5,
      "anxiety_level": 3.2,
      "pain_level": 2.1,
      "steps": 7850,
      "water_ml": 2300,
      "exercise_minutes": 25
    },
    "trends": {
      "wellness": {
        "change": 5.2,
        "direction": "improving"
      },
      "sleep": {
        "change": 0.8,
        "direction": "improving"
      },
      "mood": {
        "change": 1.2,
        "direction": "improving"
      },
      "energy": {
        "change": -0.5,
        "direction": "declining"
      }
    },
    "best_day": {
      "date": "2026-02-15",
      "wellness_score": 92.5
    },
    "worst_day": {
      "date": "2026-01-28",
      "wellness_score": 45.2
    },
    "insights": [
      {
        "category": "sleep",
        "type": "positive",
        "message": "Great job! Your sleep average of 7.2 hours is in the healthy range."
      },
      {
        "category": "activity",
        "type": "positive",
        "message": "Excellent! You're averaging 7850 steps per day."
      },
      {
        "category": "overall",
        "type": "positive",
        "message": "Your overall wellness is improving! Keep up the good work."
      }
    ]
  }
}
```

---

### 3. Get Weekly Summary
**GET** `/api/wellness/weekly_summary/`

Get a summary of the past 7 days with daily breakdown.

**Response:**
```json
{
  "status": "success",
  "data": {
    "week_start": "2026-02-14",
    "week_end": "2026-02-21",
    "daily_logs": [
      {
        "date": "2026-02-14",
        "wellness_score": 75.5,
        "sleep_hours": 7.0,
        "mood_level": 7,
        "energy_level": 8,
        "stress_level": 4,
        "steps": 8200
      },
      ...
    ],
    "weekly_averages": {
      "wellness_score": 76.8,
      "sleep_hours": 7.3,
      "mood_level": 7.2,
      "energy_level": 7.5,
      "stress_level": 4.1
    },
    "logs_count": 6,
    "completion_rate": 85.7
  }
}
```

---

### 4. Get Today's Log
**GET** `/api/wellness/today/`

Get today's wellness log if it exists.

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "date": "2026-02-21",
    "wellness_score": 78.5,
    "sleep_score": 85.0,
    "activity_score": 85.0,
    "mental_score": 68.0,
    "stress_level": 5,
    "sleep_hours": 7.5,
    ...
  }
}
```

---

### 5. Get Tracking Streaks
**GET** `/api/wellness/streaks/`

Calculate wellness tracking streaks and consistency.

**Response:**
```json
{
  "status": "success",
  "data": {
    "current_streak": 12,
    "longest_streak": 25,
    "total_logs": 87,
    "last_log_date": "2026-02-21"
  }
}
```

---

### 6. List All Wellness Logs
**GET** `/api/wellness/`

Get paginated list of all wellness logs.

**Response:**
```json
{
  "count": 87,
  "next": "http://api.example.com/api/wellness/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "date": "2026-02-21",
      "wellness_score": 78.5,
      ...
    },
    ...
  ]
}
```

---

## Wellness Score Calculation

### Components:
1. **Sleep Score (30% weight)**
   - Optimal: 7-9 hours = 100 points
   - Less than 7: Proportional reduction
   - More than 9: Penalty for oversleeping

2. **Activity Score (30% weight)**
   - Based on steps (10,000 = 100 points)
   - Bonus for exercise minutes (30 min = +20 points)

3. **Mental Score (40% weight)**
   - Starts at 100
   - Reduced by stress level (×8)
   - Reduced by anxiety level (×8)
   - Reduced by pain level (×5)
   - Bonus for high mood (>5)
   - Bonus for high energy (>5)

### Overall Wellness Score:
```
wellness_score = (sleep_score × 0.3) + (activity_score × 0.3) + (mental_score × 0.4)
```

---

## Field Descriptions

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| stress_level | int | 0-10 | Stress level (0=none, 10=extreme) |
| sleep_hours | float | 0-24 | Hours of sleep |
| mood_level | int | 0-10 | Mood level (0=very bad, 10=excellent) |
| energy_level | int | 0-10 | Energy level (0=exhausted, 10=energized) |
| pain_level | int | 0-10 | Pain level (0=none, 10=severe) |
| exercise_minutes | int | 0+ | Minutes of exercise |
| nutrition_quality | int | 1-5 | Diet quality (1=poor, 5=excellent) |
| caffeine_intake | int | 0+ | Cups of caffeinated drinks |
| alcohol_intake | int | 0+ | Alcoholic drinks consumed |
| smoking | int | 0+ | Cigarettes smoked |
| anxiety_level | int | 0-10 | Anxiety level (0=calm, 10=severe) |
| focus_level | int | 0-10 | Focus/concentration (0=none, 10=excellent) |
| steps | int | 0+ | Daily step count |
| calories_burned | int | 0+ | Calories burned |
| calories_intake | int | 0+ | Calories consumed |
| water_intake_ml | int | 0+ | Water intake in milliliters |
| notes | text | - | Personal notes |

---

## Insights Categories

1. **Sleep**: Sleep duration and quality feedback
2. **Activity**: Steps and exercise recommendations
3. **Mental Health**: Stress and anxiety management
4. **Hydration**: Water intake suggestions
5. **Overall**: General wellness trends

---

## Usage Examples

### Track daily wellness:
```bash
curl -X POST https://api.rithmo.ir/api/wellness/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sleep_hours": 7.5,
    "mood_level": 8,
    "energy_level": 7,
    "stress_level": 3,
    "steps": 9000,
    "water_intake_ml": 2500
  }'
```

### Get 30-day analytics:
```bash
curl -X GET "https://api.rithmo.ir/api/wellness/analytics/?days=30" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Check today's log:
```bash
curl -X GET https://api.rithmo.ir/api/wellness/today/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```
