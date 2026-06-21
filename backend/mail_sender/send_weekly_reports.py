"""
Email Sender
Envía reportes semanales a usuarios usando Resend
"""

import os
from datetime import datetime, timedelta
from typing import List
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from supabase import create_client, Client
from dotenv import load_dotenv

from .report_generator import ReportGenerator
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from backend.matcher.job_matcher import JobMatcher

load_dotenv()


class EmailSender:
    """Envía emails con reportes de ofertas"""
    
    def __init__(self):
        # Configurar SMTP (Gmail)
        self.smtp_email = os.getenv('SMTP_USER') or os.getenv('SMTP_EMAIL')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        
        if not self.smtp_email or not self.smtp_password:
            raise ValueError("SMTP_USER/SMTP_EMAIL y SMTP_PASSWORD deben estar configurados en .env")
        
        # Configurar Supabase
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', os.getenv('SUPABASE_KEY'))
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL y SUPABASE_KEY deben estar configurados")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.report_gen = ReportGenerator()
        self.matcher = JobMatcher()
        
        # Email de origen
        self.from_email = self.smtp_email
    
    def send_weekly_reports(self):
        """Envía reportes semanales a todos los usuarios activos"""
        
        print("📧 Iniciando envío de reportes semanales...")
        
        # Obtener usuarios que reciben reporte semanal
        users = self.supabase.table('profiles').select('*').eq(
            'email_frequency', 'weekly'
        ).execute()
        
        if not users.data:
            print("No hay usuarios con reportes semanales configurados")
            return
        
        print(f"[INFO] Encontrados {len(users.data)} perfiles con alertas activas.")
        
        # Calcular período (última semana)
        today = datetime.now()
        week_start = (today - timedelta(days=7)).strftime('%d %b %Y')
        week_end = today.strftime('%d %b %Y')
        
        sent_count = 0
        error_count = 0
        
        for user in users.data:
            try:
                print(f"\nProcesando: {user['email']}")
                
                # Filtrar jobs guardados en la última semana
                last_week_iso = (today - timedelta(days=7)).isoformat()
                
                # Obtener matches del usuario (solo los nuevos de esta semana)
                matches_data = self.supabase.table('job_matches').select(
                    '*, jobs!inner(*)'
                ).eq('profile_id', user['id']).gte(
                    'match_score', user.get('alert_threshold', 60)
                ).gte('created_at', last_week_iso).order('match_score', desc=True).limit(200).execute()
                
                if not matches_data.data:
                    print(f"   Sin ofertas para este usuario")
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
                    subject=f"{len(matches)} ofertas laborales para ti",
                    html=html
                )
                
                sent_count += 1
                print(f"   Email enviado ({len(matches)} ofertas)")
                
            except Exception as e:
                error_count += 1
                print(f"   Error: {e}")
        
        print(f"\nResumen:")
        print(f"\n[INFO] Enviando reportes...: {sent_count}")
        print(f"   Errores: {error_count}")
        
    def send_report_for_profile(self, profile_id: str) -> bool:
        """Envía reporte a un solo usuario (ej. para onboarding o consulta express)"""
        user_res = self.supabase.table('profiles').select('*').eq('id', profile_id).single().execute()
        if not user_res.data:
            return False
            
        user = user_res.data
        today = datetime.now()
        week_start = (today - timedelta(days=7)).strftime('%d %b %Y')
        week_end = today.strftime('%d %b %Y')
        
        last_week_iso = (today - timedelta(days=7)).isoformat()
        
        matches_data = self.supabase.table('job_matches').select(
            '*, jobs!inner(*)'
        ).eq('profile_id', user['id']).gte(
            'match_score', user.get('alert_threshold', 60)
        ).order('match_score', desc=True).limit(200).execute()
        
        if not matches_data.data:
            return False
            
        matches = []
        for match in matches_data.data:
            matches.append((match['jobs'], match['match_score'], match.get('match_reasons', {})))
            
        html = self.report_gen.generate_weekly_report(
            user_name=user.get('name', 'Usuario'),
            matches=matches,
            week_start=week_start,
            week_end=week_end
        )
        
        return self._send_email(
            to=user['email'],
            subject=f"🎯 ¡Tus ofertas express están listas! ({len(matches)} matches)",
            html=html
        )
    
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
        """Envía un email usando Gmail SMTP"""
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"Job Detector <{self.from_email}>"
        msg['To'] = to
        
        # Adjuntar HTML
        html_part = MIMEText(html, 'html')
        msg.attach(html_part)
        
        try:
            # Conectar a Gmail SMTP en puerto 465 (SSL)
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.smtp_email, self.smtp_password)
                server.sendmail(self.from_email, to, msg.as_string())
                
            return True
        except Exception as e:
            raise Exception(f"Error enviando email: {e}")


if __name__ == '__main__':
    print("=" * 60)
    print("Job Detector - Email Sender")
    print("=" * 60)
    
    sender = EmailSender()
    sender.send_weekly_reports()
