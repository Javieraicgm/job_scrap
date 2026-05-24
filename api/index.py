from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import tempfile
import requests
import os
import sys
from typing import Optional
from supabase import create_client
import resend

# Ajustar el path para poder importar los módulos de backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.api.cv_parser import CVParser
from backend.matcher.calculate_all_matches import MatchCalculator
from backend.scrapers.run_all_scrapers import ScraperRunner

app = FastAPI()

class ParseCVRequest(BaseModel):
    fileUrl: str

class CalculateMatchesRequest(BaseModel):
    profileId: str

class ScrapeNowRequest(BaseModel):
    profileId: Optional[str] = None

class ReportBugRequest(BaseModel):
    type: str
    description: str
    imageUrl: Optional[str] = None
    userEmail: str
    userName: str

@app.post("/api/parse-cv")
async def parse_cv(request: ParseCVRequest):
    file_url = request.fileUrl
    # Descargar el archivo temporalmente
    try:
        response = requests.get(file_url)
        response.raise_for_status()
        
        # Determinar la extensión
        ext = ".pdf" if ".pdf" in file_url.lower() else ".docx"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
            temp_file.write(response.content)
            temp_path = temp_file.name
            
        parser = CVParser()
        profile_data = parser.parse_cv(temp_path)
        
        # Eliminar archivo temporal
        os.remove(temp_path)
        
        return profile_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/calculate-matches")
async def calculate_matches(request: CalculateMatchesRequest):
    try:
        calculator = MatchCalculator()
        matches_found = calculator.calculate_for_profile(request.profileId)
        return {"success": True, "matches_found": matches_found}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scrape-now")
async def scrape_now(request: ScrapeNowRequest):
    try:
        runner = ScraperRunner()
        new_jobs = runner.run_all()
        
        matches_found = 0
        if request.profileId:
            calculator = MatchCalculator()
            matches_found = calculator.calculate_for_profile(request.profileId)
            
        return {"success": True, "new_jobs": new_jobs, "matches_updated": matches_found}
    except Exception as e:
        print(f"Error scrape_now: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/report-bug")
async def report_bug(request: ReportBugRequest):
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        resend.api_key = os.getenv("RESEND_API_KEY")
        
        # 1. Guardar en Supabase
        if supabase_url and supabase_key:
            supabase = create_client(supabase_url, supabase_key)
            supabase.table("bug_reports").insert({
                "type": request.type,
                "description": request.description,
                "image_url": request.imageUrl,
                "user_email": request.userEmail,
                "user_name": request.userName
            }).execute()

        # 2. Enviar email usando Resend
        if resend.api_key:
            from_email = os.getenv("FROM_EMAIL", "onboarding@resend.dev")
            to_email = os.getenv("ADMIN_EMAIL", "javiera.icgm@gmail.com")
            
            html_content = f"""
            <h2>Nuevo Reporte: {request.type.upper()}</h2>
            <p><strong>Usuario:</strong> {request.userName} ({request.userEmail})</p>
            <p><strong>Descripción:</strong></p>
            <p>{request.description}</p>
            """
            
            if request.imageUrl:
                html_content += f'<p><strong>Adjunto:</strong> <a href="{request.imageUrl}">Ver Imagen</a></p>'
                html_content += f'<img src="{request.imageUrl}" style="max-width: 500px;" />'

            resend.Emails.send({
                "from": from_email,
                "to": to_email, # Correo destino
                "subject": f"[{request.type.upper()}] Feedback de Antigravity",
                "html": html_content
            })
            
        return {"success": True}
    except Exception as e:
        print(f"Error report_bug: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
