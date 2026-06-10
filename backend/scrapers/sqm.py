import os
import time
from typing import List, Dict
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

class SqmScraper:
    def __init__(self):
        self.base_url = "https://trabajaensqm.com/"
        
    def scrape(self) -> List[Dict]:
        """
        Extrae ofertas de SQM usando Playwright para renderizar la página SPA.
        """
        jobs = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(self.base_url, timeout=30000)
                
                # Esperar a que cargue la lista de publicaciones (el div con clase 'publication' o similar)
                # En React de 4Talent normalmente los jobs tienen clase 'hit' o 'card' o 'publication'
                # Esperamos a que no haya skeleton loader o esperamos 5 segundos
                page.wait_for_timeout(10000)
                
                html = page.content()
                page.screenshot(path="sqm.png")
                with open('sqm_render.html', 'w', encoding='utf-8') as f:
                    f.write(html)
                soup = BeautifulSoup(html, 'html.parser')
                
                # Buscamos elementos de ofertas
                # Usualmente en 4Talent/HiringUp es div.publication-panel
                offer_cards = soup.find_all('div', class_=lambda c: c and 'publication-panel' in c)
                
                for card in offer_cards:
                    link_elem = card.find('a', class_='publication_link')
                    if not link_elem:
                        continue
                        
                    title_elem = card.find('h2')
                    title = title_elem.get_text(strip=True) if title_elem else "Sin título"
                    # Quitar el texto 'Nuevo' si está
                    if title.startswith('Nuevo'):
                        title = title[5:].strip()
                    
                    link = link_elem.get('href', '')
                    if link and not link.startswith('http'):
                        link = self.base_url.rstrip('/') + '/' + link.lstrip('/')
                        
                    # Extraer location (está en un li con fa-map-marker)
                    location_elem = card.find('i', class_='fa-map-marker')
                    location = location_elem.parent.get_text(strip=True) if location_elem and location_elem.parent else "Chile"
                    
                    jobs.append({
                        "title": title,
                        "company": "SQM",
                        "location": location,
                        "description": "",
                        "url": link,
                        "source": "SQM",
                        "date_posted": None
                    })
                
                browser.close()
                return jobs
                
        except Exception as e:
            print(f"Error scraping SQM: {e}")
            return []

if __name__ == "__main__":
    scraper = SqmScraper()
    jobs = scraper.scrape()
    print(f"Encontrados {len(jobs)} trabajos en SQM")
    for j in jobs[:3]:
        print(j)
