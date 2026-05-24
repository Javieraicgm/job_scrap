import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import datetime
from .base_scraper import BaseScraper
import re
from urllib.parse import quote_plus

class LinkedInScraper(BaseScraper):
    """Scraper para LinkedIn Jobs (Búsqueda Pública)"""
    
    def __init__(self):
        super().__init__(
            source_id='linkedin',
            source_name='LinkedIn Jobs Chile',
            base_url='https://www.linkedin.com/jobs/search'
        )
        # LinkedIn requiere headers muy específicos para no rebotar la conexión
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1',
        })
        
    def scrape(self, keywords: List[str] = None) -> List[Dict]:
        if not keywords:
            keywords = ['data scientist', 'machine learning', 'geofisica']
            
        all_jobs = []
        
        for keyword in keywords:
            print(f"   Buscando '{keyword}' en LinkedIn...")
            try:
                # Codificar el keyword para la URL
                kw_encoded = quote_plus(keyword)
                # Formato de búsqueda pública de LinkedIn (Chile por defecto)
                url = f"{self.base_url}?keywords={kw_encoded}&location=Chile&geoId=104621616&trk=public_jobs_jobs-search-bar_search-submit&position=1&pageNum=0"
                
                soup = self.fetch_page(url)
                
                if not soup:
                    print(f"   No se pudo cargar la página para '{keyword}' (Posible bloqueo de LinkedIn)")
                    continue
                
                # Buscar las tarjetas de empleo. LinkedIn cambia las clases frecuentemente.
                # 'base-card' o 'job-search-card' suelen ser estables en la versión pública
                articles = soup.find_all('div', class_=re.compile(r'base-card|job-search-card'))
                if not articles:
                    articles = soup.find_all('li', class_=re.compile(r'result-card|job-result'))
                if not articles:
                    # Alternativa: li que contengan links
                    articles = [a.parent for a in soup.find_all('a', class_=re.compile(r'base-card__full-link'))]
                    
                print(f"   Encontradas {len(articles)} ofertas de '{keyword}' en LinkedIn.")
                
                for article in articles:
                    job_data = self._parse_article(article)
                    if job_data:
                        all_jobs.append(job_data)
                        
                # LinkedIn es MUY agresivo con los baneos. Usamos una pausa larga.
                self.rate_limit(4.0)
                
            except Exception as e:
                print(f"   Error consultando LinkedIn para '{keyword}': {e}")
                
        # Deduplicar por URL
        unique_jobs = {job['url']: job for job in all_jobs}.values()
        return list(unique_jobs)
        
    def _parse_article(self, article) -> Dict:
        """Extrae la información de la tarjeta HTML de LinkedIn Pública"""
        try:
            # 1. Enlace y Título
            title_elem = article.find('h3', class_=re.compile(r'title')) or article.find('span', class_='sr-only')
            if not title_elem:
                return None
            title = title_elem.get_text(strip=True)
            
            link_elem = article.find('a', class_=re.compile(r'base-card__full-link|result-card__full-card-link'))
            if not link_elem:
                link_elem = article.find('a', href=True)
                
            if not link_elem:
                return None
                
            job_url = link_elem.get('href', '').split('?')[0] # Limpiar tracking parameters
            
            # Extraer ID de LinkedIn de la URL
            external_id_match = re.search(r'view/(\d+)', job_url) or re.search(r'-(\d+)$', job_url)
            external_id = external_id_match.group(1) if external_id_match else job_url.split('/')[-1]
            
            # 2. Empresa
            company = "Confidencial"
            company_elem = article.find('h4', class_=re.compile(r'subtitle')) or article.find('a', class_=re.compile(r'hidden-nested-link'))
            if company_elem:
                company = company_elem.get_text(strip=True)
            
            # 3. Ubicación
            location = "Chile"
            location_elem = article.find('span', class_=re.compile(r'location'))
            if location_elem:
                location = location_elem.get_text(strip=True)
                
            # 4. Fecha de publicación (LinkedIn suele poner 'hace 3 días', etc. extraemos el datetime si existe)
            posted_date = datetime.datetime.now().isoformat()
            time_elem = article.find('time')
            if time_elem and time_elem.get('datetime'):
                posted_date = time_elem.get('datetime')
                
            raw_data = {
                'external_id': external_id,
                'title': title,
                'company': company,
                'description': f"Oferta de {title} en {company} ({location}). Extraída de LinkedIn.",
                'requirements': '',
                'salary_min': None,
                'salary_max': None,
                'location': location,
                'url': job_url,
                'posted_date': posted_date,
                'deadline_date': None
            }
            
            return self.normalize_job(raw_data)
            
        except Exception as e:
            print(f"   Error parseando artículo de LinkedIn: {e}")
            return None
