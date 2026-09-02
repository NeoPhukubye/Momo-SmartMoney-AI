from fastapi import APIRouter, Form
from fastapi.responses import PlainTextResponse

router = APIRouter()

# USSD session store (in production, use Redis)
sessions: dict[str, dict] = {}

# Multilingual USSD menus
MENUS = {
    "en": {
        "main": """CON Welcome to SmartMoney AI
1. Check Balance & Spending
2. Send Money (with Scam Check)
3. My Stokvel
4. Savings Goal
5. Talk to Coach
6. Report Scam
7. Change Language""",
        "spending": """CON Your spending (last 30 days):
Income: R{income}
Spent: R{expenses}
Net: R{net}

0. Back to Main Menu""",
        "stokvel": """CON My Stokvels:
1. View my stokvels
2. Record contribution
3. Check next payout

0. Back""",
        "savings": """CON Savings Goals:
Your savings: R{savings}
Target: R{target}
Progress: {progress}%

1. Add to savings
0. Back""",
        "language": """CON Choose Language / Khetha Ulimi:
1. English
2. isiZulu
3. isiXhosa
4. Sesotho
5. Setswana
6. Afrikaans
7. Kiswahili
8. Français""",
    },
    "zu": {
        "main": """CON Siyakwamukela ku-SmartMoney AI
1. Bheka Ibhalansi Nokusebenzisa
2. Thumela Imali (nge-Scam Check)
3. Isitokofela Sami
4. Umgomo Wokulondoloza
5. Khuluma noMqeqeshi
6. Bika Ukukhwabanisa
7. Shintsha Ulimi""",
        "spending": """CON Ukusebenzisa kwakho (izinsuku 30):
Engenayo: R{income}
Esebenzisiwe: R{expenses}
Esele: R{net}

0. Emuva""",
        "stokvel": """CON Izitokofela Zami:
1. Buka izitokofela zami
2. Bhala umnikelo
3. Bheka ukukhokhwa okulandelayo

0. Emuva""",
        "savings": """CON Imigomo Yokulondoloza:
Okulondoloziwe: R{savings}
Umgomo: R{target}
Inqubekela: {progress}%

1. Engeza okulondoloziwe
0. Emuva""",
        "language": """CON Khetha Ulimi:
1. English
2. isiZulu
3. isiXhosa
4. Sesotho
5. Setswana
6. Afrikaans
7. Kiswahili
8. Français""",
    },
    "xh": {
        "main": """CON Wamkelekile ku-SmartMoney AI
1. Jonga Ibhalansi neNkcitho
2. Thumela Imali (ne-Scam Check)
3. Istokfela Sam
4. Injongo Yokonga
5. Thetha noMqeqeshi
6. Xela Ubuqhophololo
7. Tshintsha Ulwimi""",
        "spending": """CON Inkcitho yakho (iintsuku 30):
Ingeniso: R{income}
Inkcitho: R{expenses}
Eseleyo: R{net}

0. Buyela Umva""",
        "stokvel": """CON Izitokfela Zam:
1. Jonga izitokfela zam
2. Bhala umnikelo
3. Jonga intlawulo elandelayo

0. Buyela Umva""",
        "savings": """CON Iinjongo Zokonga:
Ekongiweyo: R{savings}
Injongo: R{target}
Inkqubela: {progress}%

1. Yongeza okongwayo
0. Buyela Umva""",
        "language": """CON Khetha Ulwimi:
1. English
2. isiZulu
3. isiXhosa
4. Sesotho
5. Setswana
6. Afrikaans
7. Kiswahili
8. Français""",
    },
    "st": {
        "main": """CON Rea u amohela ho SmartMoney AI
1. Sheba Balanse le Tshebediso
2. Romela Chelete (ka Scam Check)
3. Setokofela sa Ka
4. Sepheo sa Poloko
5. Bua le Moeletsi
6. Tlaleha Boqhekanyetsi
7. Fetola Puo""",
        "spending": """CON Tshebediso ya hao (matsatsi a 30):
Moputso: R{income}
E sebedisitsweng: R{expenses}
E setseng: R{net}

0. Morao""",
        "stokvel": """CON Litokofela tsa Ka:
1. Sheba litokofela tsa ka
2. Ngola mohlatsetsi
3. Sheba tefo e latelang

0. Morao""",
        "savings": """CON Sepheo sa Poloko:
E bolokilweng: R{savings}
Sepheo: R{target}
Tswelopele: {progress}%

1. Eketsa poloko
0. Morao""",
        "language": """CON Khetha Puo:
1. English
2. isiZulu
3. isiXhosa
4. Sesotho
5. Setswana
6. Afrikaans
7. Kiswahili
8. Français""",
    },
    "sw": {
        "main": """CON Karibu SmartMoney AI
1. Angalia Salio na Matumizi
2. Tuma Pesa (na Ukaguzi)
3. Kikundi Changu cha Akiba
4. Lengo la Akiba
5. Zungumza na Kocha
6. Ripoti Ulaghai
7. Badilisha Lugha""",
        "spending": """CON Matumizi yako (siku 30):
Mapato: R{income}
Matumizi: R{expenses}
Salio: R{net}

0. Rudi""",
        "stokvel": """CON Vikundi Vyangu:
1. Tazama vikundi
2. Rekodi mchango
3. Angalia malipo yafuatayo

0. Rudi""",
        "savings": """CON Lengo la Akiba:
Iliyookolewa: R{savings}
Lengo: R{target}
Maendeleo: {progress}%

1. Ongeza akiba
0. Rudi""",
        "language": """CON Chagua Lugha:
1. English
2. isiZulu
3. isiXhosa
4. Sesotho
5. Setswana
6. Afrikaans
7. Kiswahili
8. Français""",
    },
    "fr": {
        "main": """CON Bienvenue sur SmartMoney AI
1. Vérifier Solde et Dépenses
2. Envoyer de l'Argent (avec Vérification)
3. Ma Tontine
4. Objectif d'Épargne
5. Parler au Coach
6. Signaler une Arnaque
7. Changer la Langue""",
        "spending": """CON Vos dépenses (30 jours):
Revenus: R{income}
Dépensé: R{expenses}
Net: R{net}

0. Retour""",
        "stokvel": """CON Mes Tontines:
1. Voir mes tontines
2. Enregistrer une contribution
3. Prochain versement

0. Retour""",
        "savings": """CON Objectif d'Épargne:
Épargné: R{savings}
Objectif: R{target}
Progrès: {progress}%

1. Ajouter à l'épargne
0. Retour""",
        "language": """CON Choisir la Langue:
1. English
2. isiZulu
3. isiXhosa
4. Sesotho
5. Setswana
6. Afrikaans
7. Kiswahili
8. Français""",
    },
}

LANG_CODES = ["en", "zu", "xh", "st", "tn", "af", "sw", "fr"]

# Coach responses per language
COACH_RESPONSES = {
    "en": {
        "save": "Try the 50/30/20 rule: 50% needs, 30% wants, 20% savings. Even R20/day = R600/month!",
        "scam": "Never share your PIN. MTN will never ask for money. If unsure, hang up and call 135.",
        "budget": "Track every R10 spent. Use SmartMoney categories to see where money goes. Small leaks sink ships!",
        "stokvel": "Stokvels grow wealth together! Start with a trusted group of 5-10 people. Set clear rules.",
        "default": "I'm SmartMoney, your coach! Ask about saving, budgeting, stokvels, or scam safety.",
    },
    "zu": {
        "save": "Sebenzisa umthetho we-50/30/20: 50% izidingo, 30% izifiso, 20% ukulondoloza. Ngisho ne-R20/ngosuku = R600/ngenyanga!",
        "scam": "Ungalokothi wabelane nge-PIN yakho. I-MTN ayisoze ikucele imali. Uma ungaqiniseki, beka ucingo ushayele u-135.",
        "budget": "Landelela yonke i-R10 oyisebenzisayo. Sebenzisa izigaba ze-SmartMoney ukubona ukuthi imali iya kuphi.",
        "stokvel": "Izitokofela zikhulisa ingcebo ndawonye! Qala neqembu elithembekile labantu abangu-5-10.",
        "default": "Ngi-SmartMoney, umqeqeshi wakho! Buza ngokulondoloza, ibhajethi, izitokofela, noma ukuphepha.",
    },
    "sw": {
        "save": "Tumia kanuni ya 50/30/20: 50% mahitaji, 30% matakwa, 20% akiba. Hata R20/siku = R600/mwezi!",
        "scam": "Usishiriki PIN yako kamwe. MTN hawataomba pesa. Ukiwa na shaka, kata simu na piga 135.",
        "budget": "Fuatilia kila R10 unayotumia. Tumia kategoria za SmartMoney kuona pesa inakwenda wapi.",
        "stokvel": "Vikundi vya akiba vinakuza mali pamoja! Anza na kikundi cha kuaminiwa cha watu 5-10.",
        "default": "Mimi ni SmartMoney, kocha wako! Uliza kuhusu kuokoa, bajeti, vikundi vya akiba, au usalama.",
    },
    "fr": {
        "save": "Essayez la règle 50/30/20: 50% besoins, 30% envies, 20% épargne. Même R20/jour = R600/mois!",
        "scam": "Ne partagez jamais votre PIN. MTN ne demandera jamais d'argent. En cas de doute, raccrochez et appelez le 135.",
        "budget": "Suivez chaque R10 dépensé. Utilisez les catégories SmartMoney pour voir où va l'argent.",
        "stokvel": "Les tontines font croître la richesse ensemble! Commencez avec un groupe de confiance de 5-10 personnes.",
        "default": "Je suis SmartMoney, votre coach! Demandez des conseils sur l'épargne, le budget, les tontines ou la sécurité.",
    },
}


def _get_menu(session: dict, menu_name: str, **kwargs) -> str:
    lang = session.get("lang", "en")
    menus = MENUS.get(lang, MENUS["en"])
    template = menus.get(menu_name, MENUS["en"][menu_name])
    if kwargs:
        return template.format(**kwargs)
    return template


def _get_coach_response(question: str, lang: str = "en") -> str:
    q = question.lower()
    responses = COACH_RESPONSES.get(lang, COACH_RESPONSES["en"])

    if any(w in q for w in ["save", "saving", "londoloz", "okoa", "épargn"]):
        return responses["save"]
    if any(w in q for w in ["scam", "fraud", "khwabanis", "ulaghai", "arnaque"]):
        return responses["scam"]
    if any(w in q for w in ["budget", "spend", "sebenzis", "tumia", "dépens"]):
        return responses["budget"]
    if any(w in q for w in ["stokvel", "group", "tokofela", "kikundi", "tontine"]):
        return responses["stokvel"]
    return responses["default"]


@router.post("/callback", response_class=PlainTextResponse)
async def ussd_callback(
    sessionId: str = Form(...),
    phoneNumber: str = Form(...),
    text: str = Form(""),
    serviceCode: str = Form(...),
):
    """
    Africa's Talking USSD callback handler.
    Multilingual support with language selection.
    Responds with CON (continue) or END (terminate) prefixed text.
    """
    parts = text.split("*") if text else []
    level = len(parts)

    # Initialize session
    if sessionId not in sessions:
        sessions[sessionId] = {"phone": phoneNumber, "level": 0, "lang": "en"}

    session = sessions[sessionId]

    # Main menu
    if text == "":
        return _get_menu(session, "main")

    # Level 1 selections
    if level == 1:
        choice = parts[0]

        if choice == "1":
            return _get_menu(session, "spending", income="4,500", expenses="3,200", net="1,300")
        elif choice == "2":
            lang = session.get("lang", "en")
            prompts = {
                "en": "CON Enter recipient's phone number:",
                "zu": "CON Faka inombolo yocingo yomamukeli:",
                "xh": "CON Faka inombolo yefowuni yomamkeli:",
                "sw": "CON Weka nambari ya simu ya mpokeaji:",
                "fr": "CON Entrez le numéro du destinataire:",
            }
            return prompts.get(lang, prompts["en"])
        elif choice == "3":
            return _get_menu(session, "stokvel")
        elif choice == "4":
            return _get_menu(session, "savings", savings="850", target="5,000", progress="17")
        elif choice == "5":
            lang = session.get("lang", "en")
            prompts = {
                "en": "CON Ask SmartMoney anything:\n(Type your question)",
                "zu": "CON Buza i-SmartMoney noma yini:\n(Bhala umbuzo wakho)",
                "xh": "CON Buza i-SmartMoney nantoni na:\n(Bhala umbuzo wakho)",
                "sw": "CON Uliza SmartMoney chochote:\n(Andika swali lako)",
                "fr": "CON Demandez à SmartMoney:\n(Tapez votre question)",
            }
            return prompts.get(lang, prompts["en"])
        elif choice == "6":
            lang = session.get("lang", "en")
            prompts = {
                "en": "CON Report a scam number:\nEnter the suspicious phone number:",
                "zu": "CON Bika inombolo yokukhwabanisa:\nFaka inombolo esola ukuthi iyinkwabaniso:",
                "xh": "CON Xela inombolo yobuqhophololo:\nFaka inombolo efunekayo:",
                "sw": "CON Ripoti nambari ya ulaghai:\nWeka nambari ya simu inayoshukiwa:",
                "fr": "CON Signaler un numéro frauduleux:\nEntrez le numéro suspect:",
            }
            return prompts.get(lang, prompts["en"])
        elif choice == "7":
            return _get_menu(session, "language")

    # Level 2: Sub-menu actions
    if level == 2:
        main_choice = parts[0]

        if main_choice == "2":
            return "CON Enter amount to send (in Rands):"

        elif main_choice == "3":
            sub = parts[1]
            if sub == "1":
                return "END Your stokvels:\n1. Kasi Savings Club - R200/month\n   Next contribution: 1st March"
            elif sub == "2":
                return "CON Enter stokvel contribution amount:"
            elif sub == "3":
                return "END Next payout:\nKasi Savings Club\nDate: 15 April\nAmount: R2,400"

        elif main_choice == "5":
            question = parts[1]
            lang = session.get("lang", "en")
            response = _get_coach_response(question, lang)
            return f"END SmartMoney:\n{response}"

        elif main_choice == "6":
            lang = session.get("lang", "en")
            thanks = {
                "en": f"END Thank you! Number {parts[1]} has been reported. We'll warn other users. Stay safe!",
                "zu": f"END Siyabonga! Inombolo {parts[1]} ibikiwe. Sizoxwayisa abanye abasebenzisi. Hlala uphephile!",
                "xh": f"END Enkosi! Inombolo {parts[1]} ixeliwe. Siya kulumkisa abanye abasebenzisi. Hlala ukhuselekile!",
                "sw": f"END Asante! Nambari {parts[1]} imeripotiwa. Tutawaarifu watumiaji wengine. Kaa salama!",
                "fr": f"END Merci! Le numéro {parts[1]} a été signalé. Nous avertirons les autres utilisateurs. Restez prudent!",
            }
            return thanks.get(lang, thanks["en"])

        elif main_choice == "7":
            # Language selection
            lang_choice = parts[1]
            if lang_choice.isdigit() and 1 <= int(lang_choice) <= len(LANG_CODES):
                session["lang"] = LANG_CODES[int(lang_choice) - 1]
            return _get_menu(session, "main")

    # Level 3: Confirm transactions
    if level == 3:
        main_choice = parts[0]
        if main_choice == "2":
            phone = parts[1]
            amount = parts[2]
            return f"CON Send R{amount} to {phone}?\nScam Check: LOW RISK\n\n1. Confirm\n2. Cancel"

    # Level 4: Final confirmation
    if level == 4:
        if parts[0] == "2" and parts[3] == "1":
            return "END Money sent successfully! Transaction reference: TXN-2024-001"
        else:
            return "END Transaction cancelled."

    # Fallback
    return "END Thank you for using SmartMoney AI. Dial *141*8# to return."
