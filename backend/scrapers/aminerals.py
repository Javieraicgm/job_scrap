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
            base_url='https://performancemanager8.successfactors.com'
        )
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        })
        self.company_id = 'AMSAP'
        
    def scrape(self, keywords: List[str] = None) -> List[Dict]:
        if not keywords:
            keywords = ['data scientist', 'geofisico', 'datos', 'analista']
            
        all_jobs = []
        
        for keyword in keywords:
            print(f"   Buscando '{keyword}' en AMSA...")
            try:
                kw_formatted = keyword.replace(' ', '+')
                url = f"{self.base_url}/career?company={self.company_id}&career_ns=job_listing_summary&navBarLevel=JOB_SEARCH&_s.crb=1&keyword={kw_formatted}"
                
                soup = self.fetch_page(url)
                
                if not soup:
                    print(f"   No se pudo cargar la página para '{keyword}'")
                    continue
                
                # SuccessFactors usa tablas o tr con la clase 'job-result' o 'data-row'
                articles = soup.find_all('tr', class_=re.compile(r'data-row|job-result', re.IGNORECASE))
                
                if not articles:
                    # Alternativa: buscar enlaces que contengan /career?career_ns=job_listing
                    articles = []
                    links = soup.find_all('a', class_='jobTitle')
                    if not links:
                        links = soup.find_all('a', href=re.compile(r'career_ns=job_listing'))
                        
                    seen = set()
                    for link in links:
                        href = link.get('href', '')
                        if href not in seen:
                            seen.add(href)
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
            title_elem = article.find('a', class_='jobTitle') or article.find('a', href=re.compile(r'career_ns=job_listing'))
            if not title_elem:
                return None
                
            title = title_elem.get_text(strip=True)
            link_path = title_elem.get('href', '')
            if not link_path.startswith('http'):
                if not link_path.startswith('/'):
                    link_path = '/' + link_path
                job_url = self.base_url + link_path
            else:
                job_url = link_path
            
            # Extraer ID
            external_id_match = re.search(r'career_job_req_id=(\d+)', job_url)
            external_id = external_id_match.group(1) if external_id_match else "amsa_" + str(hash(title))[:6]
            
            # 2. Empresa y Ubicación (en SuccessFactors suele estar en spans con clases específicas)
            location = "Chile"
            location_elem = article.find('span', class_=re.compile(r'jobLocation', re.IGNORECASE)) or article.find('div', class_='location')
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
            
            # No hacemos fetch_page detallado para no demorar
            
            return self.normalize_job(raw_data)
            
        except Exception as e:
            print(f"   Error parseando artículo de AMSA: {e}")
            return None
