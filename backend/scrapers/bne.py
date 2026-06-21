import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import datetime
from .base_scraper import BaseScraper
import re
import time

class BNEScraper(BaseScraper):
    """Scraper web para Bolsa Nacional de Empleo (BNE)"""
    
    def __init__(self):
        super().__init__(
            source_id='bne',
            source_name='Bolsa Nacional de Empleo',
            base_url='https://www.bne.cl'
        )
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        })
        
    def scrape(self, keywords: List[str] = None) -> List[Dict]:
        if not keywords:
            keywords = ['data scientist', 'analista de datos', 'geofisica']
            
        all_jobs = []
        
        for keyword in keywords:
            print(f"   Buscando '{keyword}' en BNE...")
            try:
                # Utilizamos la API pública de busqueda
                url = f"https://www.bne.cl/data/ofertas/buscarListas?mostrar=empleo&numResultadosPorPagina=15&clasificarYPaginar=true&textoLibre={keyword.replace(' ', '+')}"
                
                # Timeout de 15 segundos porque la BNE a veces demora en responder
                response = self.session.get(url, timeout=15)
                
                if response.status_code != 200:
                    print(f"   Error fetching BNE API: {response.status_code}")
                    continue
                    
                data = response.json()
                if 'paginaOfertas' in data and data['paginaOfertas']:
                    ofertas = data['paginaOfertas'].get('content', [])
                    print(f"   Encontradas {len(ofertas)} ofertas de '{keyword}' en BNE.")
                    
                    for of in ofertas:
                        job_data = self._parse_oferta(of)
                        if job_data:
                            all_jobs.append(job_data)
                else:
                    print(f"   No se encontraron ofertas para '{keyword}' en BNE.")
                    
                time.sleep(2.0)
                
            except requests.Timeout:
                print(f"   Timeout buscando en BNE para '{keyword}' (Portal muy lento)")
            except Exception as e:
                print(f"   Error consultando BNE para '{keyword}': {e}")
                
        unique_jobs = {job['url']: job for job in all_jobs}.values()
        return list(unique_jobs)
        
    def _parse_oferta(self, of: dict) -> Dict:
        """Parsea el objeto JSON de la oferta de BNE"""
        try:
            external_id = str(of.get('idOferta', ''))
            title = of.get('titulo', '')
            if not title:
                return None
                
            # La BNE suele ocultar nombres de empresas a veces ("Empresa Confidencial")
            company_data = of.get('empresa', {}) or {}
            company = company_data.get('nombreFicticio') or company_data.get('razonSocial') or 'Confidencial'
            
            salary_str = of.get('salarioStr', '')
            
            # Extraer ubicación si existe (suele venir en la comuna de la oferta)
            comuna = of.get('comuna', {})
            location = comuna.get('nombre', 'Chile') if isinstance(comuna, dict) else 'Chile'
            
            job_url = f"https://www.bne.cl/oferta/{external_id}"
            
            raw_data = {
                'external_id': external_id,
                'title': title,
                'company': company,
                'description': of.get('descripcion', ''),
                'salary_min': None,
                'salary_max': None,
                'location': location,
                'url': job_url,
                'posted_date': datetime.datetime.now().isoformat(),
                'deadline_date': None
            }
            
            return self.normalize_job(raw_data)
            
        except Exception as e:
            print(f"   Error parseando artículo de BNE: {e}")
            return None
