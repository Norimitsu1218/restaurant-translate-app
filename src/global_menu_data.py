# Common Menu Dictionary for Cost Reduction (Suzuka Architecture)
# Format: "Normalized Japanese Name": { "en": "...", "zh": "...", ... }

GLOBAL_MENU_DICT = {
    "枝豆": {
        "en": "Edamame",
        "description_en": "Boiled soybeans in the pod, lightly salted. A classic Japanese appetizer."
    },
    "生ビール": {
        "en": "Draft Beer",
        "description_en": "Freshly poured draft beer."
    },
    "唐揚げ": {
        "en": "Fried Chicken (Karaage)",
        "description_en": "Japanese-style deep-fried chicken, marinated in soy sauce and ginger."
    },
    "冷奴": {
        "en": "Chilled Tofu (Hiyayakko)",
        "description_en": "Cold tofu topped with green onions and ginger."
    },
    "刺身盛り合わせ": {
        "en": "Sashimi Assortment",
        "description_en": "Chef's selection of fresh seasonal raw fish."
    },
    "シーザーサラダ": {
        "en": "Caesar Salad",
        "description_en": "Fresh salad with caesar dressing, croutons, and cheese."
    },
    "ポテトフライ": {
        "en": "French Fries",
        "description_en": "Crispy fried potatoes."
    }
}

def lookup_global_menu(name_ja: str):
    """
    Normalizes the input name and looks it up in the dictionary.
    Returns None if not found.
    """
    norm_name = name_ja.strip().replace(" ", "").replace("　", "")
    return GLOBAL_MENU_DICT.get(norm_name)
