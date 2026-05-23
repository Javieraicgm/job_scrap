import React, { useState, useEffect } from 'react';
import { createClient } from '@supabase/supabase-js';
import { Upload, Briefcase, Settings, Mail } from 'lucide-react';

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
        .insert([{
          ...parsedProfile,
          cv_file_url: urlData.publicUrl
        }])
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
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-blue-600">
              🎯 Job Detector
            </h1>
            {profile && (
              <div className="text-sm text-gray-600">
                {profile.email}
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            <TabButton
              active={activeTab === 'upload'}
              onClick={() => setActiveTab('upload')}
              icon={<Upload size={20} />}
              label="Subir CV"
            />
            <TabButton
              active={activeTab === 'jobs'}
              onClick={() => setActiveTab('jobs')}
              icon={<Briefcase size={20} />}
              label="Ofertas"
              disabled={!profile}
            />
            <TabButton
              active={activeTab === 'settings'}
              onClick={() => setActiveTab('settings')}
              icon={<Settings size={20} />}
              label="Configuración"
              disabled={!profile}
            />
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
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
          />
        )}

        {activeTab === 'settings' && profile && (
          <SettingsTab
            profile={profile}
            onUpdate={updateProfile}
          />
        )}
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
        flex items-center space-x-2 px-3 py-4 border-b-2 font-medium text-sm
        ${active
          ? 'border-blue-500 text-blue-600'
          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
        }
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
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
      <div className="bg-white rounded-lg shadow p-8">
        <h2 className="text-2xl font-bold mb-4">
          {profile ? '✅ CV Cargado' : '📄 Sube tu CV'}
        </h2>
        
        {profile ? (
          <div className="space-y-4">
            <p className="text-gray-600">
              Tu perfil está listo. Ve a la pestaña "Ofertas" para ver los matches.
            </p>
            
            <div className="bg-blue-50 p-6 rounded-lg border border-blue-100 relative">
              {!isEditing ? (
                <>
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="font-semibold text-lg text-blue-900">Datos Extraídos:</h3>
                    <button 
                      onClick={handleEditClick}
                      className="px-3 py-1 bg-blue-100 text-blue-700 rounded-md text-sm font-medium hover:bg-blue-200 transition"
                    >
                      Editar
                    </button>
                  </div>
                  <ul className="space-y-2 text-sm text-gray-700">
                    {profile.name && <li><strong className="text-gray-900">Nombre:</strong> {profile.name}</li>}
                    {profile.email && <li><strong className="text-gray-900">Email:</strong> {profile.email}</li>}
                    {profile.phone && <li><strong className="text-gray-900">Teléfono:</strong> {profile.phone}</li>}
                    {profile.skills && (
                      <li><strong className="text-gray-900">Skills:</strong> {profile.skills.join(', ')}</li>
                    )}
                    {profile.desired_roles && (
                      <li><strong className="text-gray-900">Roles:</strong> {profile.desired_roles.join(', ')}</li>
                    )}
                  </ul>
                </>
              ) : (
                <div className="space-y-3">
                  <div className="flex justify-between items-center mb-2">
                    <h3 className="font-semibold text-lg text-blue-900">Editar Perfil:</h3>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">Nombre</label>
                    <input 
                      type="text" 
                      value={editForm.name} 
                      onChange={e => setEditForm({...editForm, name: e.target.value})}
                      className="w-full px-3 py-2 border rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">Email</label>
                    <input 
                      type="email" 
                      value={editForm.email} 
                      onChange={e => setEditForm({...editForm, email: e.target.value})}
                      className="w-full px-3 py-2 border rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">Teléfono</label>
                    <input 
                      type="text" 
                      value={editForm.phone} 
                      onChange={e => setEditForm({...editForm, phone: e.target.value})}
                      className="w-full px-3 py-2 border rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">Skills (separados por coma)</label>
                    <textarea 
                      value={editForm.skills} 
                      onChange={e => setEditForm({...editForm, skills: e.target.value})}
                      className="w-full px-3 py-2 border rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
                      rows={2}
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">Roles (separados por coma)</label>
                    <input 
                      type="text" 
                      value={editForm.desired_roles} 
                      onChange={e => setEditForm({...editForm, desired_roles: e.target.value})}
                      className="w-full px-3 py-2 border rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div className="flex space-x-2 pt-2">
                    <button 
                      onClick={handleSaveClick}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 transition"
                    >
                      Guardar Cambios
                    </button>
                    <button 
                      onClick={() => setIsEditing(false)}
                      className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md text-sm font-medium hover:bg-gray-300 transition"
                    >
                      Cancelar
                    </button>
                  </div>
                </div>
              )}
            </div>

            <button
              onClick={() => {
                if (confirm('¿Quieres subir un nuevo CV? Esto reemplazará tu perfil actual.')) {
                  localStorage.removeItem('jobDetectorProfile');
                  window.location.reload();
                }
              }}
              className="text-blue-600 hover:text-blue-800 text-sm mt-4 inline-block"
            >
              Subir nuevo CV →
            </button>
          </div>
        ) : (
          <>
            <p className="text-gray-600 mb-6">
              Sube tu CV y automáticamente extraeremos tu perfil profesional
              para encontrar las mejores ofertas laborales para ti.
            </p>

            <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center hover:border-blue-500 transition">
              <input
                type="file"
                accept=".pdf,.docx"
                onChange={onUpload}
                disabled={loading}
                className="hidden"
                id="cv-upload"
              />
              <label htmlFor="cv-upload" className="cursor-pointer">
                <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <p className="text-sm text-gray-600">
                  {loading ? 'Procesando...' : 'Click para subir CV (PDF o DOCX)'}
                </p>
              </label>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function JobsTab({ jobs, profile }) {
  if (!jobs || jobs.length === 0) {
    return (
      <div className="text-center py-12">
        <Briefcase className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        <p className="text-gray-600">
          Aún no hay ofertas. Los scrapers buscan nuevas ofertas cada 6 horas.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">
          {jobs.length} Ofertas Encontradas
        </h2>
      </div>

      {jobs.map((match) => {
        const job = match.jobs;
        const score = match.match_score;

        return (
          <div key={match.id} className="bg-white rounded-lg shadow p-6 hover:shadow-md transition">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-xl font-semibold text-blue-600">
                  {job.title}
                </h3>
                <p className="text-gray-600">{job.company}</p>
              </div>
              
              <div className={`
                px-4 py-2 rounded-full font-semibold text-sm
                ${score >= 80 ? 'bg-green-100 text-green-800' :
                  score >= 60 ? 'bg-yellow-100 text-yellow-800' :
                  'bg-orange-100 text-orange-800'}
              `}>
                {score}% Match
              </div>
            </div>

            <div className="flex space-x-6 text-sm text-gray-600 mb-4">
              <span>📍 {job.location}</span>
              <span>💼 {job.work_mode}</span>
              {job.salary_min && (
                <span>💰 ${job.salary_min.toLocaleString()}</span>
              )}
            </div>

            {job.required_skills && job.required_skills.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-4">
                {job.required_skills.map(skill => (
                  <span
                    key={skill}
                    className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            )}

            <a
              href={job.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              Ver Oferta →
            </a>
          </div>
        );
      })}
    </div>
  );
}

function SettingsTab({ profile, onUpdate }) {
  const [minSalary, setMinSalary] = useState(profile.min_salary || '');
  const [workModes, setWorkModes] = useState(profile.work_modes || []);
  const [emailFrequency, setEmailFrequency] = useState(profile.email_frequency || 'weekly');

  const handleSave = () => {
    onUpdate({
      min_salary: parseInt(minSalary),
      work_modes: workModes,
      email_frequency: emailFrequency
    });
    alert('Configuración guardada ✅');
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white rounded-lg shadow p-8 space-y-6">
        <h2 className="text-2xl font-bold mb-6">Configuración</h2>

        {/* Salario mínimo */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Salario mínimo esperado (CLP bruto)
          </label>
          <input
            type="number"
            value={minSalary}
            onChange={(e) => setMinSalary(e.target.value)}
            placeholder="1200000"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Modalidad de trabajo */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Modalidades de trabajo preferidas
          </label>
          <div className="space-y-2">
            {['remote', 'hybrid', 'onsite'].map(mode => (
              <label key={mode} className="flex items-center">
                <input
                  type="checkbox"
                  checked={workModes.includes(mode)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setWorkModes([...workModes, mode]);
                    } else {
                      setWorkModes(workModes.filter(m => m !== mode));
                    }
                  }}
                  className="mr-2"
                />
                <span className="capitalize">{mode}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Frecuencia de emails */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Frecuencia de reportes por email
          </label>
          <select
            value={emailFrequency}
            onChange={(e) => setEmailFrequency(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="daily">Diario</option>
            <option value="weekly">Semanal</option>
            <option value="biweekly">Quincenal</option>
            <option value="never">Nunca</option>
          </select>
        </div>

        <button
          onClick={handleSave}
          className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium"
        >
          Guardar Cambios
        </button>
      </div>
    </div>
  );
}

export default App;
