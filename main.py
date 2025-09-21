from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
import os
from dotenv import load_dotenv
import logging
from translator import detect_language, translate_to_english, translate_from_english
from orchestrator import run_analysis
from responder import send_message
import asyncio

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SatyaTrace WhatsApp Bot")

# Health check endpoint
@app.get("/")
async def health_check():
    return {"status": "SatyaTrace is running!", "version": "1.0.0"}

@app.post("/api/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    try:
        # Parse the incoming request from Twilio
        form_data = await request.form()
        
        # Extract relevant data
        from_number = form_data.get("From", "").replace("whatsapp:", "")
        message_body = form_data.get("Body", "").strip()
        
        logger.info(f"Received message from {from_number}: {message_body}")
        
        # Validate required fields
        if not from_number or not message_body:
            logger.warning("Missing required fields in webhook")
            return PlainTextResponse("OK", status_code=200)
        
        # Send immediate acknowledgment
        acknowledgment = "नमस्ते! I'm analyzing this for you. This might take a moment... 🧐"
        send_message(from_number, acknowledgment)
        
        # Process the message asynchronously
        asyncio.create_task(process_message_async(from_number, message_body))
        
        return PlainTextResponse("OK", status_code=200)
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return PlainTextResponse("OK", status_code=200)  # Always return OK to Twilio

async def process_message_async(from_number: str, message_body: str):
    """Process the message analysis asynchronously"""
    try:
        # Step 1: Detect language
        detected_language = detect_language(message_body)
        logger.info(f"Detected language: {detected_language}")
        
        # Step 2: Translate to English if needed
        english_text = message_body
        if detected_language != 'en':
            english_text = translate_to_english(message_body, detected_language)
            logger.info(f"Translated to English: {english_text}")
        
        # Step 3: Run analysis (in English)
        analysis_result = run_analysis(english_text)
        logger.info("Analysis completed")
        
        # Step 4: Translate response back if needed
        final_response = analysis_result
        if detected_language != 'en':
            final_response = translate_from_english(analysis_result, detected_language)
            logger.info("Response translated back to original language")
        
        # Step 5: Send the final response
        send_message(from_number, final_response)
        logger.info(f"Final response sent to {from_number}")
        
    except Exception as e:
        logger.error(f"Error in async processing: {str(e)}")
        # Send error message to user
        error_msg = "Sorry, I encountered an error while analyzing your message. Please try again later."
        send_message(from_number, error_msg)

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))  # fallback for local dev
    uvicorn.run("main:app", host="0.0.0.0", port=port)
