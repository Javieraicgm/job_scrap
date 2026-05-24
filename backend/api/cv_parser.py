"""
CV Parser - Extrae información estructurada de CVs
Soporta: PDF, DOCX
"""

import re
from typing import Dict, List, Optional
import PyPDF2
from docx import Document


class CVParser:
    """Extrae información estructurada de un CV"""
    
    # Skills técnicos conocidos para Data Science
    TECH_SKILLS = {
        'python', 'r', 'sql', 'java', 'scala', 'julia', 'matlab',
        'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'sklearn',
        'spark', 'hadoop', 'kafka', 'airflow', 'dbt',
        'aws', 'azure', 'gcp', 'google cloud',
        'power bi', 'tableau', 'looker', 'qlik', 'metabase',
        'postgresql', 'mysql', 'mongodb', 'redis', 'cassandra',
        'docker', 'kubernetes', 'git', 'mlflow',
        'excel', 'latex', 'jupyter',
        'machine learning', 'deep learning', 'nlp', 
        'computer vision', 'estadística', 'statistics'
    }
    
    # Títulos de cargo comunes
    JOB_TITLES = {
        'data scientist', 'científico de datos', 'cientifico datos',
        'data analyst', 'analista de datos', 'analista datos',
        'ml engineer', 'machine learning engineer', 'ingeniero ml',
        'data engineer', 'ingeniero de datos', 'ingeniero datos',
        'business intelligence', 'bi analyst', 'analista bi',
        'research scientist', 'científico investigador'
    }
    
    def parse_cv(self, file_path: str) -> Dict:
        """
        Parsea un CV y extrae información estructurada.
        
        Args:
            file_path: Ruta al archivo CV (PDF o DOCX)
            
        Returns:
            Dict con campos extraídos:
            {
                'name': str,
                'email': str,
                'phone': str,
                'skills': List[str],
                'desired_roles': List[str],
                'years_experience': int,
                'education_level': str,
                'raw_text': str
            }
        """
        # Extraer texto
        if file_path.endswith('.pdf'):
            text = self._extract_text_from_pdf(file_path)
        elif file_path.endswith('.docx'):
            text = self._extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Formato no soportado: {file_path}")
        
        if not text:
            raise ValueError("No se pudo extraer texto del CV")
        
        # Extraer información
        profile = {
            'name': self._extract_name(text),
            'email': self._extract_email(text),
            'phone': self._extract_phone(text),
            'skills': self._extract_skills(text),
            'desired_roles': self._extract_roles(text),
            'years_experience': self._extract_experience_years(text),
            'education_level': self._extract_education(text),
            'raw_text': text
        }
        
        return profile
    
    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extrae texto de PDF"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error extrayendo PDF: {e}")
        return text
    
    def _extract_text_from_docx(self, file_path: str) -> str:
        """Extrae texto de DOCX"""
        text = ""
        try:
            doc = Document(file_path)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            print(f"Error extrayendo DOCX: {e}")
        return text
    
    def _extract_name(self, text: str) -> Optional[str]:
        """
        Intenta extraer el nombre (primera línea generalmente)
        """
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines:
            # Primera línea no vacía, max 50 caracteres
            first_line = lines[0]
            if len(first_line) < 50 and not '@' in first_line:
                return first_line
        return None
    
    def _extract_email(self, text: str) -> Optional[str]:
        """Extrae email usando regex"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        return emails[0] if emails else None
    
    def _extract_phone(self, text: str) -> Optional[str]:
        """Extrae teléfono chileno"""
        # Patrones chilenos: +56912345678, 912345678, +56 9 1234 5678
        phone_patterns = [
            r'\+56\s*9\s*\d{4}\s*\d{4}',
            r'\+56\d{9}',
            r'9\d{8}'
        ]
        
        for pattern in phone_patterns:
            phones = re.findall(pattern, text.replace('-', '').replace(' ', ''))
            if phones:
                return phones[0]
        return None
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extrae skills técnicos del texto mediante heurística de secciones y keywords"""
        found_skills = []
        
        # 1. Extracción Heurística por Secciones
        section_patterns = [r'(?i)\bhabilidades\b', r'(?i)\bskills\b', r'(?i)\baptitudes\b', r'(?i)\bconocimientos\b', r'(?i)\btecnolog[ií]as\b']
        lines = text.split('\n')
        in_skills_section = False
        
        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue
                
            # Detectar inicio de sección de habilidades
            if len(line_clean) < 40 and any(re.search(p, line_clean) for p in section_patterns):
                in_skills_section = True
                continue
            
            # Detectar fin de sección (otro título corto)
            stop_words = ['experiencia', 'educación', 'education', 'experience', 'perfil', 'resumen', 'idiomas', 'languages']
            if in_skills_section:
                if len(line_clean) < 40 and any(sw == line_clean.lower() for sw in stop_words):
                    in_skills_section = False
                    continue
                    
                # Extraer elementos de la sección
                # Limpiar viñetas comunes
                clean_str = re.sub(r'^[-*•>]\s*', '', line_clean)
                
                # Separar por comas si las hay
                if ',' in clean_str:
                    parts = [p.strip() for p in clean_str.split(',')]
                    found_skills.extend([p for p in parts if 2 < len(p) < 40])
                elif len(clean_str) < 40:  # Si la línea es corta, asumimos que es un skill listado hacia abajo
                    found_skills.append(clean_str)

        # 2. Extracción por Diccionario (Fallback)
        text_lower = text.lower()
        for skill in self.TECH_SKILLS:
            if skill in text_lower:
                found_skills.append(skill.title())
                
        # Limpiar y deduplicar
        final_skills = []
        seen = set()
        for s in found_skills:
            s_clean = s.strip()
            if s_clean and s_clean.lower() not in seen:
                seen.add(s_clean.lower())
                # Si es del diccionario lo formateamos bonito, sino lo dejamos como lo escribió el usuario (titlecase)
                final_skills.append(s_clean.title())
                
        return final_skills
    
    def _extract_roles(self, text: str) -> List[str]:
        """
        Extrae roles/cargos que aparecen en el CV
        """
        text_lower = text.lower()
        found_roles = []
        
        for role in self.JOB_TITLES:
            if role in text_lower:
                found_roles.append(role.title())
        
        # Si no encontramos ninguno, inferir por skills
        if not found_roles:
            skills_lower = [s.lower() for s in self._extract_skills(text)]
            if any(s in skills_lower for s in ['python', 'machine learning', 'tensorflow']):
                found_roles.append('Data Scientist')
            if any(s in skills_lower for s in ['power bi', 'tableau', 'sql']):
                found_roles.append('Data Analyst')
        
        return list(set(found_roles))
    
    def _extract_experience_years(self, text: str) -> Optional[int]:
        """
        Intenta extraer años de experiencia
        Busca patrones como "5 años de experiencia", "3+ years"
        """
        patterns = [
            r'(\d+)\+?\s*años?\s+de\s+experiencia',
            r'(\d+)\+?\s*years?\s+of\s+experience',
            r'experiencia\s+de\s+(\d+)\+?\s*años?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return int(match.group(1))
        
        # Contar empleos anteriores como proxy
        job_patterns = [
            r'(20\d{2})\s*-\s*(20\d{2}|presente|actual)',
        ]
        
        total_years = 0
        for pattern in job_patterns:
            matches = re.findall(pattern, text.lower())
            for start, end in matches:
                start_year = int(start)
                end_year = 2025 if 'presente' in end or 'actual' in end else int(end)
                total_years += (end_year - start_year)
        
        return total_years if total_years > 0 else None
    
    def _extract_education(self, text: str) -> Optional[str]:
        """
        Extrae nivel educacional
        """
        text_lower = text.lower()
        
        education_levels = {
            'phd': ['doctorado', 'phd', 'ph.d', 'doctor'],
            'masters': ['magíster', 'magister', 'maestría', 'master', 'msc', 'm.sc'],
            'bachelors': ['ingeniero', 'ingeniera', 'licenciado', 'licenciada', 
                         'bachelor', 'título profesional'],
            'technical': ['técnico', 'technician']
        }
        
        for level, keywords in education_levels.items():
            if any(kw in text_lower for kw in keywords):
                return level
        
        return None
    
    def generate_summary(self, profile: Dict) -> str:
        """
        Genera un resumen legible del perfil extraído
        """
        summary = []
        
        if profile.get('name'):
            summary.append(f"Nombre: {profile['name']}")
        
        if profile.get('email'):
            summary.append(f"Email: {profile['email']}")
        
        if profile.get('skills'):
            skills_str = ', '.join(profile['skills'][:10])
            summary.append(f"Skills: {skills_str}")
        
        if profile.get('desired_roles'):
            roles_str = ', '.join(profile['desired_roles'])
            summary.append(f"Roles: {roles_str}")
        
        if profile.get('years_experience'):
            summary.append(f"Experiencia: {profile['years_experience']} años")
        
        if profile.get('education_level'):
            summary.append(f"Educación: {profile['education_level']}")
        
        return '\n'.join(summary)


# Test
if __name__ == '__main__':
    # Ejemplo con texto simulado
    sample_text = """
    Juan Pérez González
    juan.perez@email.com | +56 9 1234 5678
    
    Data Scientist con 5 años de experiencia
    
    HABILIDADES
    - Python, R, SQL
    - TensorFlow, PyTorch
    - Power BI, Tableau
    - AWS, Docker
    
    EXPERIENCIA
    Data Scientist - Empresa Tech (2020-2025)
    Analista de Datos - StartupCL (2018-2020)
    
    EDUCACIÓN
    Magíster en Ciencia de Datos - Universidad de Chile (2018)
    Ingeniero Civil - PUC (2016)
    """
    
    parser = CVParser()
    
    # Simular extracción (en producción vendría de archivo)
    profile = {
        'name': parser._extract_name(sample_text),
        'email': parser._extract_email(sample_text),
        'phone': parser._extract_phone(sample_text),
        'skills': parser._extract_skills(sample_text),
        'desired_roles': parser._extract_roles(sample_text),
        'years_experience': parser._extract_experience_years(sample_text),
        'education_level': parser._extract_education(sample_text)
    }
    
    print(parser.generate_summary(profile))
