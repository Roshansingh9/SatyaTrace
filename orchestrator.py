import google.generativeai as genai
import os
import logging
import requests
import json
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import faiss
import pickle
from datetime import datetime
import re

load_dotenv()
logger = logging.getLogger(__name__)

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-pro')

# Load sentence transformer model
try:
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    logger.info("Sentence transformer model loaded successfully")
except Exception as e:
    logger.error(f"Error loading sentence transformer: {str(e)}")
    embedder = None

# Load FAISS index and knowledge base
try:
    faiss_index = faiss.read_index("faiss_index.bin")
    with open("knowledge_base.pkl", "rb") as f:
        knowledge_base = pickle.load(f)
    logger.info("FAISS index and knowledge base loaded successfully")
except Exception as e:
    logger.warning(f"Could not load FAISS index: {str(e)}. Will work without knowledge base.")
    faiss_index = None
    knowledge_base = []

def extract_claims(text: str) -> list:
    """Extract verifiable claims from the text using Gemini."""
    try:
        prompt = f"""
Extract the main verifiable claims from this text. Focus on factual statements that can be fact-checked.
Return ONLY a numbered list of claims, nothing else:

Text: "{text}"

Claims:
"""
        
        response = model.generate_content(prompt)
        claims_text = response.text.strip()
        
        # Parse the numbered list
        claims = []
        for line in claims_text.split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                # Remove numbering and clean up
                claim = re.sub(r'^\d+\.\s*', '', line)
                claim = re.sub(r'^-\s*', '', claim)
                claims.append(claim.strip())
        
        logger.info(f"Extracted {len(claims)} claims")
        return claims
        
    except Exception as e:
        logger.error(f"Error extracting claims: {str(e)}")
        return [text]  # Return original text as single claim

def retrieve_relevant_context(claims: list) -> list:
    """Retrieve relevant context from knowledge base using FAISS."""
    if not embedder or not faiss_index or not knowledge_base:
        logger.warning("Knowledge base not available")
        return []
    
    try:
        all_context = []
        for claim in claims:
            # Generate embedding for the claim
            claim_embedding = embedder.encode([claim])
            
            # Search in FAISS index
            k = min(3, len(knowledge_base))  # Get top 3 matches
            distances, indices = faiss_index.search(claim_embedding, k)
            
            # Retrieve matching contexts
            for idx in indices[0]:
                if idx < len(knowledge_base):
                    all_context.append(knowledge_base[idx])
        
        logger.info(f"Retrieved {len(all_context)} relevant contexts")
        return all_context
        
    except Exception as e:
        logger.error(f"Error retrieving context: {str(e)}")
        return []

def search_claim_origin(claim: str) -> dict:
    """Search for the earliest mention of a claim online using SerpApi."""
    try:
        serpapi_key = os.getenv("SERPAPI_KEY")
        if not serpapi_key:
            logger.warning("SerpApi key not found")
            return {"first_seen": "Unknown", "spread_info": "Unable to trace origin"}
        
        # Search for the claim
        params = {
            "engine": "google",
            "q": f'"{claim[:100]}"',  # Limit query length
            "api_key": serpapi_key,
            "num": 10,
            "sort": "date"
        }
        
        response = requests.get("https://serpapi.com/search", params=params)
        if response.status_code == 200:
            results = response.json()
            
            # Analyze results for origin
            if "organic_results" in results:
                dates = []
                sources = []
                
                for result in results["organic_results"]:
                    # Extract date if available
                    if "date" in result:
                        dates.append(result["date"])
                    
                    # Extract source domain
                    if "link" in result:
                        domain = result["link"].split("//")[-1].split("/")[0]
                        sources.append(domain)
                
                # Determine earliest date
                first_seen = "Recently" if not dates else min(dates)
                
                # Analyze spread pattern
                unique_sources = list(set(sources[:5]))
                if len(unique_sources) > 3:
                    spread_pattern = "Widely shared across multiple platforms"
                elif len(unique_sources) > 1:
                    spread_pattern = "Shared on a few platforms"
                else:
                    spread_pattern = "Limited sharing detected"
                
                return {
                    "first_seen": first_seen,
                    "spread_info": spread_pattern
                }
        
        return {"first_seen": "Unknown", "spread_info": "Unable to trace spread pattern"}
        
    except Exception as e:
        logger.error(f"Error searching claim origin: {str(e)}")
        return {"first_seen": "Unknown", "spread_info": "Search unavailable"}

def synthesize_response(claims: list, context: list, forensics: dict, original_text: str) -> str:
    """Synthesize the final structured response using Gemini."""
    try:
        context_text = "\n".join(context[:3]) if context else "No specific fact-check data available"
        claims_text = "\n".join([f"- {claim}" for claim in claims])
        
        prompt = f"""
You are SatyaTrace, a fact-checking assistant. Analyze the following information and provide a structured response.

ORIGINAL MESSAGE: "{original_text}"

KEY CLAIMS:
{claims_text}

RELEVANT FACT-CHECK CONTEXT:
{context_text}

FORENSICS DATA:
- First seen: {forensics.get('first_seen', 'Unknown')}
- Spread pattern: {forensics.get('spread_info', 'Unknown')}

Create a response with this EXACT structure:

[RISK LEVEL EMOJI] [RISK LEVEL]

**The Gist:** [One sentence summary of the claim's accuracy]

**Why?**
• [Reason 1]
• [Reason 2]
• [Reason 3 if needed]

**🔍 Trace Report:**
📅 First Seen: {forensics.get('first_seen', 'Unknown')}
📊 How it's Spreading: {forensics.get('spread_info', 'Unknown')}

**Action:** [Simple recommendation like "Don't forward this" or "This appears reliable"]

RISK LEVELS:
- 🔴 HIGH RISK: False, misleading, or harmful information
- 🟡 MEDIUM RISK: Partially true, needs context, or unverified
- 🟢 LOW RISK: Appears accurate and from reliable sources

Keep the response concise and clear.
"""
        
        response = model.generate_content(prompt)
        result = response.text.strip()
        
        logger.info("Response synthesized successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error synthesizing response: {str(e)}")
        return "🟡 MEDIUM RISK\n\n**The Gist:** Unable to fully verify this information.\n\n**Why?**\n• Analysis system temporarily unavailable\n• Recommend checking with trusted sources\n\n**Action:** Verify before sharing"

def run_analysis(text_in_english: str) -> str:
    """Main analysis function that orchestrates all steps."""
    try:
        logger.info("Starting analysis")
        
        # Step 1: Extract claims
        claims = extract_claims(text_in_english)
        
        # Step 2: Retrieve relevant context
        context = retrieve_relevant_context(claims)
        
        # Step 3: Perform forensics (use first claim for search)
        primary_claim = claims[0] if claims else text_in_english
        forensics = search_claim_origin(primary_claim)
        
        # Step 4: Synthesize response
        result = synthesize_response(claims, context, forensics, text_in_english)
        
        logger.info("Analysis completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error in analysis: {str(e)}")
        return "🟡 MEDIUM RISK\n\n**The Gist:** Unable to analyze this message due to technical issues.\n\n**Why?**\n• System temporarily unavailable\n• Recommend manual verification\n\n**Action:** Check with trusted sources before sharing"