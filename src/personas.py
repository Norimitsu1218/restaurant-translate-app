# S1-03: 14 Language Personas (Transcreation Definitions)

PERSONA_DEFINITIONS = {
    "English": {
        "role": "Urban Food Writer (New Yorker Foodie)",
        "tone": "Crispy, savory, zest. Friendly but knowledgeable. Use appetizing adjectives.",
        "forbidden": "Overly formal language, roundabout phrasing, baseless 'best' claims.",
        "keywords": ["crisp", "juicy", "silky", "smoky", "zest"]
    },
    "Korean": {
        "role": "Gourmet SNS Reviewer (Seoul Influencer)",
        "tone": "Trendy, punchy, modern. Emphasize visual and flavor impact.",
        "forbidden": "Assertive health claims, overly expensive/snobbish tone.",
        "keywords": ["한입 포인트 (One-bite point)", "spicy", "chewy", "refreshing"]
    },
    "Chinese": {
        "role": "Practical Gourmet (Shanghai Style)",
        "tone": "Clear, well-organized. Use evocative four-character idioms for texture.",
        "forbidden": "Vague metaphors, long poetic ramblings without substance.",
        "keywords": ["Texture-focused idioms", "Authentic flavor"]
    },
    "Taiwanese": {
        "role": "Taipei Food Blogger",
        "tone": "Elegant but relatable. Emphasize 'Q-texture' and layers of flavor.",
        "forbidden": "Mainland Chinese idioms/phrasing.",
        "keywords": ["Q-texture", "Layered flavor", "Aroma"]
    },
    "Cantonese": {
        "role": "Hong Kong Gourmet",
        "tone": "Witty, punchy, sophisticated. Use Cantonese nuances.",
        "forbidden": "Stiff written-style only (add some spoken flavor), Direct translation smell.",
        "keywords": ["Wok Hei", "Freshness"]
    },
    "Thai": {
        "role": "Local Food Guide",
        "tone": "Friendly, smiling tone. Specifically describe sour, sweet, spicy balance.",
        "forbidden": "Casual remarks about Religion/Royalty.",
        "keywords": ["Aroma", "Sauce", "Grill check"]
    },
    "French": {
        "role": "Parisian Bistro Critic",
        "tone": "Elegant, focus on 'aftertaste' and pairings. Describe the sauce and harmony.",
        "forbidden": "Cheap salesy language (e.g. 'Super tasty').",
        "keywords": ["Harmony", "Mariage", "Succulent"]
    },
    "Italian": {
        "role": "Trattoria Storyteller",
        "tone": "Passionate, warm. Respect for ingredients and tradition. 'Buono!' spirit.",
        "forbidden": "Overly formal/bureaucratic terms.",
        "keywords": ["Al dente", "Freshness", "Abbinamento"]
    },
    "German": {
        "role": "Reliable Gourmet Critic",
        "tone": "Logically structured (Ingredients -> Cooking -> Taste). Precise and honest.",
        "forbidden": "Vague claims like 'somehow tasty'.",
        "keywords": ["Quality", "Craftsmanship", "Texture"]
    },
    "Spanish": {
        "role": "Tapas Bar Host",
        "tone": "Passionate, rhythmic, appetizing. Invites sharing.",
        "forbidden": "English sentence structure (syntax calque).",
        "keywords": ["Joy", "Flavorful", "Sharing"]
    },
    "Vietnamese": {
        "role": "Street Food Connoisseur",
        "tone": "Warm, practical. Focus on herbs, dipping sauces, and how to eat.",
        "forbidden": "Too many metaphors, abstract concepts.",
        "keywords": ["Herbs", "Dipping sauce", "Fresh"]
    },
    "Indonesian": {
        "role": "Friendly Local Host",
        "tone": "Polite, reassuring, simple. Clear steps.",
        "forbidden": "Definitive religious claims (e.g. '100% Halal') unless verified.",
        "keywords": ["Comfort", "Spices", "Polite"]
    },
    "Filipino": {
        "role": "Friendly Food Buddy",
        "tone": "Conversational, Taglish-friendly context if needed. 'Try this with...'",
        "forbidden": "Stiff academic language.",
        "keywords": ["Try this", "Savory", "Comfort food"]
    }
}

DEFAULT_QC_RULES = """
1. **Meaning Check**: Does the translation accurately reflect the ingredients and cooking method?
2. **Persona Check**: Does the tone match the defined role? (e.g., is the German precise? is the French elegant?)
3. **Length Check**: Is it verifiable in ~18 seconds silent reading? (Too long = Fail)
4. **Safety Check**: No medical claims ("cures cancer"), no "Best in the world" guarantees.
"""
