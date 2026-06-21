import requests
from typing import List, Dict
import datetime
from .base_scraper import BaseScraper
import re
import json
import time

class LaborumScraper(BaseScraper):
    """Scraper web para Laborum Chile"""
    
    def __init__(self):
        super().__init__(
            source_id='laborum',
            source_name='Laborum Chile',
            base_url='https://www.laborum.cl'
        )
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9',
        })
        
    def scrape(self, keywords: List[str] = None) -> List[Dict]:
        if not keywords:
            keywords = ['data scientist', 'analista de datos', 'geofisica']
            
        all_jobs = []
        
        for keyword in keywords:
            print(f"   Buscando '{keyword}' en Laborum...")
            try:
                # Utilizamos el portal público
                kw_formatted = keyword.replace(' ', '-')
                url = f"{self.base_url}/empleos-busqueda-{kw_formatted}.html"
                
                response = self.session.get(url, timeout=15)
                if response.status_code != 200:
                    print(f"   Error fetching {url}: {response.status_code}")
                    continue
                
                html = response.text
                
                # Buscar el estado pre-cargado de la SPA de Laborum (Next.js o similar)
                match = re.search(r'window\.__PRELOADED_STATE__\s*=\s*({.*?});', html)
                if not match:
                    print(f"   No se encontró el estado precargado para '{keyword}'. Posible protección antibot.")
                    continue
                    
                state_json = match.group(1)
                data = json.loads(state_json)
                
                ofertas = []
                # Navegar el JSON para encontrar la lista de trabajos
                try:
                    # La estructura suele ser: data -> search -> listings -> content
                    # o algo similar dependiendo de la versión de Jobint
                    for key in data:
                        if isinstance(data[key], dict) and 'postings' in data[key]:
                            ofertas = data[key]['postings']
                            break
                        if isinstance(data[key], dict) and 'list' in data[key]:
                            ofertas = data[key]['list']
                            break
                            
                    # Alternativa: buscar directamente "postings" recursivamente (simplificado)
                    if not ofertas and 'search' in data and 'postings' in data['search']:
                        ofertas = data['search']['postings']
                except Exception:
                    pass
                    
                if not ofertas:
                    print(f"   Estructura JSON no reconocida o sin ofertas para '{keyword}' en Laborum.")
                    continue
                    
                print(f"   Encontradas {len(ofertas)} ofertas de '{keyword}' en Laborum.")
                
                for of in ofertas:
                    job_data = self._parse_oferta(of)
                    if job_data:
                        all_jobs.append(job_data)
                        
                time.sleep(2.0)
                
            except requests.Timeout:
                print(f"   Timeout buscando en Laborum para '{keyword}'")
            except Exception as e:
                print(f"   Error consultando Laborum para '{keyword}': {e}")
                
        unique_jobs = {job['url']: job for job in all_jobs}.values()
        return list(unique_jobs)
        
    def _parse_oferta(self, of: dict) -> Dict:
        """Parsea la oferta individual de Laborum desde el JSON"""
        try:
            # Laborum a veces viene como diccionario complejo
            if not isinstance(of, dict):
                return None
                
            external_id = str(of.get('id', '') or of.get('postingId', ''))
            title = of.get('title', '')
            if not title:
                return None
                
            company = of.get('companyName', '') or of.get('company', {}).get('name', 'Confidencial')
            
            # Construir URL
            url_slug = of.get('url', '')
            job_url = f"https://www.laborum.cl{url_slug}" if url_slug.startswith('/') else f"https://www.laborum.cl/empleos/{url_slug}"
            if not url_slug:
                job_url = f"https://www.laborum.cl/empleos/{external_id}.html"
            
            location_obj = of.get('location', {})
            location = location_obj.get('name', 'Chile') if isinstance(location_obj, dict) else str(location_obj or 'Chile')
            
            raw_data = {
                'external_id': external_id,
                'title': title,
                'company': company,
                'description': of.get('details', ''),
                'salary_min': None,
                'salary_max': None,
                'location': location,
                'url': job_url,
                'posted_date': datetime.datetime.now().isoformat(),
                'deadline_date': None
            }
            
            return self.normalize_job(raw_data)
            
        except Exception as e:
            print(f"   Error parseando artículo de Laborum: {e}")
            return None
