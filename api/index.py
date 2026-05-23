from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import tempfile
import requests
import os
import sys

# Ajustar el path para poder importar los módulos de backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.api.cv_parser import CVParser
from backend.matcher.calculate_all_matches import MatchCalculator

app = FastAPI()

class ParseCVRequest(BaseModel):
    fileUrl: str

class CalculateMatchesRequest(BaseModel):
    profileId: str

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
