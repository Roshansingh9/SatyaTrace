from twilio.rest import Client
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

def send_message(recipient_number: str, message_body: str):
    """Send a message to the recipient via Twilio WhatsApp API."""
    try:
        # Get Twilio credentials from environment variables
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")  # Twilio sandbox default
        
        if not account_sid or not auth_token:
            logger.error("Twilio credentials not found in environment variables")
            return False
        
        # Initialize Twilio client
        client = Client(account_sid, auth_token)
        
        # Format recipient number
        if not recipient_number.startswith("whatsapp:"):
            recipient_number = f"whatsapp:{recipient_number}"
        
        # Send the message
        message = client.messages.create(
            from_=whatsapp_number,
            body=message_body,
            to=recipient_number
        )
        
        logger.info(f"Message sent successfully. SID: {message.sid}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        return False

def send_acknowledgment(recipient_number: str):
    """Send immediate acknowledgment message."""
    acknowledgment = "नमस्ते! I'm analyzing this for you. This might take a moment... 🧐"
    return send_message(recipient_number, acknowledgment)

def send_error_message(recipient_number: str):
    """Send error message when analysis fails."""
    error_msg = "Sorry, I encountered an error while analyzing your message. Please try again later."
    return send_message(recipient_number, error_msg)