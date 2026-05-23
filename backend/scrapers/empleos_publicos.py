"""
Scraper para Empleos Públicos Chile (empleospublicos.cl)
"""

from .base_scraper import BaseScraper
from typing import List, Dict
from datetime import datetime
import re


class EmpleosPublicosScraper(BaseScraper):
    """Scraper para portal de empleos públicos chileno"""
    
    def __init__(self):
        super().__init__(
            source_id='empleos_publicos',
            source_name='Empleos Públicos Chile',
            base_url='https://www.empleospublicos.cl'
        )
        self.search_url = f"{self.base_url}/pub/convocatorias/buscador.aspx"
    
    def scrape(self, keywords: List[str] = None) -> List[Dict]:
        """
        Busca ofertas en empleospublicos.cl
        
        Args:
            keywords: Lista de términos de búsqueda
            
        Returns:
            Lista de ofertas normalizadas
        """
        if keywords is None:
            keywords = [
                'data scientist', 
                'científico de datos',
                'analista de datos',
                'data analyst',
                'business intelligence',
                'machine learning'
            ]
        
        all_jobs = []
        
        for keyword in keywords:
            print(f"Buscando '{keyword}' en Empleos Públicos...")
            jobs = self._search_keyword(keyword)
            all_jobs.extend(jobs)
            self.rate_limit(2)  # Esperar 2 segundos entre búsquedas
        
        # Remover duplicados por URL
        unique_jobs = {job['url']: job for job in all_jobs}
        
        print(f"Total ofertas encontradas: {len(unique_jobs)}")
        return list(unique_jobs.values())
    
    def _search_keyword(self, keyword: str) -> List[Dict]:
        """Busca un keyword específico"""
        
        # Nota: empleospublicos.cl requiere form submission y maneja sesiones
        # Para MVP, haremos scraping de la página de búsqueda general
        # En producción, se puede usar Selenium para interacción completa
        
        search_params = {
            'palabra_clave': keyword,
            'region': '',  # Todas las regiones
            'institucion': ''  # Todas las instituciones
        }
        
        try:
            # Obtener página de resultados
            soup = self.fetch_page(self.search_url)
            
            if not soup:
                return []
            
            jobs = []
            
            # Extraer ofertas (estructura específica del sitio)
            # NOTA: Esta es una estructura de ejemplo
            # Debe ajustarse a la estructura real del HTML
            
            job_cards = soup.find_all('div', class_='resultado-convocatoria')
            
            for card in job_cards:
                try:
                    job = self._parse_job_card(card)
                    if job:
                        jobs.append(self.normalize_job(job))
                except Exception as e:
                    print(f"Error parseando oferta: {e}")
                    continue
            
            return jobs
            
        except Exception as e:
            print(f"Error en búsqueda de '{keyword}': {e}")
            return []
    
    def _parse_job_card(self, card) -> Dict:
        """Extrae datos de una tarjeta de oferta"""
        
        # Extraer título
        title_elem = card.find('h3') or card.find('a', class_='titulo')
        title = title_elem.get_text(strip=True) if title_elem else ''
        
        # Extraer link
        link_elem = card.find('a', href=True)
        url = self.base_url + link_elem['href'] if link_elem else ''
        
        # Extraer institución
        institution_elem = card.find('span', class_='institucion')
        company = institution_elem.get_text(strip=True) if institution_elem else ''
        
        # Extraer ubicación
        location_elem = card.find('span', class_='region')
        location = location_elem.get_text(strip=True) if location_elem else 'Chile'
        
        # Extraer fecha de publicación
        date_elem = card.find('span', class_='fecha-publicacion')
        posted_date = self._parse_date(date_elem.get_text(strip=True)) if date_elem else None
        
        # Extraer salario (si está visible)
        salary_elem = card.find('span', class_='remuneracion')
        salary_text = salary_elem.get_text(strip=True) if salary_elem else ''
        
        # ID único basado en URL
        external_id = re.search(r'id=(\d+)', url)
        external_id = external_id.group(1) if external_id else url.split('/')[-1]
        
        return {
            'external_id': external_id,
            'title': title,
            'company': company,
            'description': '',  # Se obtendría haciendo click en el detalle
            'requirements': '',
            'salary_min': self.parse_salary(salary_text),
            'salary_max': None,
            'location': location,
            'url': url,
            'posted_date': posted_date,
            'deadline_date': None
        }
    
    def _parse_date(self, date_str: str) -> str:
        """
        Convierte fechas como "15-05-2025" o "hace 3 días" a ISO format
        """
        try:
            # Formato DD-MM-YYYY
            if '-' in date_str and len(date_str.split('-')) == 3:
                day, month, year = date_str.split('-')
                return f"{year}-{month}-{day}"
            
            # "Hace X días"
            if 'hace' in date_str.lower():
                days_match = re.search(r'(\d+)', date_str)
                if days_match:
                    days = int(days_match.group(1))
                    date = datetime.now() - timedelta(days=days)
                    return date.strftime('%Y-%m-%d')
            
            # Default: hoy
            return datetime.now().strftime('%Y-%m-%d')
            
        except Exception:
            return datetime.now().strftime('%Y-%m-%d')


# Test standalone
if __name__ == '__main__':
    from datetime import timedelta
    
    scraper = EmpleosPublicosScraper()
    jobs = scraper.scrape()
    
    print(f"\n=== Resultados ===")
    for job in jobs[:5]:  # Mostrar primeras 5
        print(f"\nTítulo: {job['title']}")
        print(f"Empresa: {job['company']}")
        print(f"Ubicación: {job['location']}")
        print(f"Skills: {', '.join(job['required_skills'])}")
        print(f"URL: {job['url']}")
