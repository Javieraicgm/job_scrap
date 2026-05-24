"""
Run All Scrapers
Ejecuta todos los scrapers activos y guarda resultados en Supabase
"""

import os
import json
import concurrent.futures
from datetime import datetime
from typing import List, Dict
from supabase import create_client, Client
from dotenv import load_dotenv

# Importar scrapers
from .empleos_publicos import EmpleosPublicosScraper
from .getonboard import GetOnBoardScraper
from .computrabajo import ComputrabajoScraper
from .trabajando import TrabajandoScraper
from .codelco import CodelcoScraper
from .linkedin import LinkedInScraper
from .bhp import BhpScraper

load_dotenv()


class ScraperRunner:
    """Ejecuta scrapers y guarda resultados en DB"""
    
    def __init__(self):
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', os.getenv('SUPABASE_KEY'))
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL y SUPABASE_KEY deben estar configurados")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
        # Cargar configuración de fuentes usando ruta absoluta
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sources_path = os.path.join(current_dir, '..', '..', 'shared', 'config', 'sources.json')
        with open(sources_path, 'r') as f:
            config = json.load(f)
            self.sources = config['sources']
    
    def run_all(self):
        """Ejecuta todos los scrapers activos"""
        
        # Mapeo de scrapers disponibles
        scraper_classes = {
            'empleos_publicos': EmpleosPublicosScraper,
            'getonboard': GetOnBoardScraper,
            'computrabajo': ComputrabajoScraper,
            'trabajando': TrabajandoScraper,
            'codelco': CodelcoScraper,
            'linkedin': LinkedInScraper,
            'bhp': BhpScraper,
        }
        
        total_new_jobs = 0
        
        active_sources = [s for s in self.sources if s['active'] and s['id'] in scraper_classes]
        
        def run_single_scraper(source):
            source_id = source['id']
            print(f"\n🔍 Ejecutando scraper: {source['name']}")
            run_id = None
            try:
                run_id = self._log_scraper_start(source_id)
            except Exception as e:
                print(f"No se pudo registrar log de inicio (ignorando): {e}")

            try:
                scraper = scraper_classes[source_id]()
                # Limitar búsqueda express a 1 keyword por rapidez si es posible, o usar todas. 
                # El método scrape original decide
                jobs = scraper.scrape()
                print(f"   Encontradas {len(jobs)} ofertas en {source['name']}")
                
                new_jobs = self._save_jobs(jobs)
                print(f"   ✅ {new_jobs} ofertas nuevas guardadas en {source['name']}")
                
                if run_id:
                    self._log_scraper_success(run_id, len(jobs), new_jobs)
                return new_jobs
                
            except Exception as e:
                print(f"   ❌ Error en {source['name']}: {e}")
                if run_id:
                    self._log_scraper_error(run_id, str(e))
                return 0

        # Ejecutar en paralelo para evitar timeout en Vercel (10s limit)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = executor.map(run_single_scraper, active_sources)
            total_new_jobs = sum(results)
        
        print(f"\n🎉 Total ofertas nuevas: {total_new_jobs}")
        return total_new_jobs
    
    def _save_jobs(self, jobs: List[Dict]) -> int:
        """Guarda ofertas en DB, evitando duplicados"""
        new_count = 0
        
        for job in jobs:
            try:
                # Intentar insertar (falla si URL duplicada)
                result = self.supabase.table('jobs').insert(job).execute()
                new_count += 1
                
            except Exception as e:
                # Si es duplicado, actualizar
                if 'duplicate' in str(e).lower() or 'unique' in str(e).lower():
                    self.supabase.table('jobs').update({
                        'description': job['description'],
                        'requirements': job['requirements'],
                        'scraped_at': job.get('scraped_at', datetime.now().isoformat())
                    }).eq('url', job['url']).execute()
                else:
                    print(f"      Error guardando oferta: {e}")
        
        return new_count
    
    def _log_scraper_start(self, source_id: str) -> str:
        """Registra inicio de scraper"""
        result = self.supabase.table('scraper_runs').insert({
            'source_id': source_id,
            'status': 'running',
            'started_at': datetime.now().isoformat()
        }).execute()
        
        return result.data[0]['id']
    
    def _log_scraper_success(self, run_id: str, jobs_found: int, new_jobs: int):
        """Registra éxito de scraper"""
        self.supabase.table('scraper_runs').update({
            'status': 'success',
            'jobs_found': jobs_found,
            'new_jobs': new_jobs,
            'finished_at': datetime.now().isoformat()
        }).eq('id', run_id).execute()
    
    def _log_scraper_error(self, run_id: str, error_msg: str):
        """Registra error de scraper"""
        self.supabase.table('scraper_runs').update({
            'status': 'failed',
            'errors': [error_msg],
            'finished_at': datetime.now().isoformat()
        }).eq('id', run_id).execute()


if __name__ == '__main__':
    print("=" * 60)
    print("🤖 Job Detector - Scraper Runner")
    print("=" * 60)
    
    runner = ScraperRunner()
    runner.run_all()
