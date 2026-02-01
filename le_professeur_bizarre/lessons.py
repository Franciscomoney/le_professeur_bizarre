"""
French Lessons for Le Professeur Bizarre
Structured lessons that Reachy teaches
"""

LESSONS = {
    "greetings": {
        "title": "Greetings & Basics",
        "description": "Learn how to say hello, goodbye, and basic pleasantries",
        "icon": "👋",
        "phrases": [
            {
                "english": "Hello",
                "french": "Bonjour",
                "pronunciation": "bohn-ZHOOR",
                "tip": "Use this until evening, then switch to 'Bonsoir'",
                "cultural_fact": "In France, you MUST say Bonjour when entering any shop. Not doing so is considered extremely rude!"
            },
            {
                "english": "Good evening",
                "french": "Bonsoir",
                "pronunciation": "bohn-SWAHR",
                "tip": "Use after around 6 PM",
                "cultural_fact": "The French take their greetings seriously - they'll judge your entire character based on how you say hello!"
            },
            {
                "english": "How are you?",
                "french": "Comment ça va?",
                "pronunciation": "koh-mahn sah VAH",
                "tip": "Casual version. Formal: 'Comment allez-vous?'",
                "cultural_fact": "This phrase literally asks about your digestive system! King Louis XIV used it to monitor his court's health."
            },
            {
                "english": "I'm fine, thank you",
                "french": "Ça va bien, merci",
                "pronunciation": "sah vah bee-EN, mair-SEE",
                "tip": "Even if you're having a terrible day, this is the expected response",
                "cultural_fact": "Unlike Americans who might share their life story, the French keep it brief!"
            },
            {
                "english": "Goodbye",
                "french": "Au revoir",
                "pronunciation": "oh ruh-VWAHR",
                "tip": "Literally means 'until we see each other again'",
                "cultural_fact": "The French have many goodbyes: 'Salut' (casual), 'À bientôt' (see you soon), 'Bonne journée' (have a good day)"
            },
            {
                "english": "Please",
                "french": "S'il vous plaît",
                "pronunciation": "seel voo PLAY",
                "tip": "Literally: 'if it pleases you' - very polite!",
                "cultural_fact": "The French find Americans say 'please' too much, making it seem insincere!"
            },
            {
                "english": "Thank you very much",
                "french": "Merci beaucoup",
                "pronunciation": "mair-SEE boh-KOO",
                "tip": "Don't overuse it or you'll sound like a tourist!",
                "cultural_fact": "The French thank less frequently but more meaningfully than Americans."
            }
        ]
    },
    "restaurant": {
        "title": "At the Restaurant",
        "description": "Essential phrases for dining in France",
        "icon": "🍽️",
        "phrases": [
            {
                "english": "A table for two, please",
                "french": "Une table pour deux, s'il vous plaît",
                "pronunciation": "oon TAHBL poor DUH, seel voo PLAY",
                "tip": "The waiter might ask 'Vous avez réservé?' (Did you reserve?)",
                "cultural_fact": "In France, you wait to be seated. Don't just grab a table like in America!"
            },
            {
                "english": "The menu, please",
                "french": "La carte, s'il vous plaît",
                "pronunciation": "lah KART, seel voo PLAY",
                "tip": "'Le menu' actually means the fixed-price meal!",
                "cultural_fact": "French menus often have no pictures - you're expected to know what you're ordering!"
            },
            {
                "english": "I would like...",
                "french": "Je voudrais...",
                "pronunciation": "zhuh voo-DRAY",
                "tip": "More polite than 'Je veux' (I want)",
                "cultural_fact": "The French consider saying 'I want' to be rude - always use 'I would like'!"
            },
            {
                "english": "The check, please",
                "french": "L'addition, s'il vous plaît",
                "pronunciation": "lah-dee-see-OHN, seel voo PLAY",
                "tip": "You MUST ask for it - they'll never bring it automatically",
                "cultural_fact": "In France, rushing someone through a meal is the ultimate insult. The waiter is being POLITE by not bringing the check!"
            },
            {
                "english": "It's delicious!",
                "french": "C'est délicieux!",
                "pronunciation": "say day-lee-see-UH",
                "tip": "The chef will appreciate this compliment",
                "cultural_fact": "The French take their food very seriously - a compliment to the chef is like a standing ovation!"
            },
            {
                "english": "A glass of red wine",
                "french": "Un verre de vin rouge",
                "pronunciation": "uhn VEHR duh van ROOZH",
                "tip": "Wine is often cheaper than water in France!",
                "cultural_fact": "Asking for ice in your wine is a crime against humanity in France. Don't do it."
            }
        ]
    },
    "emergency": {
        "title": "Essential Phrases",
        "description": "Phrases you need to know for getting around",
        "icon": "🆘",
        "phrases": [
            {
                "english": "Excuse me",
                "french": "Excusez-moi",
                "pronunciation": "ex-koo-zay MWAH",
                "tip": "Use this to get someone's attention politely",
                "cultural_fact": "The French value personal space - always say this before interrupting someone!"
            },
            {
                "english": "I don't understand",
                "french": "Je ne comprends pas",
                "pronunciation": "zhuh nuh kohm-PRAHN pah",
                "tip": "They might switch to English (but appreciate you trying!)",
                "cultural_fact": "The French respect effort - even bad French is better than assuming everyone speaks English!"
            },
            {
                "english": "Where is the bathroom?",
                "french": "Où sont les toilettes?",
                "pronunciation": "oo sohn lay twah-LET",
                "tip": "In cafes, you usually need to buy something first",
                "cultural_fact": "French public toilets can be... adventures. Some are just holes in the ground!"
            },
            {
                "english": "I am lost",
                "french": "Je suis perdu",
                "pronunciation": "zhuh swee pair-DOO",
                "tip": "Add 'e' at the end if you're female: 'perdue'",
                "cultural_fact": "The French love giving directions, even if they're not entirely sure!"
            },
            {
                "english": "Can you help me?",
                "french": "Pouvez-vous m'aider?",
                "pronunciation": "poo-vay VOO may-DAY",
                "tip": "Always start with 'Excusez-moi' first",
                "cultural_fact": "Parisians have a reputation for being unhelpful, but outside Paris, people are incredibly warm!"
            },
            {
                "english": "I don't speak French well",
                "french": "Je ne parle pas bien français",
                "pronunciation": "zhuh nuh PARL pah bee-EN frahn-SAY",
                "tip": "This humble admission will earn you goodwill!",
                "cultural_fact": "The French appreciate any attempt at their language, even if imperfect!"
            }
        ]
    },
    "flirting": {
        "title": "Romance & Compliments",
        "description": "Because it's France, after all! 💕",
        "icon": "❤️",
        "phrases": [
            {
                "english": "You have beautiful eyes",
                "french": "Vous avez de beaux yeux",
                "pronunciation": "vooz ah-VAY duh boh ZYUH",
                "tip": "A classic French compliment!",
                "cultural_fact": "The French are masters of the subtle compliment - it's an art form there!"
            },
            {
                "english": "Would you like to have a coffee?",
                "french": "Voulez-vous prendre un café?",
                "pronunciation": "voo-lay VOO prahn-druh uhn kah-FAY",
                "tip": "Coffee = casual date in France",
                "cultural_fact": "In France, asking for coffee is like asking someone out. It's more intimate than it sounds!"
            },
            {
                "english": "You are very charming",
                "french": "Vous êtes très charmant(e)",
                "pronunciation": "vooz ET tray shar-MAHN(T)",
                "tip": "Add the 't' sound for feminine",
                "cultural_fact": "The French invented the word 'charming' - they take it very seriously!"
            },
            {
                "english": "I love you",
                "french": "Je t'aime",
                "pronunciation": "zhuh TEM",
                "tip": "Only say this if you REALLY mean it!",
                "cultural_fact": "The French don't throw around 'I love you' casually like Americans. It's reserved for true love!"
            }
        ]
    }
}

def get_lesson(lesson_id: str) -> dict:
    """Get a specific lesson by ID"""
    return LESSONS.get(lesson_id)

def get_all_lessons() -> dict:
    """Get all available lessons"""
    return {
        lesson_id: {
            "title": lesson["title"],
            "description": lesson["description"],
            "icon": lesson["icon"],
            "phrase_count": len(lesson["phrases"])
        }
        for lesson_id, lesson in LESSONS.items()
    }

def get_phrase(lesson_id: str, phrase_index: int) -> dict:
    """Get a specific phrase from a lesson"""
    lesson = LESSONS.get(lesson_id)
    if lesson and 0 <= phrase_index < len(lesson["phrases"]):
        phrase = lesson["phrases"][phrase_index]
        phrase["lesson_id"] = lesson_id
        phrase["phrase_index"] = phrase_index
        phrase["total_phrases"] = len(lesson["phrases"])
        phrase["is_last"] = phrase_index == len(lesson["phrases"]) - 1
        return phrase
    return None
