from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import User
from app.routers.auth import get_current_user
from app.services.ai_coach import get_coaching_response

router = APIRouter()

# Multilingual IVR messages
IVR_MESSAGES = {
    "en": {
        "welcome": (
            "Welcome to SmartMoney. "
            "Press 1 for spending summary. "
            "Press 2 for savings update. "
            "Press 3 for scam alert. "
            "Press 4 to speak to your AI coach. "
            "Press 9 to change language."
        ),
        "spending": (
            "Your spending summary. "
            "This month you received 4500 rand and spent 3200 rand. "
            "Your biggest spending was airtime at 800 rand. "
            "Press 0 to go back."
        ),
        "savings": (
            "Your savings update. "
            "You have saved 850 rand towards your goal of 5000 rand. "
            "That's 17 percent progress. Keep it up! "
            "Press 0 to go back."
        ),
        "scam": (
            "Scam alert. "
            "You have no flagged transactions this week. Stay safe! "
            "Remember, never share your PIN with anyone. "
            "Press 0 to go back."
        ),
        "coach": "Please say your question after the beep.",
        "goodbye": "Thank you for using SmartMoney. Goodbye.",
        "language": (
            "Press 1 for English. "
            "Press 2 for isiZulu. "
            "Press 3 for Kiswahili. "
            "Press 4 for Français."
        ),
    },
    "zu": {
        "welcome": (
            "Siyakwamukela ku-SmartMoney. "
            "Cindezela u-1 ukuthola isifinyezo sokusebenzisa. "
            "Cindezela u-2 ukuthola isibuyekezo sokulondoloza. "
            "Cindezela u-3 ukuthola isexwayiso sokukhwabanisa. "
            "Cindezela u-4 ukukhuluma nomqeqeshi wakho we-AI. "
            "Cindezela u-9 ukushintsha ulimi."
        ),
        "spending": (
            "Isifinyezo sokusebenzisa kwakho. "
            "Kulenyanga uthole ama-rand angu-4500 wasebenzisa ama-rand angu-3200. "
            "Okusebenzise kakhulu yi-airtime ngama-rand angu-800. "
            "Cindezela u-0 ukubuyela emuva."
        ),
        "savings": (
            "Isibuyekezo sokulondoloza kwakho. "
            "Ulondoloze ama-rand angu-850 ngomgomo wakho wama-rand angu-5000. "
            "Lokho kuphumelela okungama-phesenti angu-17. Qhubeka! "
            "Cindezela u-0 ukubuyela emuva."
        ),
        "scam": (
            "Isexwayiso sokukhwabanisa. "
            "Awunayo ukuthengiselana okuflegiwe kuleli viki. Hlala uphephile! "
            "Khumbula, ungayabelani nge-PIN yakho nanoma ubani. "
            "Cindezela u-0 ukubuyela emuva."
        ),
        "coach": "Sicela usho umbuzo wakho ngemva komsindo.",
        "goodbye": "Siyabonga ngokusebenzisa i-SmartMoney. Sala kahle.",
        "language": (
            "Cindezela u-1 nge-English. "
            "Cindezela u-2 ngesiZulu. "
            "Cindezela u-3 nge-Kiswahili. "
            "Cindezela u-4 nge-Français."
        ),
    },
    "sw": {
        "welcome": (
            "Karibu SmartMoney. "
            "Bonyeza 1 kwa muhtasari wa matumizi. "
            "Bonyeza 2 kwa habari za akiba. "
            "Bonyeza 3 kwa tahadhari ya ulaghai. "
            "Bonyeza 4 kuzungumza na kocha wako wa AI. "
            "Bonyeza 9 kubadilisha lugha."
        ),
        "spending": (
            "Muhtasari wako wa matumizi. "
            "Mwezi huu umepokea randi 4500 na kutumia randi 3200. "
            "Matumizi yako makubwa yalikuwa muda wa maongezi kwa randi 800. "
            "Bonyeza 0 kurudi."
        ),
        "savings": (
            "Habari za akiba yako. "
            "Umehifadhi randi 850 kuelekea lengo lako la randi 5000. "
            "Hiyo ni asilimia 17 ya maendeleo. Endelea hivyo! "
            "Bonyeza 0 kurudi."
        ),
        "scam": (
            "Tahadhari ya ulaghai. "
            "Huna miamala iliyotiwa alama wiki hii. Kaa salama! "
            "Kumbuka, usishiriki PIN yako na mtu yeyote. "
            "Bonyeza 0 kurudi."
        ),
        "coach": "Tafadhali sema swali lako baada ya sauti.",
        "goodbye": "Asante kwa kutumia SmartMoney. Kwaheri.",
        "language": (
            "Bonyeza 1 kwa English. "
            "Bonyeza 2 kwa isiZulu. "
            "Bonyeza 3 kwa Kiswahili. "
            "Bonyeza 4 kwa Français."
        ),
    },
    "fr": {
        "welcome": (
            "Bienvenue sur SmartMoney. "
            "Appuyez sur 1 pour le résumé des dépenses. "
            "Appuyez sur 2 pour la mise à jour de l'épargne. "
            "Appuyez sur 3 pour l'alerte arnaque. "
            "Appuyez sur 4 pour parler à votre coach IA. "
            "Appuyez sur 9 pour changer la langue."
        ),
        "spending": (
            "Votre résumé des dépenses. "
            "Ce mois-ci vous avez reçu 4500 rands et dépensé 3200 rands. "
            "Votre plus grosse dépense était le crédit téléphone à 800 rands. "
            "Appuyez sur 0 pour revenir."
        ),
        "savings": (
            "Mise à jour de votre épargne. "
            "Vous avez épargné 850 rands sur votre objectif de 5000 rands. "
            "C'est 17 pour cent de progrès. Continuez! "
            "Appuyez sur 0 pour revenir."
        ),
        "scam": (
            "Alerte arnaque. "
            "Vous n'avez aucune transaction signalée cette semaine. Restez prudent! "
            "N'oubliez pas, ne partagez jamais votre PIN avec personne. "
            "Appuyez sur 0 pour revenir."
        ),
        "coach": "Veuillez poser votre question après le bip.",
        "goodbye": "Merci d'utiliser SmartMoney. Au revoir.",
        "language": (
            "Appuyez sur 1 pour English. "
            "Appuyez sur 2 pour isiZulu. "
            "Appuyez sur 3 pour Kiswahili. "
            "Appuyez sur 4 pour Français."
        ),
    },
}

# IVR session store
ivr_sessions: dict[str, dict] = {}
LANG_OPTIONS = ["en", "zu", "sw", "fr"]


@router.post("/transcribe")
async def voice_interaction(
    audio: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Receives voice audio, transcribes it, processes with AI coach,
    and returns text response (TTS handled client-side or by gateway).
    Supports multilingual responses.
    """
    audio_content = await audio.read()
    transcribed_text = await _transcribe_audio(audio_content)

    if not transcribed_text:
        return JSONResponse(content={
            "text_response": "I couldn't hear that clearly. Please try again.",
            "transcription": "",
            "success": False,
        })

    response = await get_coaching_response(transcribed_text, user, db)

    return {
        "transcription": transcribed_text,
        "text_response": response.response,
        "suggestions": response.suggestions,
        "success": True,
    }


@router.post("/ivr-callback")
async def ivr_callback(
    caller_number: str = "",
    dtmf_digits: str = "",
    session_id: str = "",
):
    """
    IVR (Interactive Voice Response) callback for feature phones.
    Integrates with Africa's Talking Voice API.
    Supports multilingual voice menus.
    """
    if session_id not in ivr_sessions:
        ivr_sessions[session_id] = {"lang": "en", "caller": caller_number}

    session = ivr_sessions[session_id]
    lang = session.get("lang", "en")
    messages = IVR_MESSAGES.get(lang, IVR_MESSAGES["en"])

    if not dtmf_digits:
        return _voice_response(messages["welcome"])

    if dtmf_digits == "1":
        return _voice_response(messages["spending"])
    elif dtmf_digits == "2":
        return _voice_response(messages["savings"])
    elif dtmf_digits == "3":
        return _voice_response(messages["scam"])
    elif dtmf_digits == "4":
        return _voice_response(messages["coach"], gather_speech=True)
    elif dtmf_digits == "9":
        return _voice_response(messages["language"])
    elif dtmf_digits in ["91", "92", "93", "94"]:
        lang_idx = int(dtmf_digits[1]) - 1
        if 0 <= lang_idx < len(LANG_OPTIONS):
            session["lang"] = LANG_OPTIONS[lang_idx]
        new_messages = IVR_MESSAGES.get(session["lang"], IVR_MESSAGES["en"])
        return _voice_response(new_messages["welcome"])
    elif dtmf_digits == "0":
        return _voice_response(messages["welcome"])

    return _voice_response(messages["goodbye"], end_call=True)


def _voice_response(text: str, gather_speech: bool = False, end_call: bool = False) -> dict:
    return {
        "text": text,
        "gather_speech": gather_speech,
        "end_call": end_call,
    }


async def _transcribe_audio(audio_content: bytes) -> str:
    """Placeholder for STT integration. Replace with actual service."""
    # In production: send to OpenAI Whisper, Google STT, or Azure STT
    # Supports multilingual transcription
    return ""
