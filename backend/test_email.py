import os
import asyncio
from mail_sender.report_generator import ReportGenerator
from mail_sender.send_weekly_reports import EmailSender

def test():
    generator = ReportGenerator()
    sender = EmailSender()

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
        }
    }

    matches = [
        (sample_job, 92, sample_reasons),
        (sample_job, 78, sample_reasons),
    ]

    html = generator.generate_weekly_report(
        user_name='Javiera Carrasco Gamboa',
        matches=matches,
        week_start='15 Ene 2025',
        week_end='22 Ene 2025'
    )

    sender._send_email(
        to='javiera.icgm@gmail.com',
        subject='[TEST] Nuevo diseño de compatibilidad',
        html=html
    )
    print("Correo enviado exitosamente a javiera.icgm@gmail.com")

if __name__ == '__main__':
    test()
