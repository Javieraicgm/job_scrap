import json
import logging
from typing import List, Dict, Any
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class AngloAmericanScraper(BaseScraper):
    """Scraper para ofertas laborales de Anglo American usando la API de SmartRecruiters"""
    
    def __init__(self):
        super().__init__("anglo_american")
        self.api_url = "https://api.smartrecruiters.com/v1/companies/AngloAmericanDeBeersGroup/postings"
        
    def _extract_jobs(self) -> List[Dict[str, Any]]:
        """Extrae trabajos llamando a la API JSON pública de SmartRecruiters"""
        jobs = []
        try:
            # Añadimos q=Chile para filtrar inicialmente, o extraemos todo y filtramos
            params = {
                "limit": 100,
            }
            logger.info(f"[{self.source_id}] Obteniendo trabajos desde API SmartRecruiters...")
            response = requests.get(self.api_url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            postings = data.get("content", [])
            logger.info(f"[{self.source_id}] Encontrados {len(postings)} trabajos en total (global)")
            
            for posting in postings:
                # Filtrar solo trabajos en Chile
                location = posting.get("location", {})
                country = location.get("country", "").lower()
                city = location.get("city", "")
                
                # Anglo American a veces lista "Chile" o usa regiones específicas
                if "cl" == country or "chile" in country or "santiago" in city.lower():
                    # Parsear fecha
                    # Formato: "2024-05-24T06:21:00.000Z"
                    posted_date = posting.get("releasedDate", "")
                    try:
                        if posted_date:
                            dt = datetime.strptime(posted_date[:10], "%Y-%m-%d")
                            published_at = dt.strftime("%Y-%m-%d")
                        else:
                            published_at = datetime.now().strftime("%Y-%m-%d")
                    except Exception:
                        published_at = datetime.now().strftime("%Y-%m-%d")
                    
                    # Generar ID único
                    job_id = posting.get("id", "")
                    unique_id = self.generate_id(f"{job_id}_{posting.get('name', '')}")
                    
                    # Construir URL de postulación
                    # La url que da el endpoint es api (ref), la url real es la página de SmartRecruiters
                    job_url = f"https://jobs.smartrecruiters.com/AngloAmericanDeBeersGroup/{job_id}"
                    
                    job = {
                        "id": unique_id,
                        "title": posting.get("name", "").strip(),
                        "company": "Anglo American",
                        "location": f"{city}, Chile" if city else "Chile",
                        "url": job_url,
                        "description": "", # La descripcion detallada requiere otro endpoint, pero no la necesitamos para el listado básico
                        "published_at": published_at,
                        "source": self.source_id,
                        "scraped_at": datetime.now().isoformat()
                    }
                    jobs.append(job)
                    
            logger.info(f"[{self.source_id}] Encontrados {len(jobs)} trabajos en Chile")
            return jobs
            
        except Exception as e:
            logger.error(f"[{self.source_id}] Error en el scraper de Anglo American: {e}")
            return []
