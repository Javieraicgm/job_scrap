"""
Base scraper class for job sources.
Todos los scrapers heredan de esta clase.
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
import time
import re
from abc import ABC, abstractmethod


class BaseScraper(ABC):
    """Clase base abstracta para scrapers de ofertas laborales"""
    
    def __init__(self, source_id: str, source_name: str, base_url: str):
        self.source_id = source_id
        self.source_name = source_name
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    @abstractmethod
    def scrape(self, keywords: List[str] = None) -> List[Dict]:
        """
        Método principal que cada scraper debe implementar.
        
        Args:
            keywords: Lista de palabras clave para filtrar (ej: ["data scientist", "python"])
            
        Returns:
            Lista de diccionarios con ofertas encontradas
        """
        pass
    
    def normalize_job(self, raw_job: Dict) -> Dict:
        """
        Normaliza los datos de una oferta al formato estándar.
        
        Returns:
            {
                'source_id': str,
                'external_id': str,
                'title': str,
                'company': str,
                'description': str,
                'requirements': str,
                'salary_min': int or None,
                'salary_max': int or None,
                'work_mode': str,  # remote, hybrid, onsite
                'location': str,
                'url': str,
                'posted_date': str (ISO format),
                'deadline_date': str (ISO format) or None,
                'required_skills': List[str],
                'raw_data': Dict
            }
        """
        return {
            'source_id': self.source_id,
            'external_id': raw_job.get('external_id', ''),
            'title': self.clean_text(raw_job.get('title', '')),
            'company': self.clean_text(raw_job.get('company', '')),
            'description': self.clean_text(raw_job.get('description', '')),
            'requirements': self.clean_text(raw_job.get('requirements', '')),
            'salary_min': self.parse_salary(raw_job.get('salary_min')),
            'salary_max': self.parse_salary(raw_job.get('salary_max')),
            'work_mode': self.detect_work_mode(raw_job.get('description', '')),
            'location': self.clean_text(raw_job.get('location', '')),
            'url': raw_job.get('url', ''),
            'posted_date': raw_job.get('posted_date'),
            'deadline_date': raw_job.get('deadline_date'),
            'required_skills': self.extract_skills(raw_job),
            'raw_data': raw_job
        }
    
    def clean_text(self, text: str) -> str:
        """Limpia texto: espacios, saltos de línea, etc."""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def parse_salary(self, salary_str: Optional[str]) -> Optional[int]:
        """
        Extrae salario numérico de strings como:
        - "$1.200.000"
        - "1200000"
        - "1.2M"
        """
        if not salary_str:
            return None
        
        # Remover puntos, comas, símbolos
        salary_str = str(salary_str).replace('.', '').replace(',', '').replace('$', '').strip()
        
        # Manejar formato "1.5M" = 1.500.000
        if 'M' in salary_str.upper():
            try:
                return int(float(salary_str.upper().replace('M', '')) * 1_000_000)
            except:
                return None
        
        # Extraer primer número encontrado
        match = re.search(r'\d+', salary_str)
        if match:
            return int(match.group())
        
        return None
    
    def detect_work_mode(self, text: str) -> str:
        """Detecta modalidad de trabajo del texto"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['remoto', 'remote', 'teletrabajo', '100% remoto']):
            return 'remote'
        elif any(word in text_lower for word in ['híbrido', 'hybrid', 'mixto']):
            return 'hybrid'
        else:
            return 'onsite'
    
    def extract_skills(self, job_data: Dict) -> List[str]:
        """
        Extrae skills técnicos del título, descripción y requisitos.
        
        Skills conocidos para Data Science:
        """
        TECH_SKILLS = {
            # Lenguajes
            'python', 'r', 'sql', 'java', 'scala', 'julia',
            # Frameworks ML
            'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'sklearn',
            # Big Data
            'spark', 'hadoop', 'kafka', 'airflow',
            # Cloud
            'aws', 'azure', 'gcp', 'google cloud',
            # BI
            'power bi', 'tableau', 'looker', 'qlik',
            # Databases
            'postgresql', 'mysql', 'mongodb', 'redis', 'cassandra',
            # Other
            'docker', 'kubernetes', 'git', 'mlflow', 'dbt',
            'excel', 'matlab', 'latex', 'jupyter',
            # Técnicas
            'machine learning', 'deep learning', 'nlp', 'computer vision',
            'estadística', 'statistics'
        }
        
        # Combinar todo el texto
        full_text = ' '.join([
            job_data.get('title', ''),
            job_data.get('description', ''),
            job_data.get('requirements', '')
        ]).lower()
        
        # Encontrar matches
        found_skills = []
        for skill in TECH_SKILLS:
            if skill in full_text:
                found_skills.append(skill.title())
        
        return list(set(found_skills))  # Remover duplicados
    
    def rate_limit(self, seconds: float = 1.0):
        """Pausa entre requests para no saturar el servidor"""
        time.sleep(seconds)
    
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Obtiene y parsea una página HTML"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
