import React, { useState, useEffect } from 'react';
import { createClient } from '@supabase/supabase-js';
import { 
  Upload, Briefcase, Settings, Mail, 
  CheckCircle2, FileText, MapPin, DollarSign, 
  ExternalLink, Edit2, Save, X, Search, Check, Info, AlertCircle
} from 'lucide-react';
import AboutSection from './components/AboutSection';

// Inicializar Supabase
const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_KEY
);

function App() {
  const [activeTab, setActiveTab] = useState('upload');
  const [profile, setProfile] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);

  // Cargar perfil del localStorage (sin login)
  useEffect(() => {
    const savedProfile = localStorage.getItem('jobDetectorProfile');
    if (savedProfile) {
      const profileData = JSON.parse(savedProfile);
      setProfile(profileData);
      loadJobs(profileData.id);
    }
  }, []);

  const handleCVUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setLoading(true);

    try {
      // Subir CV a Supabase Storage
      const fileName = `${Date.now()}_${file.name}`;
      const { data: uploadData, error: uploadError } = await supabase
        .storage
        .from('cvs')
        .upload(fileName, file);

      if (uploadError) throw uploadError;

      // Obtener URL pública
      const { data: urlData } = supabase
        .storage
        .from('cvs')
        .getPublicUrl(fileName);

      // Parsear CV (llamada a API)
      const response = await fetch('/api/parse-cv', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fileUrl: urlData.publicUrl })
      });

      const parsedProfile = await response.json();

      // Guardar perfil en DB
      const { data: profileData, error: profileError } = await supabase
        .from('profiles')
        .upsert([{
          ...parsedProfile,
          cv_file_url: urlData.publicUrl
        }], { onConflict: 'email' })
        .select()
        .single();

      if (profileError) throw profileError;

      // Guardar en localStorage
      localStorage.setItem('jobDetectorProfile', JSON.stringify(profileData));
      setProfile(profileData);
      
      // Calcular matches iniciales
      await calculateMatches(profileData.id);
      
      setActiveTab('jobs');

    } catch (error) {
      console.error('Error:', error);
      alert('Error procesando CV: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const calculateMatches = async (profileId) => {
    // Llamar a API para calcular matches
    await fetch('/api/calculate-matches', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ profileId })
    });

    loadJobs(profileId);
  };

  const loadJobs = async (profileId) => {
    const { data, error } = await supabase
      .from('job_matches')
      .select('*, jobs(*)')
      .eq('profile_id', profileId)
      .order('match_score', { ascending: false })
      .limit(20);

    if (!error) {
      setJobs(data);
    }
  };

  const updateProfile = async (updates) => {
    if (!profile) return;

    const { error } = await supabase
      .from('profiles')
      .update(updates)
      .eq('id', profile.id);

    if (!error) {
      const updatedProfile = { ...profile, ...updates };
      setProfile(updatedProfile);
      localStorage.setItem('jobDetectorProfile', JSON.stringify(updatedProfile));
      await calculateMatches(profile.id);
    } else {
      alert('Error al actualizar el perfil: ' + error.message);
    }
  };

  return (
    <div className="min-h-screen text-gray-100 font-sans">
      {/* Header Premium Glassmorphism */}
      <header className="sticky top-0 z-50 glass-panel border-b-0 border-white/10 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-5 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-rose-900/40 rounded-xl border border-rose-500/30">
                <Search className="text-rose-400" size={24} />
              </div>
              <h1 className="text-2xl font-bold text-gray-100 tracking-tight wine-glow">
                Job Detector
              </h1>
            </div>
            {profile && (
              <div className="text-sm font-medium px-4 py-2 bg-white/5 rounded-full border border-white/10 text-gray-300 flex items-center space-x-2">
                <Mail size={14} className="text-rose-400" />
                <span>{profile.email}</span>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8">
        <div className="flex space-x-2 p-1 bg-black/20 backdrop-blur-md rounded-2xl w-fit border border-white/5">
          <TabButton
            active={activeTab === 'upload'}
            onClick={() => setActiveTab('upload')}
            icon={<Upload size={18} />}
            label="Subir CV"
          />
          <TabButton
            active={activeTab === 'jobs'}
            onClick={() => setActiveTab('jobs')}
            icon={<Briefcase size={18} />}
            label="Ofertas"
            disabled={!profile}
          />
          <TabButton
            active={activeTab === 'settings'}
            onClick={() => setActiveTab('settings')}
            icon={<Settings size={18} />}
            label="Ajustes"
            disabled={!profile}
          />
          <button 
            className={`flex items-center space-x-2 px-5 py-2.5 rounded-xl font-medium text-sm transition-all duration-300 ${activeTab === 'about' ? 'bg-rose-900/80 text-rose-100 shadow-lg border border-rose-500/30' : 'text-gray-400 hover:text-gray-200 hover:bg-white/5 border border-transparent'}`}
            onClick={() => setActiveTab('about')}
          >
            <Info size={18} />
            <span>Soporte</span>
          </button>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-10 sm:px-6 lg:px-8">
        {activeTab === 'upload' && (
          <UploadTab
            profile={profile}
            loading={loading}
            onUpload={handleCVUpload}
            onUpdate={updateProfile}
          />
        )}

        {activeTab === 'jobs' && profile && (
          <JobsTab
            jobs={jobs}
            profile={profile}
            onRefresh={() => loadJobs(profile.id)}
          />
        )}

        {activeTab === 'settings' && profile && (
          <SettingsTab
            profile={profile}
            onUpdate={updateProfile}
          />
        )}

        {activeTab === 'about' && <AboutSection />}
      </main>
    </div>
  );
}

// Componentes auxiliares

function TabButton({ active, onClick, icon, label, disabled }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`
        flex items-center space-x-2 px-5 py-2.5 rounded-xl font-medium text-sm transition-all duration-300
        ${active
          ? 'bg-rose-900/80 text-rose-100 shadow-lg border border-rose-500/30'
          : 'text-gray-400 hover:text-gray-200 hover:bg-white/5 border border-transparent'
        }
        ${disabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'}
      `}
    >
      {icon}
      <span>{label}</span>
    </button>
  );
}

function UploadTab({ profile, loading, onUpload, onUpdate }) {
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({});

  const handleEditClick = () => {
    setEditForm({
      name: profile.name || '',
      email: profile.email || '',
      phone: profile.phone || '',
      skills: profile.skills ? profile.skills.join(', ') : '',
      desired_roles: profile.desired_roles ? profile.desired_roles.join(', ') : ''
    });
    setIsEditing(true);
  };

  const handleSaveClick = () => {
    onUpdate({
      name: editForm.name,
      email: editForm.email,
      phone: editForm.phone,
      skills: editForm.skills.split(',').map(s => s.trim()).filter(Boolean),
      desired_roles: editForm.desired_roles.split(',').map(s => s.trim()).filter(Boolean)
    });
    setIsEditing(false);
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="glass-panel rounded-3xl p-10 relative overflow-hidden">
        {/* Glow effect background */}
        <div className="absolute -top-20 -right-20 w-64 h-64 bg-rose-900/20 rounded-full blur-3xl pointer-events-none"></div>
        <div className="absolute -bottom-20 -left-20 w-64 h-64 bg-blue-900/20 rounded-full blur-3xl pointer-events-none"></div>

        <h2 className="text-3xl font-bold mb-8 text-white relative z-10 flex items-center">
          {profile ? <CheckCircle2 className="mr-3 text-rose-500" size={32}/> : <FileText className="mr-3 text-rose-500" size={32}/>}
          {profile ? 'CV Analizado con Éxito' : 'Análisis de Perfil'}
        </h2>
        
        {profile ? (
          <div className="space-y-6 relative z-10">
            <div className="bg-white/5 border border-white/10 rounded-xl p-4 text-sm text-gray-300">
              <p>Tu perfil ha sido extraído y optimizado por nuestro motor de IA.</p>
              <p className="mt-2 text-rose-300"><strong>Tip:</strong> Se puede editar la información extraída haciendo clic en "Editar". Te recomendamos agregar o ajustar manualmente tus habilidades técnicas y roles de interés.</p>
            </div>
            
            <div className="bg-black/30 p-8 rounded-2xl border border-white/5">
              {!isEditing ? (
                <>
                  <div className="flex justify-between items-center mb-6 border-b border-white/10 pb-4">
                    <h3 className="font-semibold text-xl text-rose-400">Resumen Extraído</h3>
                    <button 
                      onClick={handleEditClick}
                      className="flex items-center space-x-2 px-4 py-2 bg-white/5 text-gray-300 rounded-lg text-sm font-medium hover:bg-white/10 hover:text-white transition border border-white/5"
                    >
                      <Edit2 size={14} />
                      <span>Editar</span>
                    </button>
                  </div>
                  <ul className="space-y-4 text-gray-300">
                    {profile.name && (
                      <li className="flex flex-col"><span className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-1">Nombre Completo</span> <span className="text-lg text-white">{profile.name}</span></li>
                    )}
                    {profile.email && (
                      <li className="flex flex-col"><span className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-1">Correo Electrónico</span> <span className="text-gray-200">{profile.email}</span></li>
                    )}
                    {profile.phone && (
                      <li className="flex flex-col"><span className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-1">Teléfono</span> <span className="text-gray-200">{profile.phone}</span></li>
                    )}
                    {profile.skills && (
                      <li className="flex flex-col pt-2">
                        <span className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-2">Habilidades Técnicas</span> 
                        <div className="flex flex-wrap gap-2">
                          {profile.skills.map(s => <span key={s} className="px-3 py-1 bg-rose-900/30 text-rose-200 rounded-full text-xs border border-rose-800/50">{s}</span>)}
                        </div>
                      </li>
                    )}
                    {profile.desired_roles && (
                      <li className="flex flex-col pt-2">
                        <span className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-2">Roles Identificados</span> 
                        <div className="flex flex-wrap gap-2">
                          {profile.desired_roles.map(r => <span key={r} className="px-3 py-1 bg-white/10 text-gray-200 rounded-full text-xs border border-white/10">{r}</span>)}
                        </div>
                      </li>
                    )}
                  </ul>
                </>
              ) : (
                <div className="space-y-5">
                  <div className="flex justify-between items-center mb-4 border-b border-white/10 pb-4">
                    <h3 className="font-semibold text-xl text-rose-400">Modo Edición</h3>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Nombre</label>
                    <input 
                      type="text" 
                      value={editForm.name} 
                      onChange={e => setEditForm({...editForm, name: e.target.value})}
                      className="w-full px-4 py-3 bg-black/40 border border-white/10 rounded-xl text-white focus:ring-2 focus:ring-rose-500/50 focus:border-rose-500 transition outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Email</label>
                    <input 
                      type="email" 
                      value={editForm.email} 
                      onChange={e => setEditForm({...editForm, email: e.target.value})}
                      className="w-full px-4 py-3 bg-black/40 border border-white/10 rounded-xl text-white focus:ring-2 focus:ring-rose-500/50 focus:border-rose-500 transition outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Teléfono</label>
                    <input 
                      type="text" 
                      value={editForm.phone} 
                      onChange={e => setEditForm({...editForm, phone: e.target.value})}
                      className="w-full px-4 py-3 bg-black/40 border border-white/10 rounded-xl text-white focus:ring-2 focus:ring-rose-500/50 focus:border-rose-500 transition outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Habilidades (separadas por coma)</label>
                    <textarea 
                      value={editForm.skills} 
                      onChange={e => setEditForm({...editForm, skills: e.target.value})}
                      className="w-full px-4 py-3 bg-black/40 border border-white/10 rounded-xl text-white focus:ring-2 focus:ring-rose-500/50 focus:border-rose-500 transition outline-none"
                      rows={3}
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Roles (separados por coma)</label>
                    <input 
                      type="text" 
                      value={editForm.desired_roles} 
                      onChange={e => setEditForm({...editForm, desired_roles: e.target.value})}
                      className="w-full px-4 py-3 bg-black/40 border border-white/10 rounded-xl text-white focus:ring-2 focus:ring-rose-500/50 focus:border-rose-500 transition outline-none"
                    />
                  </div>
                  <div className="flex space-x-3 pt-4 border-t border-white/10">
                    <button 
                      onClick={handleSaveClick}
                      className="flex-1 flex justify-center items-center space-x-2 px-6 py-3 bg-gradient-to-r from-rose-700 to-rose-600 text-white rounded-xl font-semibold hover:from-rose-600 hover:to-rose-500 transition-all shadow-lg"
                    >
                      <Save size={18} />
                      <span>Guardar Perfil</span>
                    </button>
                    <button 
                      onClick={() => setIsEditing(false)}
                      className="flex-1 flex justify-center items-center space-x-2 px-6 py-3 bg-white/5 text-gray-300 rounded-xl font-semibold hover:bg-white/10 hover:text-white transition-all border border-white/10"
                    >
                      <X size={18} />
                      <span>Descartar</span>
                    </button>
                  </div>
                </div>
              )}
            </div>

            <button
              onClick={() => {
                if (confirm('¿Quieres subir un nuevo CV? Esto reemplazará tu perfil actual de forma permanente.')) {
                  localStorage.removeItem('jobDetectorProfile');
                  window.location.reload();
                }
              }}
              className="text-gray-400 hover:text-rose-400 text-sm mt-6 inline-flex items-center transition-colors duration-200"
            >
              ← Procesar un documento diferente
            </button>
          </div>
        ) : (
          <div className="relative z-10">
            <p className="text-gray-300 mb-10 text-lg leading-relaxed">
              Nuestro motor de análisis extraerá automáticamente tus habilidades técnicas, experiencia y perfil profesional para conectarte con las mejores oportunidades del mercado.
            </p>

            <div className="border-2 border-dashed border-white/20 rounded-3xl p-16 text-center hover:border-rose-500/50 hover:bg-white/5 transition-all duration-300 group">
              <input
                type="file"
                accept=".pdf,.docx"
                onChange={onUpload}
                disabled={loading}
                className="hidden"
                id="cv-upload"
              />
              <label htmlFor="cv-upload" className="cursor-pointer flex flex-col items-center">
                <div className="w-20 h-20 bg-black/40 rounded-full flex items-center justify-center mb-6 group-hover:scale-110 group-hover:bg-rose-900/30 transition-all duration-300 border border-white/5 group-hover:border-rose-500/30">
                  <Upload className={`h-8 w-8 ${loading ? 'text-rose-500 animate-bounce' : 'text-gray-400 group-hover:text-rose-400'}`} />
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">
                  {loading ? 'Analizando Documento...' : 'Selecciona tu CV'}
                </h3>
                <p className="text-sm text-gray-500">
                  Soporte para PDF o DOCX (Máx. 5MB)
                </p>
              </label>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function JobsTab({ jobs, profile, onRefresh }) {
  const [isScraping, setIsScraping] = useState(false);
  const [scrapeResult, setScrapeResult] = useState(null);

  const handleExpressSearch = async () => {
    setIsScraping(true);
    setScrapeResult(null);
    try {
      const response = await fetch('/api/scrape-now', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profileId: profile.id })
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Error al ejecutar la búsqueda');
      }
      
      setScrapeResult({ success: true, newJobs: data.new_jobs });
      if (onRefresh) onRefresh();
      
      // Ocultar mensaje de éxito después de 8 segundos
      setTimeout(() => setScrapeResult(null), 8000);
    } catch (error) {
      console.error('Error in express search:', error);
      setScrapeResult({ success: false, error: error.message });
    } finally {
      setIsScraping(false);
    }
  };
  if (!jobs || jobs.length === 0) {
    return (
      <div className="glass-panel max-w-3xl mx-auto text-center py-20 rounded-3xl">
        <div className="w-24 h-24 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-6">
          <Briefcase className="h-10 w-10 text-gray-500" />
        </div>
        <h3 className="text-2xl font-bold text-white mb-3">No hay ofertas disponibles</h3>
        <p className="text-gray-400 max-w-md mx-auto mb-8">
          El sistema está analizando el mercado. Nuestros recolectores actualizan la base de datos cada 6 horas.
        </p>

        <button
          onClick={handleExpressSearch}
          disabled={isScraping}
          className={`mx-auto flex items-center space-x-2 px-6 py-3 rounded-full font-medium transition ${
            isScraping 
              ? 'bg-rose-900/40 text-rose-300 cursor-wait border border-rose-500/30' 
              : 'bg-gradient-to-r from-rose-500 to-rose-700 hover:from-rose-400 hover:to-rose-600 text-white shadow-lg shadow-rose-900/50'
          }`}
        >
          {isScraping ? (
            <>
              <div className="w-5 h-5 border-2 border-rose-300 border-t-transparent rounded-full animate-spin"></div>
              <span>Buscando en la web (puede tardar 60s)...</span>
            </>
          ) : (
            <>
              <Search size={18} />
              <span>Búsqueda Express Ahora</span>
            </>
          )}
        </button>
        
        {scrapeResult && scrapeResult.success && (
          <div className="mt-6 inline-flex items-center space-x-2 px-4 py-2 bg-green-900/30 text-green-400 rounded-lg border border-green-500/30">
            <CheckCircle2 size={18} />
            <span>¡Búsqueda completada! Se encontraron {scrapeResult.newJobs} ofertas nuevas.</span>
          </div>
        )}
        {scrapeResult && !scrapeResult.success && (
          <div className="mt-6 inline-flex items-center space-x-2 px-4 py-2 bg-red-900/30 text-red-400 rounded-lg border border-red-500/30">
            <AlertCircle size={18} />
            <span>Error: {scrapeResult.error}</span>
          </div>
        )}

      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-8 border-b border-white/10 pb-6 gap-4">
        <div>
          <h2 className="text-3xl font-bold text-white wine-glow mb-2">
            Ofertas Recomendadas
          </h2>
          <p className="text-gray-400">
            Encontramos {jobs.length} oportunidades alineadas a tu perfil
          </p>
        </div>
        
        <div className="flex flex-col items-end">
          <button
            onClick={handleExpressSearch}
            disabled={isScraping}
            className={`flex items-center space-x-2 px-5 py-2.5 rounded-xl font-medium transition ${
              isScraping 
                ? 'bg-rose-900/40 text-rose-300 cursor-wait border border-rose-500/30' 
                : 'bg-black/40 hover:bg-rose-900/40 text-rose-100 border border-white/10 hover:border-rose-500/50 shadow-lg'
            }`}
          >
            {isScraping ? (
              <>
                <div className="w-4 h-4 border-2 border-rose-300 border-t-transparent rounded-full animate-spin"></div>
                <span className="text-sm">Buscando...</span>
              </>
            ) : (
              <>
                <Search size={16} />
                <span className="text-sm">Búsqueda Express</span>
              </>
            )}
          </button>
          
          {scrapeResult && scrapeResult.success && (
            <span className="text-xs text-green-400 mt-2 flex items-center">
              <CheckCircle2 size={12} className="mr-1" />
              +{scrapeResult.newJobs} nuevas
            </span>
          )}
          {scrapeResult && !scrapeResult.success && (
            <span className="text-xs text-red-400 mt-2">Error al buscar</span>
          )}
        </div>
      </div>

      <div className="grid gap-6">
        {jobs.map((match) => {
          const job = match.jobs;
          const score = match.match_score;

          return (
            <div key={match.id} className="glass-panel glass-panel-hover rounded-2xl p-8 relative overflow-hidden group">
              <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-rose-600 to-rose-400 opacity-0 group-hover:opacity-100 transition-opacity"></div>
              
              <div className="flex justify-between items-start mb-6">
                <div className="pr-10">
                  <h3 className="text-2xl font-bold text-white mb-2 group-hover:text-rose-400 transition-colors">
                    {job.title}
                  </h3>
                  <p className="text-lg text-gray-400 font-medium">{job.company}</p>
                </div>
                
                <div className={`
                  flex flex-col items-center justify-center w-20 h-20 rounded-full border-4 flex-shrink-0
                  ${score >= 80 ? 'border-emerald-500/50 bg-emerald-500/10 text-emerald-400' :
                    score >= 60 ? 'border-amber-500/50 bg-amber-500/10 text-amber-400' :
                    'border-gray-500/50 bg-gray-500/10 text-gray-400'}
                `}>
                  <span className="text-2xl font-bold leading-none">{score}</span>
                  <span className="text-[10px] font-bold uppercase tracking-wider mt-1 opacity-80">Match</span>
                </div>
              </div>

              <div className="flex flex-wrap gap-4 text-sm text-gray-300 mb-6 bg-black/20 p-4 rounded-xl border border-white/5">
                <div className="flex items-center space-x-2">
                  <MapPin size={16} className="text-gray-500" />
                  <span>{job.location || 'No especificada'}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Briefcase size={16} className="text-gray-500" />
                  <span className="capitalize">{job.work_mode || 'Remoto'}</span>
                </div>
                {job.salary_min && (
                  <div className="flex items-center space-x-2 text-emerald-400">
                    <DollarSign size={16} />
                    <span className="font-semibold">{job.salary_min.toLocaleString()} CLP</span>
                  </div>
                )}
              </div>

              {job.required_skills && job.required_skills.length > 0 && (
                <div className="mb-8">
                  <h4 className="text-xs uppercase tracking-wider text-gray-500 font-semibold mb-3">Requisitos Técnicos</h4>
                  <div className="flex flex-wrap gap-2">
                    {job.required_skills.map(skill => (
                      <span
                        key={skill}
                        className="px-3 py-1.5 bg-white/5 text-gray-300 rounded-lg text-xs font-medium border border-white/10"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <a
                href={job.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center space-x-2 px-6 py-3 bg-white text-black rounded-xl font-bold hover:bg-gray-200 transition-colors"
              >
                <span>Postular Ahora</span>
                <ExternalLink size={16} />
              </a>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function SettingsTab({ profile, onUpdate }) {
  const [minSalary, setMinSalary] = useState(profile.min_salary || '');
  const [workModes, setWorkModes] = useState(profile.work_modes || []);
  const [emailFrequency, setEmailFrequency] = useState(profile.email_frequency || 'weekly');

  const handleSave = () => {
    onUpdate({
      min_salary: minSalary ? parseInt(minSalary) : null,
      work_modes: workModes,
      email_frequency: emailFrequency
    });
    alert('Configuración guardada exitosamente.');
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="glass-panel rounded-3xl p-10">
        <div className="flex items-center space-x-3 mb-8 border-b border-white/10 pb-6">
          <Settings className="text-rose-500" size={28} />
          <h2 className="text-3xl font-bold text-white wine-glow">Preferencias</h2>
        </div>

        <div className="space-y-8">
          {/* Salario mínimo */}
          <div>
            <label className="block text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">
              Expectativa Salarial Mínima (CLP)
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <DollarSign className="text-gray-500" size={18} />
              </div>
              <input
                type="number"
                value={minSalary}
                onChange={(e) => setMinSalary(e.target.value)}
                placeholder="1500000"
                className="w-full pl-12 pr-4 py-4 bg-black/40 border border-white/10 rounded-xl text-white focus:ring-2 focus:ring-rose-500/50 focus:border-rose-500 transition outline-none text-lg"
              />
            </div>
          </div>

          {/* Modalidad de trabajo */}
          <div>
            <label className="block text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">
              Modalidades de Trabajo Aceptadas
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {[
                { id: 'remote', label: '100% Remoto' },
                { id: 'hybrid', label: 'Híbrido' },
                { id: 'onsite', label: 'Presencial' }
              ].map(mode => (
                <label 
                  key={mode.id} 
                  className={`flex items-center p-4 border rounded-xl cursor-pointer transition-all duration-200 ${
                    workModes.includes(mode.id) 
                      ? 'bg-rose-900/20 border-rose-500 text-rose-300' 
                      : 'bg-black/20 border-white/10 text-gray-400 hover:border-white/30 hover:bg-white/5'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={workModes.includes(mode.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setWorkModes([...workModes, mode.id]);
                      } else {
                        setWorkModes(workModes.filter(m => m !== mode.id));
                      }
                    }}
                    className="hidden"
                  />
                  <div className={`w-5 h-5 rounded-md border flex items-center justify-center mr-3 ${
                    workModes.includes(mode.id) ? 'bg-rose-500 border-rose-500' : 'border-gray-500'
                  }`}>
                    {workModes.includes(mode.id) && <Check size={14} className="text-white" />}
                  </div>
                  <span className="font-medium">{mode.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Frecuencia de emails */}
          <div>
            <label className="block text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">
              Frecuencia de Notificaciones (Email)
            </label>
            <div className="relative">
              <select
                value={emailFrequency}
                onChange={(e) => setEmailFrequency(e.target.value)}
                className="w-full px-4 py-4 bg-black/40 border border-white/10 rounded-xl text-white focus:ring-2 focus:ring-rose-500/50 focus:border-rose-500 transition outline-none appearance-none"
              >
                <option value="daily" className="bg-gray-900">Diario</option>
                <option value="weekly" className="bg-gray-900">Semanal (Recomendado)</option>
                <option value="biweekly" className="bg-gray-900">Quincenal</option>
                <option value="never" className="bg-gray-900">Desactivado</option>
              </select>
              <div className="absolute inset-y-0 right-0 flex items-center px-4 pointer-events-none text-gray-500">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-white/10">
            <button
              onClick={handleSave}
              className="w-full flex items-center justify-center space-x-2 px-6 py-4 bg-gradient-to-r from-rose-700 to-rose-600 text-white rounded-xl hover:from-rose-600 hover:to-rose-500 transition-all font-bold text-lg shadow-lg"
            >
              <Save size={20} />
              <span>Guardar Configuración</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
