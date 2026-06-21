"""
Calculate Matches
Calcula scores de matching entre todos los perfiles y ofertas activas
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv
from .job_matcher import JobMatcher

load_dotenv()


class MatchCalculator:
    """Calcula y guarda matches en DB"""
    
    def __init__(self):
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL y SUPABASE_KEY deben estar configurados")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.matcher = JobMatcher()
    
    def calculate_all_matches(self):
        """Calcula matches para todos los perfiles contra todas las ofertas activas"""
        
        print("Calculando matches...")
        
        # Obtener todos los perfiles
        profiles = self.supabase.table('profiles').select('*').execute()
        
        if not profiles.data:
            print("No hay perfiles registrados")
            return
        
        # Obtener todas las ofertas activas
        jobs = self.supabase.table('jobs').select('*').eq('is_active', True).execute()
        
        if not jobs.data:
            print("No hay ofertas activas")
            return
        
        print(f"{len(profiles.data)} perfiles")
        print(f"{len(jobs.data)} ofertas activas")
        
        total_matches = 0
        
        for profile in profiles.data:
            print(f"\nProcesando perfil: {profile.get('email', profile['id'])}")
            
            matches_for_profile = 0
            
            for job in jobs.data:
                # Calcular match
                score, reasons = self.matcher.calculate_match(profile, job)
                
                # Solo guardar si supera threshold mínimo
                threshold = profile.get('alert_threshold', 60)
                
                # Regla especial: LinkedIn requiere 90+ por su alto volumen
                if job.get('source', '').lower() == 'linkedin':
                    threshold = max(threshold, 90)
                
                if score >= threshold:
                    # Guardar o actualizar match
                    self._upsert_match(
                        profile_id=profile['id'],
                        job_id=job['id'],
                        score=score,
                        reasons=reasons
                    )
                    matches_for_profile += 1
            
            print(f"   {matches_for_profile} matches encontrados")
            total_matches += matches_for_profile
        
        print(f"\nTotal matches calculados: {total_matches}")
        return total_matches
    
    def calculate_for_profile(self, profile_id: str):
        """Calcula matches para un perfil específico"""
        
        # Obtener perfil
        profile = self.supabase.table('profiles').select('*').eq(
            'id', profile_id
        ).single().execute()
        
        if not profile.data:
            raise ValueError(f"Perfil {profile_id} no encontrado")
        
        # Obtener ofertas activas
        jobs = self.supabase.table('jobs').select('*').eq('is_active', True).execute()
        
        matches_count = 0
        
        for job in jobs.data:
            score, reasons = self.matcher.calculate_match(profile.data, job)
            
            threshold = profile.data.get('alert_threshold', 60)
            
            # Regla especial: LinkedIn requiere 90+ por su alto volumen
            if job.get('source', '').lower() == 'linkedin':
                threshold = max(threshold, 90)
            
            if score >= threshold:
                self._upsert_match(
                    profile_id=profile_id,
                    job_id=job['id'],
                    score=score,
                    reasons=reasons
                )
                matches_count += 1
        
        return matches_count
    
    def _upsert_match(self, profile_id: str, job_id: str, score: int, reasons: dict):
        """Inserta o actualiza un match"""
        
        try:
            # Intentar insertar
            self.supabase.table('job_matches').insert({
                'profile_id': profile_id,
                'job_id': job_id,
                'match_score': score,
                'match_reasons': reasons
            }).execute()
            
        except Exception as e:
            # Si ya existe, actualizar
            if 'duplicate' in str(e).lower() or 'unique' in str(e).lower():
                self.supabase.table('job_matches').update({
                    'match_score': score,
                    'match_reasons': reasons
                }).eq('profile_id', profile_id).eq('job_id', job_id).execute()


if __name__ == '__main__':
    print("=" * 60)
    print("Job Detector - Match Calculator")
    print("=" * 60)
    
    calculator = MatchCalculator()
    calculator.calculate_all_matches()
