import requests
import datetime
from typing import List, Dict
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper

class GetOnBoardScraper(BaseScraper):
    """Scraper para GetOnBoard usando su API pública"""
    
    def __init__(self):
        super().__init__(
            source_id='getonboard',
            source_name='GetOnBoard',
            base_url='https://www.getonbrd.com'
        )
        self.api_url = 'https://www.getonbrd.com/api/v0/search/jobs'
        
    def scrape(self, keywords: List[str] = None) -> List[Dict]:
        """Extrae ofertas usando la API de GetOnBoard"""
        
        if not keywords:
            # Por defecto buscamos 'data' que engloba data science, engineering, etc.
            keywords = ['data']
            
        all_jobs = []
        
        for keyword in keywords:
            print(f"   Buscando '{keyword}' en GetOnBoard...")
            try:
                response = self.session.get(
                    self.api_url,
                    params={'query': keyword},
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()
                
                raw_jobs = data.get('data', [])
                for raw_job in raw_jobs:
                    job_data = self._parse_job(raw_job)
                    if job_data:
                        all_jobs.append(job_data)
                        
                self.rate_limit(1.0)
                
            except Exception as e:
                print(f"   Error consultando API GetOnBoard para '{keyword}': {e}")
                
        # Deduplicar por URL
        unique_jobs = {job['url']: job for job in all_jobs}.values()
        return list(unique_jobs)
        
    def _parse_job(self, api_job: Dict) -> Dict:
        """Parsea el formato JSON de la API al formato estándar"""
        try:
            attrs = api_job.get('attributes', {})
            links = api_job.get('links', {})
            
            # Limpiar HTML de descripciones usando BeautifulSoup
            desc_html = attrs.get('description', '') + ' ' + attrs.get('functions', '')
            req_html = attrs.get('desirable', '') + ' ' + attrs.get('requirements', '')
            
            description = BeautifulSoup(desc_html, 'html.parser').get_text(separator=' ', strip=True) if desc_html.strip() else ""
            requirements = BeautifulSoup(req_html, 'html.parser').get_text(separator=' ', strip=True) if req_html.strip() else ""
            
            # Formatear fecha
            published_timestamp = attrs.get('published_at')
            posted_date = datetime.datetime.fromtimestamp(published_timestamp).isoformat() if published_timestamp else datetime.datetime.now().isoformat()
            
            # Extraer modalidades
            remote_modality = attrs.get('remote_modality', '')
            if remote_modality == 'fully_remote':
                description += " (100% Remoto)"
            elif remote_modality == 'hybrid':
                description += " (Híbrido)"
            
            # Extraer empresa del ID (suele tener el formato nombre-empresa-ciudad al final)
            # Como la API v0 no da el nombre de la empresa directo en este endpoint sin expander
            company_str = api_job.get('id', 'Empresa Confidencial')
            
            raw_data = {
                'external_id': api_job.get('id'),
                'title': attrs.get('title', ''),
                'company': company_str.replace('-', ' ').title(), # Aproximación
                'description': description,
                'requirements': requirements,
                'salary_min': attrs.get('min_salary'),
                'salary_max': attrs.get('max_salary'),
                'location': ', '.join(attrs.get('countries', [])),
                'url': links.get('public_url', ''),
                'posted_date': posted_date,
                'deadline_date': None
            }
            
            return self.normalize_job(raw_data)
            
        except Exception as e:
            print(f"   Error parseando oferta {api_job.get('id')}: {e}")
            return None
