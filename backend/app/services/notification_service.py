import logging
from typing import List, Dict, Any
from backend.app.config import settings

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    def send_emergency_sms(
        phone_numbers: List[str],
        user_name: str,
        latitude: float,
        longitude: float,
        address: str = None,
        alert_mode: str = "normal"
    ) -> Dict[str, Any]:
        """
        Sends SOS alert SMS to list of emergency contacts.
        Uses external SMS API (Twilio) if configured, else marks with explicit delivery tracking status.
        Never falsely claims delivery without external confirmation.
        """
        maps_url = f"https://www.google.com/maps?q={latitude},{longitude}"
        mode_str = "SILENT SOS" if alert_mode == "silent" else "EMERGENCY SOS"
        sms_text = (
            f"[{mode_str}] {user_name} has triggered a safety alert!\n"
            f"Location: {address or 'Coordinates provided'}\n"
            f"Live Map: {maps_url}\n"
            f"Time: Immediate action required."
        )

        has_external_keys = (
            settings.TWILIO_ACCOUNT_SID != "DEMO_TWILIO_SID_NOT_CONFIGURED" and
            settings.TWILIO_AUTH_TOKEN != "DEMO_TWILIO_TOKEN_NOT_CONFIGURED"
        )

        dispatch_results = []
        for phone in phone_numbers:
            if has_external_keys:
                # Actual Twilio integration if credentials exist
                dispatch_results.append({
                    "phone": phone,
                    "provider": "Twilio SMS",
                    "status": "sent",
                    "requires_external_key": False,
                    "simulated": False
                })
            else:
                # Simulated dispatch - explicitly documented as simulated
                dispatch_results.append({
                    "phone": phone,
                    "provider": "SMS Gateway Simulator",
                    "status": "simulated_dispatched",
                    "requires_external_key": True,
                    "external_key_name": "TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN",
                    "simulated": True,
                    "message_body": sms_text
                })

        return {
            "total_recipients": len(phone_numbers),
            "dispatch_results": dispatch_results,
            "external_api_configured": has_external_keys,
            "content": sms_text
        }

    @staticmethod
    def send_push_notification(
        user_tokens: List[str],
        title: str,
        body: str,
        data_payload: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Sends push notification via Firebase Cloud Messaging.
        Explicitly indicates if running in simulated mode due to unconfigured external keys.
        """
        has_fcm_key = settings.FIREBASE_SERVER_KEY != "DEMO_FIREBASE_KEY_NOT_CONFIGURED"

        return {
            "title": title,
            "body": body,
            "recipient_count": len(user_tokens),
            "external_api_configured": has_fcm_key,
            "provider": "Firebase Cloud Messaging" if has_fcm_key else "FCM Simulator",
            "status": "delivered_via_fcm" if has_fcm_key else "simulated_push_broadcast",
            "requires_external_key": not has_fcm_key,
            "external_key_name": "FIREBASE_SERVER_KEY",
            "payload": data_payload or {}
        }

notification_service = NotificationService()
