import requests
import os
import logging
import json
from twilio.rest import Client

# Configuration
# Phase 8: default points at the local public-feed receiver so the dispatch
# loop closes locally for testing without requiring a separate MNO process.
# On Render, fall back to the service's own public URL (RENDER_EXTERNAL_URL) so
# the self-dispatch loop still closes remotely without a manual config step.
# In production, set MNO_WEBHOOK_URL to the real telecom endpoint.
_default_mno_url = "http://localhost:5000/public/feed/receive"
_render_external_url = os.environ.get("RENDER_EXTERNAL_URL", "").strip().rstrip("/")
if _render_external_url:
    _default_mno_url = f"{_render_external_url}/public/feed/receive"
MNO_WEBHOOK_URL = os.environ.get("MNO_WEBHOOK_URL", _default_mno_url)
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.environ.get("TWILIO_FROM_NUMBER", "+1234567890") # Replace with your Twilio number

class DispatchService:
    def __init__(self):
        self.mno_webhook_url = MNO_WEBHOOK_URL
        self.twilio_sid = TWILIO_ACCOUNT_SID
        self.twilio_auth_token = TWILIO_AUTH_TOKEN
        self.twilio_from = TWILIO_FROM_NUMBER
        self.client = None

        # Initialize Twilio client only if both SID and token are available
        if self.twilio_sid and self.twilio_auth_token:
            try:
                self.client = Client(self.twilio_sid, self.twilio_auth_token)
                logging.info("Twilio client initialized successfully.")
            except Exception as e:
                logging.warning(f"Failed to initialize Twilio client: {e}. SMS will be mocked.")
                self.client = None
        else:
            logging.info("Twilio credentials not fully configured. SMS will be mocked.")

    def dispatch_to_mno(self, alert_payload):
        """
        Pushes a structured JSON payload to the MNO webhook endpoint.
        """
        try:
            logging.info(f"Dispatching enriched alert to MNO at {self.mno_webhook_url}")
            response = requests.post(self.mno_webhook_url, json=alert_payload, timeout=5)
            response.raise_for_status()
            logging.info("MNO dispatch successful.")
            return True
        except Exception as e:
            logging.error(f"Failed to dispatch to MNO: {e}")
            return False

    def send_sms(self, text, recipients):
        """
        Sends an SMS to the specified recipients via Twilio.
        """
        if not self.client:
            logging.warning("No Twilio Auth Token found. Mocking SMS send.")
            logging.info(f"Mock Twilio SMS Sent: '{text}' to {recipients}")
            return True

        # Real SMS dispatch via Twilio
        success_count = 0
        for recipient in recipients:
            try:
                message = self.client.messages.create(
                    body=text,
                    from_=self.twilio_from,
                    to=recipient
                )
                logging.info(f"Twilio SMS sent to {recipient}. SID: {message.sid}")
                success_count += 1
            except Exception as e:
                logging.error(f"Twilio SMS failed for {recipient}: {e}")
        
        return success_count > 0

# Singleton instance
dispatch_service = DispatchService()
