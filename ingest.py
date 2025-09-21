"""
One-time setup script to create the knowledge base for SatyaTrace.
This script scrapes trusted fact-checking sources and creates a FAISS index.
"""

import requests
from bs4 import BeautifulSoup
import json
import os
from sentence_transformers import SentenceTransformer
import faiss
import pickle
import numpy as np
from urllib.parse import urljoin, urlparse
import time
import logging
from typing import List, Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FactCheckScraper:
    def __init__(self):
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.knowledge_base = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def scrape_snopes_rss(self) -> List[Dict]:
        """Scrape recent fact-checks from Snopes RSS feed."""
        articles = []
        try:
            response = self.session.get("https://www.snopes.com/feed/", timeout=10)
            soup = BeautifulSoup(response.content, 'xml')
            
            items = soup.find_all('item')[:20]  # Get last 20 items
            
            for item in items:
                try:
                    title = item.title.text if item.title else ""
                    description = item.description.text if item.description else ""
                    link = item.link.text if item.link else ""
                    
                    if title and description:
                        articles.append({
                            'title': title.strip(),
                            'content': description.strip(),
                            'source': 'Snopes',
                            'url': link,
                            'type': 'fact_check'
                        })
                except Exception as e:
                    logger.warning(f"Error processing Snopes item: {e}")
                    continue
            
            logger.info(f"Scraped {len(articles)} articles from Snopes")
            return articles
            
        except Exception as e:
            logger.error(f"Error scraping Snopes: {e}")
            return []
    
    def scrape_factcheck_org_rss(self) -> List[Dict]:
        """Scrape recent fact-checks from FactCheck.org RSS feed."""
        articles = []
        try:
            response = self.session.get("https://www.factcheck.org/feed/", timeout=10)
            soup = BeautifulSoup(response.content, 'xml')
            
            items = soup.find_all('item')[:20]  # Get last 20 items
            
            for item in items:
                try:
                    title = item.title.text if item.title else ""
                    description = item.description.text if item.description else ""
                    link = item.link.text if item.link else ""
                    
                    # Clean description (remove HTML tags)
                    if description:
                        desc_soup = BeautifulSoup(description, 'html.parser')
                        description = desc_soup.get_text()
                    
                    if title and description:
                        articles.append({
                            'title': title.strip(),
                            'content': description.strip(),
                            'source': 'FactCheck.org',
                            'url': link,
                            'type': 'fact_check'
                        })
                except Exception as e:
                    logger.warning(f"Error processing FactCheck.org item: {e}")
                    continue
            
            logger.info(f"Scraped {len(articles)} articles from FactCheck.org")
            return articles
            
        except Exception as e:
            logger.error(f"Error scraping FactCheck.org: {e}")
            return []
    
    def add_curated_facts(self) -> List[Dict]:
        """Add some curated fact-check examples for common misinformation."""
        curated_facts = [
            {
                'title': 'COVID-19 Vaccine Safety',
                'content': 'COVID-19 vaccines authorized for use have undergone rigorous testing and continue to be monitored for safety. Serious adverse reactions are rare.',
                'source': 'CDC',
                'url': 'https://www.cdc.gov/coronavirus/2019-ncov/vaccines/safety/safety-of-vaccines.html',
                'type': 'curated_fact'
            },
            {
                'title': '5G and Health Concerns',
                'content': 'There is no scientific evidence that 5G networks cause health problems. 5G uses radio frequencies that are non-ionizing and do not damage DNA.',
                'source': 'WHO',
                'url': 'https://www.who.int/news-room/q-a-detail/radiation-5g-mobile-networks-and-health',
                'type': 'curated_fact'
            },
            {
                'title': 'Climate Change Scientific Consensus',
                'content': 'There is overwhelming scientific consensus that climate change is occurring and is primarily caused by human activities. Over 97% of climate scientists agree on this.',
                'source': 'NASA',
                'url': 'https://climate.nasa.gov/scientific-consensus/',
                'type': 'curated_fact'
            },
            {
                'title': 'Government Scheme Verification',
                'content': 'Always verify government schemes and benefits through official government websites and helplines. Fake schemes often spread through social media.',
                'source': 'Government Advisory',
                'url': 'https://www.india.gov.in',
                'type': 'curated_fact'
            },
            {
                'title': 'WhatsApp Forward Reliability',
                'content': 'Information shared through WhatsApp forwards is often unreliable. Always check the original source before believing or sharing such information.',
                'source': 'Digital Literacy',
                'url': 'https://www.whatsapp.com/safety/',
                'type': 'curated_fact'
            }
        ]
        
        logger.info(f"Added {len(curated_facts)} curated facts")
        return curated_facts
    
    def process_articles(self, articles: List[Dict]) -> List[str]:
        """Process articles and create text chunks for embedding."""
        processed_texts = []
        
        for article in articles:
            # Combine title and content for better context
            full_text = f"{article['title']}\n\n{article['content']}"
            
            # Split long content into chunks
            if len(full_text) > 500:
                # Simple sentence-based chunking
                sentences = full_text.split('. ')
                current_chunk = ""
                
                for sentence in sentences:
                    if len(current_chunk + sentence) < 500:
                        current_chunk += sentence + ". "
                    else:
                        if current_chunk:
                            processed_texts.append(current_chunk.strip())
                        current_chunk = sentence + ". "
                
                if current_chunk:
                    processed_texts.append(current_chunk.strip())
            else:
                processed_texts.append(full_text)
        
        # Store articles in knowledge base
        self.knowledge_base = processed_texts
        
        logger.info(f"Processed {len(processed_texts)} text chunks")
        return processed_texts
    
    def create_faiss_index(self, texts: List[str]):
        """Create FAISS index from processed texts."""
        try:
            # Generate embeddings
            logger.info("Generating embeddings...")
            embeddings = self.embedder.encode(texts, show_progress_bar=True)
            
            # Create FAISS index
            dimension = embeddings.shape[1]
            index = faiss.IndexFlatL2(dimension)
            
            # Add embeddings to index
            index.add(embeddings.astype('float32'))
            
            # Save index
            faiss.write_index(index, "faiss_index.bin")
            logger.info("FAISS index saved to faiss_index.bin")
            
            # Save knowledge base
            with open("knowledge_base.pkl", "wb") as f:
                pickle.dump(self.knowledge_base, f)
            logger.info("Knowledge base saved to knowledge_base.pkl")
            
            return index
            
        except Exception as e:
            logger.error(f"Error creating FAISS index: {e}")
            return None

def main():
    """Main function to run the ingestion process."""
    logger.info("Starting knowledge base ingestion...")
    
    scraper = FactCheckScraper()
    
    # Collect articles from multiple sources
    all_articles = []
    
    # Scrape from RSS feeds
    all_articles.extend(scraper.scrape_snopes_rss())
    time.sleep(2)  # Be polite to servers
    
    all_articles.extend(scraper.scrape_factcheck_org_rss())
    time.sleep(2)
    
    # Add curated facts
    all_articles.extend(scraper.add_curated_facts())
    
    logger.info(f"Total articles collected: {len(all_articles)}")
    
    if not all_articles:
        logger.error("No articles collected. Creating minimal knowledge base...")
        all_articles = scraper.add_curated_facts()
    
    # Process articles
    processed_texts = scraper.process_articles(all_articles)
    
    if processed_texts:
        # Create FAISS index
        index = scraper.create_faiss_index(processed_texts)
        
        if index:
            logger.info("✅ Knowledge base creation completed successfully!")
            logger.info(f"📊 Total text chunks: {len(processed_texts)}")
            logger.info(f"📁 Files created: faiss_index.bin, knowledge_base.pkl")
        else:
            logger.error("❌ Failed to create FAISS index")
    else:
        logger.error("❌ No texts processed")

if __name__ == "__main__":
    main()