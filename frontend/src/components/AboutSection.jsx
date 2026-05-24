import React, { useState } from 'react';
import { User, AlertCircle, Bug, Send, Upload, CheckCircle2, Github, Linkedin } from 'lucide-react';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_KEY
);

const AboutSection = () => {
  const [reportType, setReportType] = useState('bug');
  const [description, setDescription] = useState('');
  const [file, setFile] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handlePaste = (e) => {
    if (e.clipboardData && e.clipboardData.files && e.clipboardData.files.length > 0) {
      const pastedFile = e.clipboardData.files[0];
      if (pastedFile.type.startsWith('image/')) {
        setFile(pastedFile);
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!description.trim()) return;

    setIsSubmitting(true);
    setSubmitStatus(null);

    try {
      let imageUrl = null;

      // 1. Subir la imagen a Supabase Storage (si existe)
      if (file) {
        const fileExt = file.name.split('.').pop();
        const fileName = `${Date.now()}-${Math.random().toString(36).substring(2)}.${fileExt}`;
        const filePath = `reports/${fileName}`;

        const { error: uploadError, data } = await supabase.storage
          .from('bug_reports')
          .upload(filePath, file);

        if (uploadError) throw uploadError;

        // Obtener URL pública
        const { data: urlData } = supabase.storage
          .from('bug_reports')
          .getPublicUrl(filePath);

        imageUrl = urlData.publicUrl;
      }

      // 2. Obtener datos del usuario local si existe
      const profileStr = localStorage.getItem('jobDetectorProfile');
      let userEmail = 'Usuario Anónimo';
      let userName = 'Anónimo';
      
      if (profileStr) {
        const profile = JSON.parse(profileStr);
        userEmail = profile.email || userEmail;
        userName = profile.name || userName;
      }

      // 3. Enviar a nuestro backend para que mande el correo y guarde en BD
      const response = await fetch('/api/report-bug', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: reportType,
          description,
          imageUrl,
          userEmail,
          userName
        })
      });

      if (!response.ok) {
        throw new Error('Error enviando el reporte al servidor');
      }

      setSubmitStatus('success');
      setDescription('');
      setFile(null);
      
      // Limpiar mensaje de éxito después de 5 segundos
      setTimeout(() => setSubmitStatus(null), 5000);

    } catch (error) {
      console.error('Error submitting report:', error);
      setSubmitStatus('error');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      
      {/* Creador Info */}
      <div className="glass-panel rounded-3xl p-10 relative overflow-hidden">
        <div className="absolute -top-20 -right-20 w-64 h-64 bg-rose-900/20 rounded-full blur-3xl pointer-events-none"></div>
        <div className="absolute -bottom-20 -left-20 w-64 h-64 bg-blue-900/20 rounded-full blur-3xl pointer-events-none"></div>
        
        <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center gap-8">
          <div className="w-24 h-24 bg-gradient-to-br from-rose-500 to-rose-700 rounded-full flex items-center justify-center flex-shrink-0 shadow-lg shadow-rose-900/50">
            <User size={40} className="text-white" />
          </div>
          <div>
            <h2 className="text-3xl font-bold text-white mb-2">Google Antigravity</h2>
            <p className="text-gray-400 mb-4 text-sm">Desarrollado y mantenido por <strong className="text-rose-400">Javiera Carrasco Gamboa</strong></p>
            <p className="text-gray-300 max-w-2xl text-base leading-relaxed mb-6">
              Esta aplicación es un buscador impulsado por Inteligencia Artificial diseñado para facilitar la búsqueda de empleos en áreas STEM en Chile. Actualmente se encuentra en versión <strong className="text-white">Beta</strong>.
            </p>
            <div className="flex gap-4">
              <a 
                href="https://www.linkedin.com/in/javiera-ignacia-carrasco-gamboa-a8177b273/" 
                target="_blank" 
                rel="noreferrer"
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600/20 hover:bg-blue-600/40 text-blue-300 rounded-full text-sm font-medium transition border border-blue-500/30"
              >
                <Linkedin size={16} />
                <span>Conectar en LinkedIn</span>
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* Report Bug Section */}
      <div className="glass-panel rounded-3xl p-10 relative overflow-hidden">
        <div className="relative z-10">
          <div className="flex items-center mb-6 border-b border-white/10 pb-4">
            <Bug className="text-rose-400 mr-3" size={28} />
            <h3 className="text-2xl font-bold text-white">Centro de Reportes</h3>
          </div>
          
          <p className="text-gray-400 mb-8">
            Al ser una versión Beta, es posible que el robot de scraping cometa errores o la página tenga fallos. 
            Si encuentras algo extraño, o tienes una idea genial, por favor envíala aquí. Me llegará directamente a mi correo.
          </p>

          <form onSubmit={handleSubmit} onPaste={handlePaste} className="space-y-6 max-w-2xl bg-black/30 p-8 rounded-2xl border border-white/5">
            
            {/* Tipo de reporte */}
            <div>
              <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Tipo de Feedback</label>
              <div className="flex gap-4">
                <button
                  type="button"
                  onClick={() => setReportType('bug')}
                  className={`flex-1 py-3 px-4 rounded-xl flex items-center justify-center space-x-2 border transition ${
                    reportType === 'bug' 
                      ? 'bg-rose-900/40 border-rose-500/50 text-rose-300' 
                      : 'bg-black/40 border-white/10 text-gray-400 hover:bg-white/5'
                  }`}
                >
                  <AlertCircle size={18} />
                  <span>Error / Bug</span>
                </button>
                <button
                  type="button"
                  onClick={() => setReportType('idea')}
                  className={`flex-1 py-3 px-4 rounded-xl flex items-center justify-center space-x-2 border transition ${
                    reportType === 'idea' 
                      ? 'bg-blue-900/40 border-blue-500/50 text-blue-300' 
                      : 'bg-black/40 border-white/10 text-gray-400 hover:bg-white/5'
                  }`}
                >
                  <User size={18} />
                  <span>Idea / Mejora</span>
                </button>
              </div>
            </div>

            {/* Descripción */}
            <div>
              <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Descripción detallada</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Ej: Intenté subir mi CV pero se quedó cargando infinito..."
                required
                rows={4}
                className="w-full px-4 py-3 bg-black/40 border border-white/10 rounded-xl text-white focus:ring-2 focus:ring-rose-500/50 focus:border-rose-500 transition outline-none resize-none"
              ></textarea>
            </div>

            {/* Subida de foto */}
            <div>
              <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Adjuntar Captura (Opcional)</label>
              <div className="flex items-center justify-center w-full">
                <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-white/10 border-dashed rounded-xl cursor-pointer bg-black/20 hover:bg-white/5 transition">
                  <div className="flex flex-col items-center justify-center pt-5 pb-6">
                    <Upload className="w-8 h-8 mb-3 text-gray-500" />
                    <p className="mb-2 text-sm text-gray-400">
                      {file ? <span className="text-rose-400 font-semibold">{file.name}</span> : <span><span className="font-semibold">Haz clic para subir</span>, arrastra, o presiona Ctrl+V para pegar</span>}
                    </p>
                    <p className="text-xs text-gray-500">PNG, JPG o WEBP (MAX. 5MB)</p>
                  </div>
                  <input type="file" className="hidden" accept="image/*" onChange={handleFileChange} />
                </label>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isSubmitting || !description.trim()}
              className="w-full py-4 bg-gradient-to-r from-rose-600 to-rose-800 hover:from-rose-500 hover:to-rose-700 text-white font-semibold rounded-xl transition shadow-lg shadow-rose-900/30 flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <div className="w-6 h-6 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
              ) : (
                <>
                  <Send size={18} />
                  <span>Enviar Reporte a Javiera</span>
                </>
              )}
            </button>

            {/* Status Messages */}
            {submitStatus === 'success' && (
              <div className="flex items-center space-x-2 text-green-400 bg-green-900/20 p-4 rounded-xl border border-green-500/30">
                <CheckCircle2 size={20} />
                <p className="text-sm font-medium">¡Reporte enviado exitosamente! Muchas gracias por tu ayuda.</p>
              </div>
            )}
            
            {submitStatus === 'error' && (
              <div className="flex items-center space-x-2 text-red-400 bg-red-900/20 p-4 rounded-xl border border-red-500/30">
                <AlertCircle size={20} />
                <p className="text-sm font-medium">Ocurrió un error al enviar. Por favor intenta de nuevo.</p>
              </div>
            )}

          </form>
        </div>
      </div>

    </div>
  );
};

export default AboutSection;
