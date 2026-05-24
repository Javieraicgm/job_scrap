"""
Run All Scrapers
Ejecuta todos los scrapers activos y guarda resultados en Supabase
"""

import os
import json
from datetime import datetime
from typing import List, Dict
from supabase import create_client, Client
from dotenv import load_dotenv

# Importar scrapers
from .empleos_publicos import EmpleosPublicosScraper
from .getonboard import GetOnBoardScraper
# Importar otros scrapers cuando estén listos
# from .linkedin import LinkedInScraper

load_dotenv()


class ScraperRunner:
    """Ejecuta scrapers y guarda resultados en DB"""
    
    def __init__(self):
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL y SUPABASE_KEY deben estar configurados")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
        # Cargar configuración de fuentes
        with open('../../shared/config/sources.json', 'r') as f:
            config = json.load(f)
            self.sources = config['sources']
    
    def run_all(self):
        """Ejecuta todos los scrapers activos"""
        
        # Mapeo de scrapers disponibles
        scraper_classes = {
            'empleos_publicos': EmpleosPublicosScraper,
            'getonboard': GetOnBoardScraper,
            # 'linkedin': LinkedInScraper,
        }
        
        total_new_jobs = 0
        
        for source in self.sources:
            if not source['active']:
                print(f"⏭️  Saltando {source['name']} (inactivo)")
                continue
            
            source_id = source['id']
            
            if source_id not in scraper_classes:
                print(f"⚠️  Scraper para {source['name']} no implementado aún")
                continue
            
            print(f"\n🔍 Ejecutando scraper: {source['name']}")
            
            # Registrar inicio
            run_id = self._log_scraper_start(source_id)
            
            try:
                # Ejecutar scraper
                scraper = scraper_classes[source_id]()
                jobs = scraper.scrape()
                
                print(f"   Encontradas {len(jobs)} ofertas")
                
                # Guardar en DB
                new_jobs = self._save_jobs(jobs)
                total_new_jobs += new_jobs
                
                print(f"   ✅ {new_jobs} ofertas nuevas guardadas")
                
                # Registrar éxito
                self._log_scraper_success(run_id, len(jobs), new_jobs)
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                self._log_scraper_error(run_id, str(e))
        
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
