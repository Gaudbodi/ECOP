"""SMS 2FA delivery service.

Primary: Africa's Talking (recommended by PRD §5 for Ghana coverage; sandbox
available for tests). Fallback: Twilio (existing dependency, kept as adapter).
Final fallback: log-only — preserves the graceful-degradation invariant so the
app boots and logs verification codes when no SMS provider is configured.
"""
import logging
import os

logger = logging.getLogger(__name__)

AT_USERNAME = os.environ.get("AFRICASTALKING_USERNAME")
AT_API_KEY = os.environ.get("AFRICASTALKING_API_KEY")
AT_FROM = os.environ.get("AFRICASTALKING_FROM")  # short code or sender ID; optional

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.environ.get("TWILIO_FROM_NUMBER")


class SMS2FAService:
    """SMS verification-code delivery with provider fallback.

    Provider priority on send_code():
        1. Africa's Talking (if AFRICASTALKING_USERNAME + AFRICASTALKING_API_KEY set)
        2. Twilio (if TWILIO_ACCOUNT_SID + TWILIO_AUTH_TOKEN + TWILIO_FROM_NUMBER set)
        3. Log-only (graceful degradation)

    Returns ``True`` if a delivery attempt succeeded with any provider OR the
    log-only path ran (consistent with the existing email_service pattern that
    returns True for "simulated success" so the login flow proceeds in dev).
    Callers should NOT rely on True implying real SMS delivery.
    """

    def __init__(self):
        self.at_client = None
        self.twilio_client = None
        self._init_at()
        self._init_twilio()

    def _init_at(self):
        if not (AT_USERNAME and AT_API_KEY):
            logger.info("Africa's Talking credentials not set. SMS 2FA via AT disabled.")
            return
        try:
            import africastalking
            africastalking.initialize(AT_USERNAME, AT_API_KEY)
            self.at_client = africastalking.SMS
            logger.info("Africa's Talking SMS client initialised (username=%s).", AT_USERNAME)
        except ImportError:
            logger.warning("africastalking package not installed; AT SMS disabled. Run pip install -r requirements.txt.")
        except Exception as e:
            logger.warning("Africa's Talking init failed: %s. AT SMS disabled.", e)

    def _init_twilio(self):
        if not (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_FROM_NUMBER):
            logger.info("Twilio credentials incomplete. SMS 2FA via Twilio disabled.")
            return
        try:
            from twilio.rest import Client
            self.twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            logger.info("Twilio client initialised as SMS 2FA fallback.")
        except Exception as e:
            logger.warning("Twilio init failed: %s. Twilio SMS fallback disabled.", e)

    def send_code(self, phone_number: str, code: str) -> bool:
        """Send a verification code to ``phone_number``. Returns True on
        attempted delivery (real or logged)."""
        if not phone_number:
            logger.warning("send_code called with empty phone_number; falling through to log-only.")
            return self._log_only(phone_number, code)

        body = f"Ghana CAP verification code: {code}\n(expires in 10 minutes — do not share)"

        if self.at_client:
            try:
                resp = self.at_client.send(body, [phone_number], sender_id=AT_FROM)
                logger.info("AT SMS sent to %s. Response: %s", phone_number, resp)
                return True
            except Exception as e:
                logger.warning("AT SMS send failed: %s. Trying Twilio fallback.", e)

        if self.twilio_client:
            try:
                msg = self.twilio_client.messages.create(
                    body=body, from_=TWILIO_FROM_NUMBER, to=phone_number
                )
                logger.info("Twilio SMS sent to %s. SID: %s", phone_number, msg.sid)
                return True
            except Exception as e:
                logger.warning("Twilio SMS send failed: %s. Falling back to log-only.", e)

        return self._log_only(phone_number, code)

    @staticmethod
    def _log_only(phone_number: str, code: str) -> bool:
        logger.warning(
            "SMS 2FA: no provider available. Code for %s is %s (DEV ONLY — configure AT/Twilio for real delivery).",
            phone_number or "<no phone>", code,
        )
        return True


# Singleton (matches the pattern across the rest of services/)
sms_2fa_service = SMS2FAService()
