from fastapi import APIRouter
from backend.app.schemas import ChatMessage, ChatResponse

router = APIRouter(prefix="/chatbot", tags=["AI Safety Chatbot (English & Kannada)"])

EMERGENCY_NUMBERS = {
    "All India Emergency Helpline": "112",
    "Women Helpline (Domestic Abuse & Harassment)": "1091",
    "National Commission for Women (NCW)": "7827170170",
    "Women in Distress Helpline": "181",
    "Karnataka State Police Helpline": "100 / 112",
    "Anti-Eve Teasing Squad (Bengaluru)": "1090",
    "Ambulance Services": "108"
}

RESPONSES_EN = {
    "help": "If you are in immediate danger, tap the RED SOS BUTTON on the top header or dial 112 right now! Keep your phone on loud and walk towards a crowded store or petrol station.",
    "stalk": "If someone is following you: 1) Cross the street or enter an open commercial store/cafe immediately. 2) Call a family member or pretend to talk loudly on phone. 3) Trigger Silent SOS in this app so verified nearby community helpers are notified with your live coordinates. 4) Dial 112.",
    "cab": "Safe transit advice: Before boarding, share the cab license plate and live GPS route with your trusted contacts. Verify the child lock is deactivated and ensure the driver follows the mapped safe route.",
    "hotspot": "You can inspect the Crime Hotspot map tab in this app. Red zones indicate poorly lit areas or previously reported incidents. Select the 'Safe Route' feature to bypass them.",
    "kannada": "ನೀವು ಕನ್ನಡದಲ್ಲಿ ಸಹಾಯ ಪಡೆಯಲು ಭಾಷೆಯನ್ನು 'kn' ಗೆ ಬದಲಾಯಿಸಬಹುದು ಅಥವಾ 'ಸಹಾಯ' ಎಂದು ಟೈಪ್ ಮಾಡಬಹುದು.",
    "default": "I am your AI Women Safety Assistant. I can advise you on: 1) Immediate emergency protocols (SOS), 2) Safe route selection, 3) How to handle suspicious followers, 4) Connecting to verified neighbourhood helpers. In critical danger, please press the SOS button immediately!"
}

RESPONSES_KN = {
    "help": "ನೀವು ತಕ್ಷಣದ ಅಪಾಯದಲ್ಲಿದ್ದರೆ, ದಯವಿಟ್ಟು ಕೆಂಪು SOS ಬಟನ್ ಒತ್ತಿರಿ ಅಥವಾ ತಕ್ಷಣ 112 ಗೆ ಕರೆ ಮಾಡಿ! ಧೈರ್ಯವಾಗಿರಿ, ಹತ್ತಿರದ ಜನನಿಬಿಡ ಅಂಗಡಿ ಅಥವಾ ಪೆಟ್ರೋಲ್ ಬಂಕ್ ಕಡೆಗೆ ನಡೆಯಿರಿ.",
    "stalk": "ಯಾರಾದರೂ ನಿಮ್ಮನ್ನು ಹಿಂಬಾಲಿಸುತ್ತಿದ್ದರೆ: 1) ತಕ್ಷಣ ರಸ್ತೆ ದಾಟಿ ತೆರೆದಿರುವ ಅಂಗಡಿ ಅಥವಾ ಹೋಟೆಲ್ ಪ್ರವೇಶಿಸಿ. 2) ನಿಮ್ಮ ಕುಟುಂಬದವರಿಗೆ ಕರೆ ಮಾಡಿ ಅಥವಾ ಫೋನ್‌ನಲ್ಲಿ ಜೋರಾಗಿ ಮಾತನಾಡಿ. 3) ಈ ಆ್ಯಪ್‌ನಲ್ಲಿ ಸೈಲೆಂಟ್ SOS ಆನ್ ಮಾಡಿ - ಹತ್ತಿರದ ಸ್ವಯಂಸೇವಕರಿಗೆ ನಿಮ್ಮ ಲೈವ್ ಲೊಕೇಶನ್ ಸಿಗುತ್ತದೆ. 4) 112 ಗೆ ಕರೆ ಮಾಡಿ.",
    "cab": "ಕ್ಯಾಬ್ ಸುರಕ್ಷತೆ: ಹತ್ತುವ ಮುನ್ನ ವಾಹನದ ನಂಬರ್ ಮತ್ತು ಲೈವ್ ಜಿಪಿಎಸ್ ಅನ್ನು ನಿಮ್ಮ ಕುಟುಂಬದವರಿಗೆ ಹಂಚಿಕೊಳ್ಳಿ. ಚಾಲಕ ಸುರಕ್ಷಿತ ಮಾರ್ಗದಲ್ಲೇ ಹೋಗುತ್ತಿದ್ದಾನೆಯೇ ಎಂದು ಗಮನಿಸಿ.",
    "hotspot": "ಈ ಆ್ಯಪ್‌ನಲ್ಲಿ 'ಹಾಟ್‌ಸ್ಪಾಟ್ ಮ್ಯಾಪ್' ನೋಡಿ. ಕೆಂಪು ವಲಯಗಳು ಬೆಳಕಿಲ್ಲದ ಅಥವಾ ಸಂಶಯಾಸ್ಪದ ಪ್ರದೇಶಗಳಾಗಿವೆ. ಸುರಕ್ಷಿತ ಮಾರ್ಗ (Safe Route) ಬಳಸಿ.",
    "default": "ನಾನು ನಿಮ್ಮ ಸ್ಮಾರ್ಟ್ ಮಹಿಳಾ ಸುರಕ್ಷತಾ ಸಹಾಯಕ. ತುರ್ತು ಸಂದರ್ಭದಲ್ಲಿ ಏನು ಮಾಡಬೇಕು, ಸುರಕ್ಷಿತ ಮಾರ್ಗಗಳು ಮತ್ತು ಪೊಲೀಸ್ ಸಹಾಯವಾಣಿ (112, 1091) ಬಗ್ಗೆ ನಾನು ನಿಮಗೆ ಮಾರ್ಗದರ್ಶನ ನೀಡಬಲ್ಲೆ. ತಕ್ಷಣದ ಅಪಾಯವಿದ್ದರೆ ಕೆಂಪು SOS ಬಟನ್ ಒತ್ತಿ!"
}

@router.post("/query", response_model=ChatResponse)
def query_chatbot(chat_in: ChatMessage):
    lang = chat_in.language.lower() if chat_in.language else "en"
    msg = chat_in.message.lower().strip()

    if lang.startswith("kn") or any(char in chat_in.message for char in "ಅಆಇಈಉಊಋಎಏಐಒಓಔಕಖಗಘ"):
        lang = "kn"
        if "ಸಹಾಯ" in msg or "ತುರ್ತು" in msg or "help" in msg or "sos" in msg:
            reply = RESPONSES_KN["help"]
        elif "ಹಿಂಬಾಲ" in msg or "ಫಾಲೋ" in msg or "stalk" in msg:
            reply = RESPONSES_KN["stalk"]
        elif "ಕ್ಯಾಬ್" in msg or "ಆಟೋ" in msg or "cab" in msg:
            reply = RESPONSES_KN["cab"]
        elif "ಹಾಟ್‌ಸ್ಪಾಟ್" in msg or "ರಸ್ತೆ" in msg:
            reply = RESPONSES_KN["hotspot"]
        else:
            reply = RESPONSES_KN["default"]

        actions = [
            "ತುರ್ತು SOS ಬಟನ್ ಒತ್ತಿರಿ",
            "112 ಗೆ ಕರೆ ಮಾಡಿ",
            "ಲೈವ್ ಲೊಕೇಶನ್ ಶೇರ್ ಮಾಡಿ",
            "ಹತ್ತಿರದ ಪೊಲೀಸ್ ಠಾಣೆ ನೋಡಿ"
        ]
    else:
        lang = "en"
        if "help" in msg or "emergency" in msg or "sos" in msg or "danger" in msg:
            reply = RESPONSES_EN["help"]
        elif "follow" in msg or "stalk" in msg or "creep" in msg or "chase" in msg:
            reply = RESPONSES_EN["stalk"]
        elif "cab" in msg or "taxi" in msg or "uber" in msg or "auto" in msg:
            reply = RESPONSES_EN["cab"]
        elif "hotspot" in msg or "crime" in msg or "dark" in msg or "unlit" in msg:
            reply = RESPONSES_EN["hotspot"]
        elif "kannada" in msg or "kn" in msg:
            reply = RESPONSES_EN["kannada"]
        else:
            reply = RESPONSES_EN["default"]

        actions = [
            "Trigger One-Tap SOS",
            "Dial 112 (National Emergency)",
            "Share Live GPS Coordinates",
            "Find Nearby Safe Route & Police Station"
        ]

    return ChatResponse(
        response=reply,
        language=lang,
        suggested_actions=actions,
        emergency_numbers=EMERGENCY_NUMBERS
    )
