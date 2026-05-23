# Job Detector - Sistema de Detección Inteligente de Ofertas Laborales

Sistema automatizado que encuentra ofertas laborales relevantes para perfiles de Data Science en Chile.

## 🎯 Características

- ✅ **Sin login**: Acceso directo con link compartido
- ✅ **Parser automático de CV**: Sube tu CV y extrae tu perfil
- ✅ **Matching inteligente**: Score de compatibilidad 0-100
- ✅ **Fuentes configurables**: Agrega/edita fuentes fácilmente
- ✅ **Reportes semanales**: Email automático cada lunes
- ✅ **100% gratuito**: Hasta 1000 usuarios activos

## 🏗️ Arquitectura

```
Frontend (React + Vite)
    ↓
Vercel Serverless Functions
    ↓
Supabase (PostgreSQL)
    ↑
GitHub Actions (Scrapers cada 6h)
```

## 📋 Prerequisitos

### Para desarrollo:
- Node.js 18+
- Python 3.11+
- Git

### Cuentas gratuitas necesarias:
1. **GitHub** (código + CI/CD)
2. **Vercel** (hosting frontend + API)
3. **Supabase** (base de datos)
4. **Resend** (emails)

## 🚀 Setup Paso a Paso

### 1. Clonar repositorio

```bash
git clone <tu-repo>
cd job-detector-saas
```

### 2. Configurar Supabase

1. Crear cuenta en [supabase.com](https://supabase.com)
2. Crear nuevo proyecto
3. Ir a SQL Editor y ejecutar `database/schema.sql`
4. Copiar URL y API Key (Settings → API)

### 3. Configurar Variables de Entorno

Crear archivo `.env` en la raíz:

```env
# Supabase
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-anon-key

# Resend (para emails)
RESEND_API_KEY=re_tu_key
```

### 4. Setup Frontend

```bash
cd frontend
npm install
npm run dev
```

Abre http://localhost:5173

### 5. Setup Backend (scrapers locales)

```bash
cd backend
pip install -r requirements.txt

# Probar un scraper
python -m scrapers.empleos_publicos
```

### 6. Deploy a Vercel

1. Crear cuenta en [vercel.com](https://vercel.com)
2. Conectar tu repo de GitHub
3. Configurar variables de entorno en Vercel:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `RESEND_API_KEY`
4. Deploy automático al hacer push a `main`

### 7. Configurar GitHub Actions

1. Ir a Settings → Secrets en tu repo de GitHub
2. Agregar secrets:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `RESEND_API_KEY`
3. Los scrapers se ejecutarán automáticamente cada 6 horas

## 📝 Agregar Nueva Fuente de Empleos

### 1. Editar configuración

`shared/config/sources.json`:

```json
{
  "id": "nueva_fuente",
  "name": "Nueva Fuente Empleos",
  "url": "https://ejemplo.cl",
  "type": "scraper",
  "active": true,
  "scraper_file": "nueva_fuente.py"
}
```

### 2. Crear scraper

`backend/scrapers/nueva_fuente.py`:

```python
from .base_scraper import BaseScraper

class NuevaFuenteScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            source_id='nueva_fuente',
            source_name='Nueva Fuente',
            base_url='https://ejemplo.cl'
        )
    
    def scrape(self, keywords=None):
        # Tu lógica de scraping aquí
        jobs = []
        # ...
        return jobs
```

### 3. Registrar en runner

`backend/scrapers/run_all_scrapers.py`:

```python
from .nueva_fuente import NuevaFuenteScraper

# Agregar a la lista
scrapers = [
    EmpleosPublicosScraper(),
    NuevaFuenteScraper(),  # <-- Tu nuevo scraper
]
```

### 4. Commit y push

```bash
git add .
git commit -m "Add nueva fuente scraper"
git push
```

Los scrapers se actualizarán automáticamente.

## 🎨 Personalización

### Modificar criterios de matching

Editar `backend/matcher/job_matcher.py`:

```python
WEIGHTS = {
    'skills_match': 0.40,      # Ajustar pesos
    'role_match': 0.30,
    'salary_match': 0.20,
    'work_mode_match': 0.10
}
```

### Cambiar frecuencia de emails

Editar `.github/workflows/scrape-jobs.yml`:

```yaml
schedule:
  - cron: '0 */6 * * *'  # Cambiar frecuencia
```

## 📊 Monitoreo

### Ver logs de scrapers

1. GitHub Actions → Workflows → Run Job Scrapers
2. Click en última ejecución
3. Ver logs de cada paso

### Consultar base de datos

```sql
-- Ofertas por fuente
SELECT source_id, COUNT(*) 
FROM jobs 
WHERE is_active = true 
GROUP BY source_id;

-- Top matches de un usuario
SELECT * FROM user_top_matches 
WHERE email = 'usuario@example.com'
ORDER BY match_score DESC
LIMIT 10;
```

## 🔧 Troubleshooting

### Scraper falla

1. Verificar que el sitio no cambió su estructura HTML
2. Revisar logs en GitHub Actions
3. Probar scraper localmente:
   ```bash
   python -m scrapers.empleos_publicos
   ```

### No llegan emails

1. Verificar configuración de Resend
2. Revisar límite de 3000 emails/mes
3. Verificar que hay usuarios con `email_frequency='weekly'`

### Frontend no carga

1. Verificar variables de entorno en Vercel
2. Revisar logs de deployment
3. Probar localmente: `npm run dev`

## 📈 Escalamiento

### Si crece a >1000 usuarios:

1. **Vercel Pro**: $20/mes (builds ilimitados)
2. **Supabase Pro**: $25/mes (8GB DB)
3. **Resend Pro**: $20/mes (50k emails)

**Total: ~$65/mes** para miles de usuarios

## 🤝 Contribuir

Para agregar features o reportar bugs:

1. Fork del repo
2. Crear branch: `git checkout -b feature/nueva-feature`
3. Commit: `git commit -m 'Add nueva feature'`
4. Push: `git push origin feature/nueva-feature`
5. Crear Pull Request

## 📄 Licencia

MIT License - úsalo libremente

## 💬 Soporte

Para dudas o problemas:
- Crear Issue en GitHub
- Contactar a [tu-email]

---

**¡Listo para encontrar tu próximo trabajo en Data Science! 🚀**
