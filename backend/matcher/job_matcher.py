"""
Job Matching Engine
Calcula el score de compatibilidad entre un perfil y una oferta laboral.
"""

from typing import Dict, List, Tuple
import re


class JobMatcher:
    """Sistema de scoring para matching perfil-oferta"""
    
    # Pesos de cada componente del score (total = 100%)
    WEIGHTS = {
        'skills_match': 0.40,      # 40% - Match de skills técnicos
        'role_match': 0.30,        # 30% - Match de cargo deseado
        'salary_match': 0.20,      # 20% - Compatibilidad salarial
        'work_mode_match': 0.10    # 10% - Modalidad de trabajo
    }
    
    def __init__(self):
        self.role_keywords = {
            'data scientist': ['data scientist', 'científico de datos', 'cientifico datos'],
            'data analyst': ['data analyst', 'analista de datos', 'analista datos', 'business intelligence'],
            'ml engineer': ['machine learning', 'ml engineer', 'ingeniero ml', 'ai engineer'],
            'data engineer': ['data engineer', 'ingeniero de datos', 'ingeniero datos'],
            'bi analyst': ['business intelligence', 'bi analyst', 'analista bi']
        }
    
    def calculate_match(self, profile: Dict, job: Dict) -> Tuple[int, Dict]:
        """
        Calcula el score de match entre perfil y oferta.
        
        Args:
            profile: Diccionario con datos del perfil
            job: Diccionario con datos de la oferta
            
        Returns:
            (score, reasons) donde:
            - score: int de 0-100
            - reasons: dict con scores individuales y explicaciones
        """
        
        scores = {}
        reasons = {}
        
        # 1. Skills Match (40%)
        skills_score, skills_reason = self._calculate_skills_match(
            profile.get('skills', []),
            job.get('required_skills', [])
        )
        scores['skills_match'] = skills_score
        reasons['skills_match'] = skills_reason
        
        # 2. Role Match (30%)
        role_score, role_reason = self._calculate_role_match(
            profile.get('desired_roles', []),
            job.get('title', '')
        )
        scores['role_match'] = role_score
        reasons['role_match'] = role_reason
        
        # 3. Salary Match (20%)
        salary_score, salary_reason = self._calculate_salary_match(
            profile.get('min_salary'),
            job.get('salary_min'),
            job.get('salary_max')
        )
        scores['salary_match'] = salary_score
        reasons['salary_match'] = salary_reason
        
        # 4. Work Mode Match (10%)
        work_mode_score, work_mode_reason = self._calculate_work_mode_match(
            profile.get('work_modes', []),
            job.get('work_mode', '')
        )
        scores['work_mode_match'] = work_mode_score
        reasons['work_mode_match'] = work_mode_reason
        
        # Calcular score total ponderado
        total_score = sum(
            scores[key] * self.WEIGHTS[key] 
            for key in scores
        )
        
        # Redondear a entero
        total_score = round(total_score)
        
        # Compilar razones
        match_reasons = {
            'total_score': total_score,
            'component_scores': scores,
            'explanations': reasons
        }
        
        return total_score, match_reasons
    
    def _calculate_skills_match(
        self, 
        profile_skills: List[str], 
        job_skills: List[str]
    ) -> Tuple[int, str]:
        """
        Calcula match de skills técnicos.
        
        Returns:
            (score 0-100, explicación)
        """
        if not job_skills or not profile_skills:
            return 50, "No hay información de skills para comparar"
        
        # Normalizar a lowercase
        profile_skills_lower = [s.lower() for s in profile_skills]
        job_skills_lower = [s.lower() for s in job_skills]
        
        # Calcular intersección
        matched_skills = set(profile_skills_lower) & set(job_skills_lower)
        
        # Score basado en % de skills requeridos que el perfil tiene
        if len(job_skills_lower) > 0:
            match_percentage = len(matched_skills) / len(job_skills_lower)
        else:
            match_percentage = 0
        
        score = int(match_percentage * 100)
        
        # Generar explicación
        if matched_skills:
            matched_list = ', '.join(matched_skills)
            reason = f"Coincide en {len(matched_skills)}/{len(job_skills_lower)} skills: {matched_list}"
        else:
            reason = "No hay coincidencia directa en skills técnicos"
        
        return score, reason
    
    def _calculate_role_match(
        self, 
        desired_roles: List[str], 
        job_title: str
    ) -> Tuple[int, str]:
        """
        Calcula match del cargo con roles deseados.
        
        Returns:
            (score 0-100, explicación)
        """
        if not desired_roles or not job_title:
            return 50, "No hay información de cargo para comparar"
        
        job_title_lower = job_title.lower()
        
        # Buscar coincidencias exactas o parciales
        max_score = 0
        matched_role = None
        
        for desired_role in desired_roles:
            desired_lower = desired_role.lower()
            
            # Match exacto = 100
            if desired_lower in job_title_lower or job_title_lower in desired_lower:
                max_score = 100
                matched_role = desired_role
                break
            
            # Match por keywords = 70-90
            if desired_lower in self.role_keywords:
                keywords = self.role_keywords[desired_lower]
                for keyword in keywords:
                    if keyword in job_title_lower:
                        score = 80
                        if max_score < score:
                            max_score = score
                            matched_role = desired_role
        
        # Si no hay match, buscar keywords genéricos de data
        if max_score == 0:
            data_keywords = ['data', 'datos', 'analytic', 'analytics', 'intelligence']
            if any(kw in job_title_lower for kw in data_keywords):
                max_score = 60
                matched_role = "roles relacionados con datos"
        
        # Generar razón
        if max_score >= 80:
            reason = f"Cargo coincide con '{matched_role}'"
        elif max_score >= 60:
            reason = f"Cargo relacionado con {matched_role}"
        else:
            reason = "Cargo no coincide directamente con roles deseados"
        
        return max_score, reason
    
    def _calculate_salary_match(
        self,
        profile_min_salary: int,
        job_salary_min: int,
        job_salary_max: int
    ) -> Tuple[int, str]:
        """
        Calcula match salarial.
        
        Returns:
            (score 0-100, explicación)
        """
        # Si no hay info de salario en la oferta
        if not job_salary_min and not job_salary_max:
            return 50, "Salario no especificado en la oferta"
        
        # Si no hay mínimo en perfil
        if not profile_min_salary:
            return 70, "Sin expectativa salarial definida"
        
        # Determinar salario ofrecido
        offered_salary = job_salary_max if job_salary_max else job_salary_min
        
        # Calcular diferencia porcentual
        if offered_salary >= profile_min_salary:
            # Oferta cumple o supera expectativa
            percentage_over = ((offered_salary - profile_min_salary) / profile_min_salary) * 100
            
            if percentage_over >= 20:
                score = 100
                reason = f"Salario supera expectativa en {int(percentage_over)}%"
            elif percentage_over >= 0:
                score = 90
                reason = "Salario cumple expectativa"
            else:
                score = 80
                reason = "Salario cercano a expectativa"
        else:
            # Oferta por debajo de expectativa
            percentage_below = ((profile_min_salary - offered_salary) / profile_min_salary) * 100
            
            if percentage_below <= 10:
                score = 70
                reason = f"Salario {int(percentage_below)}% bajo expectativa"
            elif percentage_below <= 20:
                score = 50
                reason = f"Salario {int(percentage_below)}% bajo expectativa"
            else:
                score = 20
                reason = f"Salario significativamente bajo expectativa ({int(percentage_below)}%)"
        
        return score, reason
    
    def _calculate_work_mode_match(
        self,
        preferred_modes: List[str],
        job_work_mode: str
    ) -> Tuple[int, str]:
        """
        Calcula match de modalidad de trabajo.
        
        Returns:
            (score 0-100, explicación)
        """
        if not preferred_modes or not job_work_mode:
            return 70, "Modalidad no especificada"
        
        # Normalizar
        preferred_lower = [m.lower() for m in preferred_modes]
        job_mode_lower = job_work_mode.lower()
        
        # Match directo
        if job_mode_lower in preferred_lower:
            return 100, f"Modalidad {job_work_mode} coincide con preferencia"
        
        # Casos especiales
        if 'remote' in preferred_lower and job_mode_lower == 'hybrid':
            return 80, "Híbrido parcialmente compatible con remoto"
        
        if 'hybrid' in preferred_lower and job_mode_lower == 'remote':
            return 90, "Remoto compatible con preferencia híbrida"
        
        return 40, f"Modalidad {job_work_mode} no coincide con preferencia"
    
    def get_top_matches(
        self, 
        profile: Dict, 
        jobs: List[Dict], 
        threshold: int = 60,
        limit: int = 20
    ) -> List[Tuple[Dict, int, Dict]]:
        """
        Encuentra las mejores ofertas para un perfil.
        
        Args:
            profile: Perfil del usuario
            jobs: Lista de ofertas
            threshold: Score mínimo para incluir (default 60)
            limit: Máximo de resultados (default 20)
            
        Returns:
            Lista de tuplas (job, score, reasons) ordenadas por score descendente
        """
        matches = []
        
        for job in jobs:
            score, reasons = self.calculate_match(profile, job)
            
            if score >= threshold:
                matches.append((job, score, reasons))
        
        # Ordenar por score descendente
        matches.sort(key=lambda x: x[1], reverse=True)
        
        return matches[:limit]


# Test
if __name__ == '__main__':
    matcher = JobMatcher()
    
    # Perfil de ejemplo
    profile = {
        'skills': ['Python', 'SQL', 'TensorFlow', 'Power BI'],
        'desired_roles': ['Data Scientist', 'Data Analyst'],
        'min_salary': 1_200_000,
        'work_modes': ['remote', 'hybrid']
    }
    
    # Oferta de ejemplo
    job = {
        'title': 'Data Scientist Senior',
        'required_skills': ['Python', 'SQL', 'Machine Learning'],
        'salary_min': 1_500_000,
        'salary_max': 2_000_000,
        'work_mode': 'hybrid'
    }
    
    score, reasons = matcher.calculate_match(profile, job)
    
    print(f"Match Score: {score}/100")
    print(f"\nComponent Scores:")
    for component, value in reasons['component_scores'].items():
        print(f"  {component}: {value}")
    
    print(f"\nExplanations:")
    for component, explanation in reasons['explanations'].items():
        print(f"  {component}: {explanation}")
