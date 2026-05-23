# 🚀 Guía Rápida de Inicio - Job Detector

## 📍 Dónde están los archivos

Los archivos están generados en: `/home/claude/job-detector-saas/`

## 📦 Qué hacer con ellos

### Paso 1: Descargar el proyecto

Todos los archivos están en la carpeta `/home/claude/job-detector-saas/`. Necesitas:

1. **Descargar todo el proyecto** a tu computador
2. O copiar los archivos a un repositorio de GitHub

### Paso 2: Configurar cuentas necesarias

Necesitas crear cuentas GRATUITAS en:

1. **GitHub** → github.com (para código y CI/CD)
2. **Supabase** → supabase.com (base de datos)
3. **Vercel** → vercel.com (hosting web)
4. **Resend** → resend.com (envío de emails)

### Paso 3: Configurar Supabase (Base de Datos)

1. Ve a supabase.com
2. Crea un nuevo proyecto
3. Ve a SQL Editor
4. Copia y pega el contenido de `database/schema.sql`
5. Ejecuta el script
6. Guarda tu URL y API Key (Settings → API)

### Paso 4: Configurar Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto (copia `.env.example`):

```bash
# Supabase
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Resend
RESEND_API_KEY=re_abc123...

# Frontend
VITE_SUPABASE_URL=https://tu-proyecto.supabase.co
VITE_SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Paso 5: Probar Localmente

#### Backend (Scrapers):

```bash
cd backend
pip install -r requirements.txt
python -m scrapers.empleos_publicos  # Probar un scraper
```

#### Frontend (Web App):

```bash
cd frontend
npm install
npm run dev
```

Abre http://localhost:5173

### Paso 6: Subir a GitHub

```bash
# Inicializar git
git init
git add .
git commit -m "Initial commit - Job Detector"

# Crear repo en github.com y luego:
git remote add origin https://github.com/TU-USUARIO/job-detector.git
git push -u origin main
```

### Paso 7: Deploy en Vercel

1. Ve a vercel.com
2. Click "Import Project"
3. Conecta tu repo de GitHub
4. Configura variables de entorno:
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_KEY`
5. Deploy!

Tu app estará en: `https://job-detector-tu-nombre.vercel.app`

### Paso 8: Configurar GitHub Actions (Scrapers Automáticos)

1. En tu repo de GitHub, ve a Settings → Secrets
2. Agrega:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `RESEND_API_KEY`

Los scrapers correrán automáticamente cada 6 horas.

## 🎯 Cómo usar la aplicación

1. Comparte el link de Vercel con tus colegas
2. Ellos suben su CV
3. El sistema extrae su perfil automáticamente
4. Cada 6 horas busca nuevas ofertas
5. Cada lunes les envía un reporte por email

## 🔧 Agregar nueva fuente de empleos

1. Edita `shared/config/sources.json`
2. Crea scraper en `backend/scrapers/nueva_fuente.py`
3. Usa `base_scraper.py` como template
4. Commit y push

¡Listo!

## 📊 Estructura del Proyecto

```
job-detector-saas/
├── frontend/              # Aplicación web (React)
│   ├── src/
│   │   ├── App.jsx       # Componente principal
│   │   └── main.jsx
│   └── package.json
│
├── backend/               # Scrapers y lógica
│   ├── scrapers/         # Buscadores de ofertas
│   ├── matcher/          # Sistema de matching
│   ├── email/            # Envío de reportes
│   └── api/              # Parser de CV
│
├── database/
│   └── schema.sql        # Base de datos
│
├── shared/
│   └── config/
│       └── sources.json  # Fuentes configurables
│
└── .github/
    └── workflows/        # Automatización
```

## ❓ Problemas Comunes

**"No puedo instalar dependencias Python"**
→ Asegúrate de tener Python 3.11+ instalado

**"Frontend no carga"**
→ Verifica que las variables VITE_* estén en Vercel

**"Scrapers no encuentran nada"**
→ Algunos sitios pueden haber cambiado su estructura HTML

**"No llegan emails"**
→ Verifica que configuraste Resend y el FROM_EMAIL

## 💡 Siguiente Pasos

Una vez funcionando:

1. Invita a tus 10 colegas
2. Monitorea logs en GitHub Actions
3. Ajusta fuentes según lo que encuentren útil
4. Personaliza el threshold de matching si es necesario

---

**¿Dudas?** Lee el README.md completo o revisa los comentarios en el código.
