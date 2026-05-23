-- Schema para Job Detector (Supabase PostgreSQL)

-- Tabla de perfiles de usuarios
CREATE TABLE profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  cv_file_url TEXT,
  
  -- Datos extraídos del CV
  skills TEXT[], -- Array de skills: ["Python", "SQL", "TensorFlow"]
  desired_roles TEXT[], -- ["Data Scientist", "Data Analyst"]
  years_experience INTEGER,
  education_level TEXT,
  
  -- Preferencias de búsqueda
  min_salary INTEGER, -- En pesos chilenos
  max_salary INTEGER,
  work_modes TEXT[], -- ["remote", "hybrid", "onsite"]
  preferred_locations TEXT[], -- ["Santiago", "Valparaíso", "Remoto"]
  
  -- Configuración de alertas
  email_frequency TEXT DEFAULT 'weekly', -- daily, weekly, biweekly
  alert_threshold INTEGER DEFAULT 70, -- Enviar solo matches >70%
  
  -- Metadata
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_login TIMESTAMP WITH TIME ZONE
);

-- Tabla de ofertas laborales
CREATE TABLE jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- Identificación
  source_id TEXT NOT NULL, -- De sources.json
  external_id TEXT, -- ID en la fuente original
  url TEXT UNIQUE NOT NULL,
  
  -- Información básica
  title TEXT NOT NULL,
  company TEXT,
  description TEXT,
  requirements TEXT,
  
  -- Detalles
  salary_min INTEGER,
  salary_max INTEGER,
  salary_currency TEXT DEFAULT 'CLP',
  work_mode TEXT, -- remote, hybrid, onsite
  location TEXT,
  contract_type TEXT, -- full_time, part_time, contract, internship
  
  -- Skills detectados
  required_skills TEXT[],
  nice_to_have_skills TEXT[],
  
  -- Fechas
  posted_date DATE,
  deadline_date DATE,
  scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  -- Metadata
  raw_data JSONB, -- Datos completos del scraper
  is_active BOOLEAN DEFAULT TRUE,
  
  UNIQUE(source_id, external_id)
);

-- Tabla de matches (precalculados)
CREATE TABLE job_matches (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
  job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
  
  -- Scoring
  match_score INTEGER NOT NULL, -- 0-100
  match_reasons JSONB, -- {"skills_match": 85, "salary_match": 90, ...}
  
  -- Estado
  is_favorite BOOLEAN DEFAULT FALSE,
  is_viewed BOOLEAN DEFAULT FALSE,
  is_applied BOOLEAN DEFAULT FALSE,
  
  -- Metadata
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  UNIQUE(profile_id, job_id)
);

-- Tabla de scrapers (estado)
CREATE TABLE scraper_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_id TEXT NOT NULL,
  
  -- Resultados
  status TEXT NOT NULL, -- success, failed, partial
  jobs_found INTEGER DEFAULT 0,
  new_jobs INTEGER DEFAULT 0,
  errors TEXT[],
  
  -- Timing
  started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  finished_at TIMESTAMP WITH TIME ZONE,
  duration_seconds INTEGER,
  
  -- Metadata
  scraper_version TEXT,
  run_metadata JSONB
);

-- Índices para performance
CREATE INDEX idx_jobs_source ON jobs(source_id);
CREATE INDEX idx_jobs_posted_date ON jobs(posted_date DESC);
CREATE INDEX idx_jobs_active ON jobs(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_jobs_skills ON jobs USING GIN(required_skills);
CREATE INDEX idx_matches_profile ON job_matches(profile_id);
CREATE INDEX idx_matches_score ON job_matches(match_score DESC);

-- Función para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Vista para obtener top matches de un usuario
CREATE VIEW user_top_matches AS
SELECT 
  p.email,
  p.name,
  j.title,
  j.company,
  j.url,
  j.salary_min,
  j.salary_max,
  j.work_mode,
  j.location,
  jm.match_score,
  jm.match_reasons,
  jm.is_favorite,
  jm.is_viewed,
  j.posted_date,
  j.deadline_date
FROM job_matches jm
JOIN profiles p ON jm.profile_id = p.id
JOIN jobs j ON jm.job_id = j.id
WHERE j.is_active = TRUE
ORDER BY jm.match_score DESC;

-- Función para limpiar ofertas antiguas (>90 días)
CREATE OR REPLACE FUNCTION cleanup_old_jobs()
RETURNS void AS $$
BEGIN
  UPDATE jobs 
  SET is_active = FALSE 
  WHERE posted_date < NOW() - INTERVAL '90 days'
    AND is_active = TRUE;
END;
$$ LANGUAGE plpgsql;
