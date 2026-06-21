import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import datetime
from .base_scraper import BaseScraper
import re
import time

class ChileTrabajosScraper(BaseScraper):
    """Scraper web para ChileTrabajos"""
    
    def __init__(self):
        super().__init__(
            source_id='chiletrabajos',
            source_name='ChileTrabajos',
            base_url='https://www.chiletrabajos.cl'
        )
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        })
        
    def scrape(self, keywords: List[str] = None) -> List[Dict]:
        if not keywords:
            keywords = ['data scientist', 'analista de datos', 'geofisica']
            
        all_jobs = []
        
        for keyword in keywords:
            print(f"   Buscando '{keyword}' en ChileTrabajos...")
            try:
                # Reemplazamos espacios por +
                kw_formatted = keyword.replace(' ', '+')
                url = f"{self.base_url}/encuentra-un-empleo?2={kw_formatted}"
                
                response = self.session.get(url, timeout=15)
                if response.status_code != 200:
                    print(f"   Error fetching {url}: {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # En ChileTrabajos los trabajos están bajo la clase job-item
                articles = soup.select('.job-item')
                if not articles:
                    print(f"   No se encontraron ofertas para '{keyword}' en la primera página.")
                    continue
                    
                print(f"   Encontradas {len(articles)} ofertas de '{keyword}' en la primera página.")
                
                for article in articles:
                    job_data = self._parse_article(article)
                    if job_data:
                        all_jobs.append(job_data)
                        
                time.sleep(2.0)
                
            except Exception as e:
                print(f"   Error consultando ChileTrabajos para '{keyword}': {e}")
                
        # Deduplicar por URL
        unique_jobs = {job['url']: job for job in all_jobs}.values()
        return list(unique_jobs)
        
    def _parse_article(self, article) -> Dict:
        """Parsea el HTML de una oferta individual de ChileTrabajos"""
        try:
            title_elem = article.select_one('h2.title a')
            if not title_elem:
                return None
                
            title = title_elem.text.strip()
            job_url = title_elem['href']
            
            # La empresa suele estar en un h3 dentro de .meta o el h3 principal del item
            company_elem = article.select_one('.meta h3, h3')
            company_text = company_elem.text.strip() if company_elem else 'Confidencial'
            
            # Normalmente viene "Empresa, Localidad"
            parts = [p.strip() for p in company_text.split(',')]
            company = parts[0]
            location = parts[1] if len(parts) > 1 else 'Chile'
            
            # ID externo
            external_id = job_url.split('-')[-1] if '-' in job_url else str(hash(job_url))
            
            raw_data = {
                'external_id': external_id,
                'title': title,
                'company': company,
                'description': '', # No disponible en listado corto
                'salary_min': None,
                'salary_max': None,
                'location': location,
                'url': job_url,
                'posted_date': datetime.datetime.now().isoformat(),
                'deadline_date': None
            }
            
            return self.normalize_job(raw_data)
            
        except Exception as e:
            print(f"   Error parseando artículo de ChileTrabajos: {e}")
            return None
