import random

def generate_response(label: str) -> list:
    """
    Return 3-4 possible English suggestions for a given primary_label.
    If label is known, use predefined suggestions.
    If label is unknown, generate generic but relevant suggestions.
    """

    mapping = {
        # ------------------ PERIOD & PMS ------------------
        "Period today: rest, hydration, iron-rich foods": [
            "Stay hydrated and rest as much as possible during your period.",
            "Include iron-rich foods like spinach or beans in your meals today.",
            "Listen to your body and avoid overexertion.",
            "Use a warm compress if you experience cramps."
        ],
        "Period today + poor sleep: prioritize rest & hydration": [
            "Since you had poor sleep, focus on napping or going to bed earlier tonight.",
            "Drink enough water and avoid caffeine overload.",
            "Try to relax with light activities and avoid stress.",
            "Resting will help both with sleep debt and period discomfort."
        ],
        "Period today with severe pain: consult doctor": [
            "Your pain level is high, please consider consulting a doctor.",
            "Avoid strenuous activity today and rest as much as possible.",
            "Pain relief methods like warm compresses may help temporarily.",
            "Seek medical help if the pain continues."
        ],
        "PMS symptoms: comfort, herbal tea, relaxation": [
            "Drink herbal tea like chamomile or ginger to ease PMS symptoms.",
            "Practice relaxation techniques such as deep breathing.",
            "Allow yourself to rest and avoid heavy exercise.",
            "Track your symptoms for better cycle management."
        ],
        "Pre-period phase: prepare body with self-care": [
            "Prepare by keeping healthy snacks and hot tea nearby.",
            "Focus on gentle exercise like walking or yoga.",
            "Stay hydrated to reduce bloating or discomfort.",
            "Maintain a regular bedtime routine for stability."
        ],
        "Upcoming period with stress: relaxation recommended": [
            "Try mindfulness or meditation to reduce stress.",
            "Take breaks and avoid overwhelming tasks.",
            "Hydrate and include calming herbal teas.",
            "Gentle stretching may help release tension."
        ],

        # ------------------ SLEEP ------------------
        "Severe sleep deprivation: urgent rest needed": [
            "Your body needs urgent rest—avoid all heavy activities.",
            "Try to nap during the day and sleep longer tonight.",
            "Limit screen time to recover your sleep cycle.",
            "If ongoing, consult a doctor for sleep issues."
        ],
        "Very poor sleep: short nap & avoid caffeine": [
            "Take a 20-minute nap to recharge.",
            "Avoid too much caffeine—it can worsen sleep.",
            "Relax and keep a light schedule today.",
            "Go to bed earlier than usual tonight."
        ],
        "Poor sleep: calming evening routine suggested": [
            "Create a calm environment with no screens before bed.",
            "Drink warm milk or herbal tea before bedtime.",
            "Avoid stressful work in the evening.",
            "Stick to a fixed bedtime to improve sleep quality."
        ],
        "Slight sleep deficit: aim for full rest tonight": [
            "Prioritize 7-8 hours of sleep tonight.",
            "Wind down with light stretching before bed.",
            "Avoid late caffeine to ensure quality sleep.",
            "Stay consistent with your sleep schedule."
        ],
        "Healthy sleep achieved: maintain consistency": [
            "Great job on good sleep—maintain the habit.",
            "Keep a consistent bedtime and wake time.",
            "Support healthy sleep with balanced nutrition.",
            "Avoid late-night screens to keep sleep quality."
        ],
        "Excessive sleep: ensure balance with activity": [
            "Too much sleep can reduce energy—balance it with light activity.",
            "Go for a short walk to energize your body.",
            "Stick to a fixed bedtime to avoid oversleeping.",
            "Monitor if excessive sleep continues regularly."
        ],

        # ------------------ STRESS ------------------
        "Extreme stress: professional help may be required": [
            "Your stress is extreme, please consider professional support.",
            "Do breathing or mindfulness but also seek help if needed.",
            "Reduce workload and focus only on essentials.",
            "Talk to a trusted person about your stress."
        ],
        "High stress: deep breathing & mindfulness": [
            "Do a 5-minute breathing exercise.",
            "Take a short break outdoors.",
            "Write your thoughts in a journal.",
            "Hydrate and avoid stimulants like caffeine."
        ],
        "Moderate stress: balance work & rest": [
            "Take small breaks during work.",
            "Use time management to avoid overload.",
            "Stay hydrated and avoid skipping meals.",
            "Do a light activity like walking."
        ],
        "Mild stress: short walk or music recommended": [
            "Take a short walk outside.",
            "Listen to relaxing music.",
            "Spend 5 minutes meditating.",
            "Drink water and rest briefly."
        ],
        "Low stress: good time for focus & productivity": [
            "Focus on your important tasks today.",
            "Use this low-stress time to be productive.",
            "Plan ahead for the week.",
            "Maintain good balance and avoid overworking."
        ],

        # ------------------ ENERGY ------------------
        "Exhaustion: urgent rest required": [
            "You are fully exhausted—rest is priority one.",
            "Avoid any physical or mental overload.",
            "Nap and hydrate to support recovery.",
            "Seek medical advice if fatigue continues."
        ],
        "Very low energy: naps and proper meals required": [
            "Take a nap and eat energy-boosting meals.",
            "Avoid strenuous activity today.",
            "Include protein and whole grains in diet.",
            "Drink enough water to prevent fatigue."
        ],
        "Low energy: light tasks only": [
            "Focus only on essential light tasks.",
            "Avoid physical strain and rest when possible.",
            "Short walks may help boost energy.",
            "Eat a healthy snack to support energy."
        ],
        "Moderate energy: steady pace": [
            "Pace yourself and avoid rushing tasks.",
            "Balance work with breaks.",
            "Hydrate regularly.",
            "Maintain steady energy with small meals."
        ],
        "Good energy: productive activities recommended": [
            "Use your good energy for productive work.",
            "Exercise moderately to channel energy.",
            "Stay hydrated to maintain balance.",
            "Plan your day effectively."
        ],
        "Very high energy: ideal time for workout or projects": [
            "Channel energy into exercise or projects.",
            "Do focused work during this peak energy.",
            "Avoid overcommitting despite high energy.",
            "Use your energy for something meaningful."
        ],

        # ------------------ NUTRITION ------------------
        "Very poor nutrition: eat balanced meals with protein/veggies": [
            "Plan meals with vegetables and protein.",
            "Avoid junk food and sugar.",
            "Cook a simple balanced meal today.",
            "Include fruits in your daily intake."
        ],
        "Poor nutrition: add fruits and fiber": [
            "Eat more fruits and high-fiber foods.",
            "Avoid skipping meals.",
            "Drink water with meals.",
            "Add leafy greens to your diet."
        ],
        "Average nutrition: maintain and improve": [
            "Maintain current diet but add more variety.",
            "Include colorful vegetables.",
            "Stay hydrated along with balanced meals.",
            "Avoid overeating or late-night snacks."
        ],
        "Good nutrition: balanced intake maintained": [
            "Keep up your balanced meals.",
            "Ensure regular eating schedule.",
            "Support nutrition with hydration.",
            "Continue to include fresh produce."
        ],
        "Excellent nutrition: keep habits strong": [
            "Great job! Keep eating healthy meals.",
            "Maintain consistency in diet.",
            "Support diet with good sleep.",
            "Encourage others with your example."
        ],

        # ------------------ HYDRATION ------------------
        "Severe dehydration risk: drink water immediately": [
            "Drink water immediately—your body needs it.",
            "Avoid caffeine and alcohol now.",
            "Eat fruits high in water like watermelon.",
            "Rest after hydrating."
        ],
        "Low hydration: increase water intake today": [
            "Drink a glass of water every hour.",
            "Carry a water bottle with you.",
            "Avoid dehydrating drinks like coffee.",
            "Eat hydrating foods such as cucumber."
        ],
        "Adequate hydration: maintain consistency": [
            "Keep drinking water regularly.",
            "Balance water intake across the day.",
            "Support hydration with fruits.",
            "Track your hydration habits."
        ],
        "Excellent hydration: well-balanced intake": [
            "Your hydration is excellent—keep it up!",
            "Stay consistent with drinking water.",
            "Add electrolytes if you exercise.",
            "Encourage hydration habits in routine."
        ],
    }

    # ------------------ FALLBACK ------------------
    default_templates = [
        "Take care of your health regarding '{}'.",
        "Pay attention to '{}' and rest if needed.",
        "Monitor your symptoms related to '{}'.",
        "Try to manage '{}' with self-care and mindfulness.",
        "Stay healthy and aware of '{}' today."
    ]

    # Return predefined suggestions if available
    if label in mapping:
        return random.choice(mapping[label])

    # Otherwise generate 3-4 generic suggestions covering the label
    # num_choices = random.randint(3, 4)
    # return [template.format(label) for template in random.sample(default_templates, num_choices)]
    return random.choice(default_templates).format(label)