"""
Report Generator
Crea reportes HTML atractivos para enviar por email
"""

from typing import List, Dict, Tuple
from datetime import datetime


class ReportGenerator:
    """Genera reportes HTML de ofertas laborales"""
    
    def generate_weekly_report(
        self, 
        user_name: str,
        matches: List[Tuple[Dict, int, Dict]],
        week_start: str,
        week_end: str
    ) -> str:
        """
        Genera reporte semanal HTML
        
        Args:
            user_name: Nombre del usuario
            matches: Lista de (job, score, reasons)
            week_start: Fecha inicio semana
            week_end: Fecha fin semana
            
        Returns:
            HTML string
        """
        
        # Calcular estadísticas
        total_jobs = len(matches)
        high_match = len([m for m in matches if m[1] >= 80])
        medium_match = len([m for m in matches if 60 <= m[1] < 80])
        
        # Generar HTML
        html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Job Detector - Reporte Semanal</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header {{
            border-bottom: 3px solid #2563eb;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        h1 {{
            color: #1e40af;
            margin: 0 0 10px 0;
        }}
        .period {{
            color: #6b7280;
            font-size: 14px;
        }}
        .stats {{
            display: flex;
            gap: 20px;
            margin: 20px 0;
            padding: 20px;
            background: #f0f9ff;
            border-radius: 6px;
        }}
        .stat {{
            flex: 1;
            text-align: center;
        }}
        .stat-number {{
            font-size: 32px;
            font-weight: bold;
            color: #2563eb;
        }}
        .stat-label {{
            font-size: 12px;
            color: #6b7280;
            text-transform: uppercase;
        }}
        .job-card {{
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            transition: all 0.2s;
        }}
        .job-card:hover {{
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border-color: #2563eb;
        }}
        .job-header {{
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 15px;
        }}
        .job-title {{
            font-size: 20px;
            font-weight: 600;
            color: #1e40af;
            margin: 0 0 5px 0;
        }}
        .job-company {{
            color: #6b7280;
            font-size: 14px;
        }}
        .match-badge {{
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 14px;
        }}
        .match-high {{
            background: #dcfce7;
            color: #166534;
        }}
        .match-medium {{
            background: #fef3c7;
            color: #92400e;
        }}
        .match-low {{
            background: #fee2e2;
            color: #991b1b;
        }}
        .job-details {{
            display: flex;
            gap: 20px;
            margin: 15px 0;
            font-size: 14px;
        }}
        .detail {{
            display: flex;
            align-items: center;
            gap: 5px;
            color: #6b7280;
        }}
        .detail-icon {{
            width: 16px;
            height: 16px;
        }}
        .match-reasons {{
            background: #f9fafb;
            padding: 15px;
            border-radius: 6px;
            margin: 15px 0;
        }}
        .reason-item {{
            margin: 5px 0;
            font-size: 14px;
            color: #4b5563;
        }}
        .apply-button {{
            display: inline-block;
            padding: 12px 24px;
            background: #2563eb;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 500;
            transition: background 0.2s;
        }}
        .apply-button:hover {{
            background: #1e40af;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
            text-align: center;
            color: #6b7280;
            font-size: 12px;
        }}
        .no-jobs {{
            text-align: center;
            padding: 40px;
            color: #6b7280;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Ofertas Laborales de la Semana</h1>
            <p class="period">Período: {week_start} - {week_end}</p>
            <p>Hola {user_name},</p>
            <p>Aquí están las mejores ofertas que encontramos para ti esta semana.</p>
        </div>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-number">{total_jobs}</div>
                <div class="stat-label">Ofertas Totales</div>
            </div>
            <div class="stat">
                <div class="stat-number">{high_match}</div>
                <div class="stat-label">Match Alto (80%+)</div>
            </div>
            <div class="stat">
                <div class="stat-number">{medium_match}</div>
                <div class="stat-label">Match Medio (60-80%)</div>
            </div>
        </div>
"""
        
        if not matches:
            html += """
        <div class="no-jobs">
            <h2>😔 No encontramos ofertas esta semana</h2>
            <p>Pero seguimos buscando. Te avisaremos cuando aparezca algo que coincida con tu perfil.</p>
        </div>
"""
        else:
            # Agregar cada oferta
            for job, score, reasons in matches[:10]:  # Top 10
                match_class = 'match-high' if score >= 80 else 'match-medium' if score >= 60 else 'match-low'
                match_label = '🟢 Alta compatibilidad' if score >= 80 else '🟡 Media compatibilidad' if score >= 60 else '🟠 Revisar'
                
                salary_text = ""
                if job.get('salary_min') or job.get('salary_max'):
                    if job.get('salary_min') and job.get('salary_max'):
                        salary_text = f"${job['salary_min']:,} - ${job['salary_max']:,}"
                    elif job.get('salary_min'):
                        salary_text = f"Desde ${job['salary_min']:,}"
                
                skills = ', '.join(job.get('required_skills', [])[:5])
                
                html += f"""
        <div class="job-card">
            <div class="job-header">
                <div>
                    <h2 class="job-title">{job.get('title', 'Sin título')}</h2>
                    <div class="job-company">{job.get('company', 'Empresa no especificada')}</div>
                </div>
                <div class="match-badge {match_class}">
                    {match_label} {score}%
                </div>
            </div>
            
            <div class="job-details">
                <div class="detail">
                    📍 {job.get('location', 'Chile')}
                </div>
                <div class="detail">
                    💼 {job.get('work_mode', 'No especificado').title()}
                </div>
                {f'<div class="detail">💰 {salary_text}</div>' if salary_text else ''}
            </div>
            
            {f'<div class="detail">🔧 {skills}</div>' if skills else ''}
            
            <div class="match-reasons">
                <strong>Por qué es un buen match:</strong>
"""
                
                # Agregar razones
                explanations = reasons.get('explanations', {})
                for key, explanation in explanations.items():
                    if explanation and isinstance(explanation, str):
                        html += f'<div class="reason-item">• {explanation}</div>'
                
                html += f"""
            </div>
            
            <a href="{job.get('url', '#')}" class="apply-button" target="_blank">
                Ver Oferta →
            </a>
        </div>
"""
        
        html += f"""
        <div class="footer">
            <p>Este reporte fue generado automáticamente por Job Detector</p>
            <p>Recibido: {datetime.now().strftime('%d/%m/%Y')}</p>
            <p style="margin-top: 15px; font-size: 11px;">¿No quieres recibir más correos? Puedes desuscribirte ingresando a la plataforma > Configuración > Frecuencia de Notificaciones > Desactivado.</p>
        </div>
    </div>
</body>
</html>
"""
        
        return html


# Test
if __name__ == '__main__':
    generator = ReportGenerator()
    
    # Datos de prueba
    sample_job = {
        'title': 'Data Scientist Senior',
        'company': 'TechCorp Chile',
        'location': 'Santiago (Remoto)',
        'work_mode': 'remote',
        'salary_min': 1_800_000,
        'salary_max': 2_500_000,
        'required_skills': ['Python', 'TensorFlow', 'SQL', 'AWS'],
        'url': 'https://ejemplo.cl/job/123'
    }
    
    sample_reasons = {
        'explanations': {
            'skills_match': 'Coincide en 3/4 skills: Python, TensorFlow, SQL',
            'role_match': 'Cargo coincide con Data Scientist',
            'salary_match': 'Salario supera expectativa en 50%',
            'work_mode_match': 'Modalidad remote coincide con preferencia'
        }
    }
    
    matches = [
        (sample_job, 92, sample_reasons),
        (sample_job, 78, sample_reasons),
    ]
    
    html = generator.generate_weekly_report(
        user_name='Juan Pérez',
        matches=matches,
        week_start='15 Ene 2025',
        week_end='22 Ene 2025'
    )
    
    # Guardar para preview
    with open('/tmp/report_preview.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("✅ Reporte generado en /tmp/report_preview.html")
