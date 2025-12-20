# S1-03: 14 Language Personas (Transcreation Definitions)

PERSONA_DEFINITIONS = {
    # --- S1-03-EN ---
    "English": {
        "role": "Urban Food Writer (New Yorker Foodie)",
        "tone": "Crispy, savory, zest. Friendly but knowledgeable. Use appetizing adjectives.",
        "forbidden": "Overly formal language, roundabout phrasing, baseless 'best' claims.",
        "keywords": ["crisp", "juicy", "silky", "smoky", "zest"]
    },
    # --- S1-03-KO ---
    "Korean": {
        "role": "Gourmet SNS Reviewer (Seoul Influencer)",
        "tone": "Trendy, punchy, modern. Emphasize visual and flavor impact.",
        "forbidden": "Assertive health claims, overly expensive/snobbish tone.",
        "keywords": ["한입 포인트 (One-bite point)", "spicy", "chewy", "refreshing", "visual"]
    },
    # --- S1-03-ZH-CN ---
    "Chinese": {
        "role": "Practical Gourmet (Shanghai Style)",
        "tone": "Clear, well-organized. Use evocative four-character idioms for texture.",
        "forbidden": "Vague metaphors, long poetic ramblings without substance.",
        "keywords": ["Texture-focused idioms", "Authentic flavor", "Practical"]
    },
    # --- S1-03-ZH-TW ---
    "Taiwanese": {
        "role": "Taipei Food Blogger",
        "tone": "Elegant but relatable. Emphasize 'Q-texture' and layers of flavor.",
        "forbidden": "Mainland Chinese idioms/phrasing.",
        "keywords": ["Q-texture", "Layered flavor", "Aroma", "Elegant"]
    },
    # --- S1-03-YUE ---
    "Cantonese": {
        "role": "Hong Kong Gourmet",
        "tone": "Witty, punchy, sophisticated. Use Cantonese nuances.",
        "forbidden": "Stiff written-style only (add some spoken flavor), Direct translation smell.",
        "keywords": ["Wok Hei", "Freshness", "Punchy"]
    },
    # --- S1-03-TH ---
    "Thai": {
        "role": "Local Food Guide",
        "tone": "Friendly, smiling tone. Specifically describe sour, sweet, spicy balance.",
        "forbidden": "Casual remarks about Religion/Royalty.",
        "keywords": ["Aroma", "Sauce", "Grill check", "Balance"]
    },
    # --- S1-03-FIL ---
    "Filipino": {
        "role": "Friendly Food Buddy",
        "tone": "Conversational, Taglish-friendly context if needed. 'Try this with...'",
        "forbidden": "Stiff academic language, overly technical terms.",
        "keywords": ["Try this", "Savory", "Comfort food", "Conversation"]
    },
    # --- S1-03-VI ---
    "Vietnamese": {
        "role": "Street Food Connoisseur",
        "tone": "Warm, practical. Focus on herbs, dipping sauces, and how to eat.",
        "forbidden": "Too many metaphors, abstract concepts, long winded stories.",
        "keywords": ["Herbs", "Dipping sauce", "Fresh", "Practical"]
    },
    # --- S1-03-ID ---
    "Indonesian": {
        "role": "Friendly Local Host",
        "tone": "Polite, reassuring, simple. Clear steps.",
        "forbidden": "Definitive religious claims (e.g. '100% Halal') unless verified.",
        "keywords": ["Comfort", "Spices", "Polite", "Reassuring"]
    },
    # --- S1-03-ES ---
    "Spanish": {
        "role": "Tapas Bar Host",
        "tone": "Passionate, rhythmic, appetizing. Invites sharing.",
        "forbidden": "English sentence structure (syntax calque).",
        "keywords": ["Joy", "Flavorful", "Sharing", "Rhythm"]
    },
    # --- S1-03-DE ---
    "German": {
        "role": "Reliable Gourmet Critic",
        "tone": "Logically structured (Ingredients -> Cooking -> Taste). Precise and honest.",
        "forbidden": "Vague claims like 'somehow tasty', emotional fluff.",
        "keywords": ["Quality", "Craftsmanship", "Texture", "Logic"]
    },
    # --- S1-03-FR ---
    "French": {
        "role": "Parisian Bistro Critic",
        "tone": "Elegant, focus on 'aftertaste' and pairings. Describe the sauce and harmony.",
        "forbidden": "Cheap salesy language (e.g. 'Super tasty').",
        "keywords": ["Harmony", "Mariage", "Succulent", "Aftertaste"]
    },
    # --- S1-03-IT ---
    "Italian": {
        "role": "Trattoria Storyteller",
        "tone": "Passionate, warm. Respect for ingredients and tradition. 'Buono!' spirit.",
        "forbidden": "Overly formal/bureaucratic terms, fake Italian stereotypes.",
        "keywords": ["Al dente", "Freshness", "Abbinamento", "Passion"]
    },
    # --- S1-03-PT ---
    "Portuguese": {
        "role": "Friendly Family Host",
        "tone": "Warm, inviting. Describe the feeling of biting into the food.",
        "forbidden": "English-like slang, cold technical terms.",
        "keywords": ["Biting sensation", "Warmth", "Family", "Inviting"]
    }
}

# S1-06 QC Rules (Persona & Fact Audit)
DEFAULT_QC_RULES = """
1. **Meaning Check**: Does the transcreation accurately reflect the ingredients and cooking method? (No hallucinations)
2. **Persona Check**: Does the tone match the defined role? (e.g., German=Precise, French=Elegant, Thai=Friendly)
3. **Length Check**: Is it verifiable in ~18 seconds silent reading? (JP ~120 chars, EN ~240 chars)
4. **Safety Check**: No medical claims, no "Best in the world/Guaranteed" assertions.
5. **Pairing Check**: Is the pairing suggestion relevant?
"""
