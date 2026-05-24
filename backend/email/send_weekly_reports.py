"""
Email Sender
Envía reportes semanales a usuarios usando Resend
"""

import os
from datetime import datetime, timedelta
from typing import List
import resend
from supabase import create_client, Client
from dotenv import load_dotenv

from .report_generator import ReportGenerator
import sys
sys.path.append('..')
from matcher.job_matcher import JobMatcher

load_dotenv()


class EmailSender:
    """Envía emails con reportes de ofertas"""
    
    def __init__(self):
        # Configurar Resend
        resend.api_key = os.getenv('RESEND_API_KEY')
        if not resend.api_key:
            raise ValueError("RESEND_API_KEY no configurado")
        
        # Configurar Supabase
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL y SUPABASE_KEY deben estar configurados")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.report_gen = ReportGenerator()
        self.matcher = JobMatcher()
        
        # Email de origen (debe estar verificado en Resend)
        self.from_email = os.getenv('FROM_EMAIL', 'jobdetector@resend.dev')
    
    def send_weekly_reports(self):
        """Envía reportes semanales a todos los usuarios activos"""
        
        print("📧 Iniciando envío de reportes semanales...")
        
        # Obtener usuarios que reciben reporte semanal
        users = self.supabase.table('profiles').select('*').eq(
            'email_frequency', 'weekly'
        ).execute()
        
        if not users.data:
            print("ℹ️  No hay usuarios con reportes semanales configurados")
            return
        
        print(f"👥 Encontrados {len(users.data)} usuarios")
        
        # Calcular período (última semana)
        today = datetime.now()
        week_start = (today - timedelta(days=7)).strftime('%d %b %Y')
        week_end = today.strftime('%d %b %Y')
        
        sent_count = 0
        error_count = 0
        
        for user in users.data:
            try:
                print(f"\n📤 Procesando: {user['email']}")
                
                # Obtener matches del usuario
                matches_data = self.supabase.table('job_matches').select(
                    '*, jobs(*)'
                ).eq('profile_id', user['id']).gte(
                    'match_score', user.get('alert_threshold', 70)
                ).order('match_score', desc=True).limit(20).execute()
                
                if not matches_data.data:
                    print(f"   ℹ️  Sin ofertas para este usuario")
                    continue
                
                # Formatear matches
                matches = []
                for match in matches_data.data:
                    job = match['jobs']
                    score = match['match_score']
                    reasons = match.get('match_reasons', {})
                    matches.append((job, score, reasons))
                
                # Generar reporte HTML
                html = self.report_gen.generate_weekly_report(
                    user_name=user.get('name', 'Usuario'),
                    matches=matches,
                    week_start=week_start,
                    week_end=week_end
                )
                
                # Enviar email
                self._send_email(
                    to=user['email'],
                    subject=f"🎯 {len(matches)} ofertas laborales para ti",
                    html=html
                )
                
                sent_count += 1
                print(f"   ✅ Email enviado ({len(matches)} ofertas)")
                
            except Exception as e:
                error_count += 1
                print(f"   ❌ Error: {e}")
        
        print(f"\n📊 Resumen:")
        print(f"   Enviados: {sent_count}")
        print(f"   Errores: {error_count}")
    
    def send_high_match_alert(self, user_email: str, job: dict, score: int):
        """
        Envía alerta inmediata cuando hay un match muy alto (>90%)
        
        Args:
            user_email: Email del usuario
            job: Datos de la oferta
            score: Score de match
        """
        
        html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .alert {{
            background: #dcfce7;
            border-left: 4px solid #16a34a;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .job-title {{
            font-size: 24px;
            color: #1e40af;
            margin: 10px 0;
        }}
        .score {{
            font-size: 36px;
            font-weight: bold;
            color: #16a34a;
        }}
        .button {{
            display: inline-block;
            padding: 12px 24px;
            background: #2563eb;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="alert">
        <h2>🎉 ¡Encontramos un match perfecto!</h2>
        <div class="score">{score}% de compatibilidad</div>
    </div>
    
    <h1 class="job-title">{job.get('title', 'Nueva oferta')}</h1>
    <p><strong>{job.get('company', 'Empresa')}</strong></p>
    <p>📍 {job.get('location', 'Chile')}</p>
    <p>💼 {job.get('work_mode', 'No especificado').title()}</p>
    
    <p>Esta oferta coincide casi perfectamente con tu perfil. ¡No la dejes pasar!</p>
    
    <a href="{job.get('url', '#')}" class="button">
        Ver Oferta Ahora →
    </a>
    
    <p style="color: #6b7280; font-size: 12px; margin-top: 40px;">
        Recibiste este email porque configuraste alertas para matches altos.<br>
        ¿No quieres recibir más correos? Puedes desuscribirte ingresando a la plataforma > Configuración > Frecuencia de Notificaciones > Desactivado.
    </p>
</body>
</html>
"""
        
        self._send_email(
            to=user_email,
            subject=f"🎉 Match {score}%: {job.get('title', 'Nueva oferta')}",
            html=html
        )
    
    def _send_email(self, to: str, subject: str, html: str):
        """Envía un email usando Resend"""
        
        params = {
            "from": self.from_email,
            "to": [to],
            "subject": subject,
            "html": html
        }
        
        try:
            email = resend.Emails.send(params)
            return email
        except Exception as e:
            raise Exception(f"Error enviando email: {e}")


if __name__ == '__main__':
    print("=" * 60)
    print("📧 Job Detector - Email Sender")
    print("=" * 60)
    
    sender = EmailSender()
    sender.send_weekly_reports()
