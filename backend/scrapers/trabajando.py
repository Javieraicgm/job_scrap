import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import datetime
from .base_scraper import BaseScraper
import re

class TrabajandoScraper(BaseScraper):
    """Scraper web para Trabajando.com Chile"""
    
    def __init__(self):
        super().__init__(
            source_id='trabajando',
            source_name='Trabajando.com Chile',
            base_url='https://www.trabajando.cl'
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
            print(f"   Buscando '{keyword}' en Trabajando.com...")
            try:
                # Reemplazamos espacios por guiones para la URL
                kw_formatted = keyword.replace(' ', '-')
                url = f"{self.base_url}/ofertas-trabajo-empleo/{kw_formatted}"
                
                soup = self.fetch_page(url)
                
                if not soup:
                    print(f"   No se pudo cargar la página para '{keyword}'")
                    continue
                
                # Buscamos contenedores de ofertas, Trabajando suele usar div con ids o clases especificas
                articles = soup.find_all('div', attrs={'data-cy': 'jobCard'})
                if not articles:
                    articles = soup.find_all('div', class_=re.compile(r'jobCard|oferta|card|job-offer', re.IGNORECASE))
                    
                print(f"   Encontradas {len(articles)} ofertas de '{keyword}' en la primera página.")
                
                for article in articles:
                    job_data = self._parse_article(article)
                    if job_data:
                        all_jobs.append(job_data)
                        
                self.rate_limit(2.0)
                
            except Exception as e:
                print(f"   Error consultando Trabajando.com para '{keyword}': {e}")
                
        # Deduplicar por URL
        unique_jobs = {job['url']: job for job in all_jobs}.values()
        return list(unique_jobs)
        
    def _parse_article(self, article: BeautifulSoup) -> Dict:
        """Extrae la información de la tarjeta HTML de Trabajando.com"""
        try:
            # 1. Enlace y Título
            title_elem = article.find('h2') or article.find('a', class_=re.compile('title|titulo', re.IGNORECASE))
            if not title_elem:
                return None
                
            title = title_elem.get_text(strip=True)
            
            # Buscar link
            link_elem = article.find('a', href=True)
            if not link_elem:
                return None
                
            link_path = link_elem.get('href', '')
            job_url = self.base_url + link_path if link_path.startswith('/') else link_path
            
            # Extraer ID (usualmente está en la URL)
            external_id_match = re.search(r'/(\d+)$', job_url)
            external_id = external_id_match.group(1) if external_id_match else job_url.split('/')[-1]
            
            # 2. Empresa
            company = ""
            if article.find(string=re.compile('Confidencial', re.IGNORECASE)):
                company = 'Confidencial'
            else:
                company_elem = article.find('h3') or article.find('span', class_=re.compile('company|empresa', re.IGNORECASE))
                if company_elem:
                    company = company_elem.get_text(strip=True)
            
            # 3. Ubicación
            location = "Chile"
            location_elem = article.find('span', class_=re.compile('location|lugar|region', re.IGNORECASE))
            if location_elem:
                location = location_elem.get_text(strip=True)
                
            raw_data = {
                'external_id': external_id,
                'title': title,
                'company': company,
                'description': f"Oferta de {title} en {company} ({location}). Extraída de Trabajando.com",
                'requirements': '',
                'salary_min': None,
                'salary_max': None,
                'location': location,
                'url': job_url,
                'posted_date': datetime.datetime.now().isoformat(),
                'deadline_date': None
            }
            
            return self.normalize_job(raw_data)
            
        except Exception as e:
            print(f"   Error parseando artículo de Trabajando.com: {e}")
            return None
