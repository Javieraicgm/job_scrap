import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import datetime
from .base_scraper import BaseScraper
import re

class AMineralsScraper(BaseScraper):
    """Scraper web para Antofagasta Minerals (SuccessFactors)"""
    
    def __init__(self):
        super().__init__(
            source_id='aminerals',
            source_name='Antofagasta Minerals',
            base_url='https://empleos.aminerals.cl'
        )
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        })
        
    def scrape(self, keywords: List[str] = None) -> List[Dict]:
        if not keywords:
            keywords = ['data scientist', 'geofisico', 'datos', 'analista']
            
        all_jobs = []
        
        for keyword in keywords:
            print(f"   Buscando '{keyword}' en AMSA...")
            try:
                kw_formatted = keyword.replace(' ', '+')
                url = f"{self.base_url}/search/?q={kw_formatted}"
                
                soup = self.fetch_page(url)
                
                if not soup:
                    print(f"   No se pudo cargar la página para '{keyword}'")
                    continue
                
                # SuccessFactors usa tablas o tr con la clase 'job-result' o 'data-row'
                articles = soup.find_all('tr', class_=re.compile(r'data-row|job-result', re.IGNORECASE))
                
                if not articles:
                    # Alternativa: buscar enlaces que contengan /job/
                    articles = []
                    links = soup.find_all('a', href=re.compile(r'/job/'))
                    # Deduplicar links
                    seen = set()
                    for link in links:
                        if link['href'] not in seen:
                            seen.add(link['href'])
                            articles.append(link.parent.parent) # subir al contenedor
                
                print(f"   Encontradas {len(articles)} ofertas de '{keyword}' en la primera página.")
                
                for article in articles:
                    job_data = self._parse_article(article)
                    if job_data:
                        all_jobs.append(job_data)
                        
                self.rate_limit(2.0)
                
            except Exception as e:
                print(f"   Error consultando AMSA para '{keyword}': {e}")
                
        unique_jobs = {job['url']: job for job in all_jobs}.values()
        return list(unique_jobs)
        
    def _parse_article(self, article) -> Dict:
        try:
            # 1. Enlace y Título
            link_elem = article.find('a', href=re.compile(r'/job/'))
            if not link_elem:
                return None
                
            title = link_elem.get_text(strip=True)
            link_path = link_elem.get('href', '')
            job_url = self.base_url + link_path if link_path.startswith('/') else link_path
            
            # Extraer ID
            external_id_match = re.search(r'/job/[^/]+/(\d+)', job_url)
            external_id = external_id_match.group(1) if external_id_match else job_url.split('/')[-2]
            
            # 2. Empresa y Ubicación (en SuccessFactors suele estar en spans con clases específicas)
            location = "Chile"
            location_elem = article.find('span', class_=re.compile(r'jobLocation', re.IGNORECASE))
            if location_elem:
                location = location_elem.get_text(strip=True)
            
            # A veces el departamento está en otro span
            department = "AMSA"
            dept_elem = article.find('span', class_=re.compile(r'department|facility', re.IGNORECASE))
            if dept_elem:
                department = f"AMSA - {dept_elem.get_text(strip=True)}"
                
            raw_data = {
                'external_id': external_id,
                'title': title,
                'company': department,
                'description': f"Oferta de {title} en {department} ({location}).",
                'requirements': '',
                'salary_min': None,
                'salary_max': None,
                'location': location,
                'url': job_url,
                'posted_date': datetime.datetime.now().isoformat(),
                'deadline_date': None
            }
            
            # Fetch para obtener descripción real
            try:
                job_soup = self.fetch_page(job_url)
                if job_soup:
                    desc_span = job_soup.find('span', class_=re.compile(r'jobdescription', re.IGNORECASE))
                    if desc_span:
                        raw_data['description'] = desc_span.get_text(separator='\n', strip=True)
            except Exception as e:
                print(f"   Error fetching description for {job_url}: {e}")
            
            return self.normalize_job(raw_data)
            
        except Exception as e:
            print(f"   Error parseando artículo de AMSA: {e}")
            return None
