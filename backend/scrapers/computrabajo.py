import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import datetime
from .base_scraper import BaseScraper

class ComputrabajoScraper(BaseScraper):
    """Scraper web tradicional para Computrabajo Chile"""
    
    def __init__(self):
        super().__init__(
            source_id='computrabajo',
            source_name='Computrabajo Chile',
            base_url='https://cl.computrabajo.com'
        )
        # Añadimos un User-Agent muy estándar para evitar bloqueos básicos
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        })
        
    def scrape(self, keywords: List[str] = None) -> List[Dict]:
        if not keywords:
            keywords = ['data']
            
        all_jobs = []
        
        for keyword in keywords:
            print(f"   Buscando '{keyword}' en Computrabajo...")
            try:
                # Computrabajo formatea la URL como /trabajo-de-{keyword}
                url = f"{self.base_url}/trabajo-de-{keyword}"
                soup = self.fetch_page(url)
                
                if not soup:
                    print(f"   No se pudo cargar la página para '{keyword}'")
                    continue
                
                articles = soup.find_all('article', class_='box_offer')
                print(f"   Encontradas {len(articles)} ofertas de '{keyword}' en la primera página.")
                
                for article in articles:
                    job_data = self._parse_article(article)
                    if job_data:
                        all_jobs.append(job_data)
                        
                self.rate_limit(2.0) # Pausa amigable entre keywords
                
            except Exception as e:
                print(f"   Error consultando Computrabajo para '{keyword}': {e}")
                
        # Deduplicar por URL
        unique_jobs = {job['url']: job for job in all_jobs}.values()
        return list(unique_jobs)
        
    def _parse_article(self, article: BeautifulSoup) -> Dict:
        """Extrae la información de la tarjeta HTML de una oferta"""
        try:
            # 1. Enlace y Título
            title_link = article.find('a', class_='js-o-link')
            if not title_link:
                return None
                
            title = title_link.get_text(strip=True)
            link_path = title_link.get('href', '')
            job_url = self.base_url + link_path if link_path.startswith('/') else link_path
            
            # El ID se puede extraer del data-id del article
            external_id = article.get('data-id', '')
            
            # 2. Empresa
            company = ""
            company_link = article.find('a', attrs={'offer-grid-article-company-url': True})
            if company_link:
                company = company_link.get_text(strip=True)
            else:
                # A veces es confidencial, buscamos texto sin link
                p_tags = article.find_all('p')
                for p in p_tags:
                    if 'Confidencial' in p.text:
                        company = 'Confidencial'
                        break
            
            # 3. Ubicación y Salario
            location = ""
            salary_text = ""
            
            # Buscar en los siguientes párrafos (después del título y empresa)
            p_tags = article.find_all('p')
            if len(p_tags) > 1:
                # Normalmente la ubicación es el párrafo que no tiene estrellas
                for p in p_tags:
                    text = p.get_text(strip=True)
                    if '-' in text and not 'Mensual' in text and not 'hora' in text.lower():
                         location = text
                         break
            
            # El salario suele estar en un span con la clase mr10 o tener un símbolo $
            salary_span = article.find(string=lambda t: t and '$' in t)
            if salary_span:
                salary_text = salary_span.strip()

            raw_data = {
                'external_id': external_id,
                'title': title,
                'company': company,
                'description': f"Oferta de {title} en {company} ({location}). Extraída de la página de listado general.",
                'requirements': '', # El listado general no muestra detalles completos sin entrar al link
                'salary_min': salary_text, # El parse_salary de BaseScraper lo limpiará
                'salary_max': salary_text,
                'location': location,
                'url': job_url,
                'posted_date': datetime.datetime.now().isoformat(),
                'deadline_date': None
            }
            
            return self.normalize_job(raw_data)
            
        except Exception as e:
            print(f"   Error parseando artículo de Computrabajo: {e}")
            return None
