import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { getUserData } from '../services/auth';

export default function NewActivity() {
  const navigate = useNavigate();
  
  const user = getUserData();
  
  const [formData, setFormData] = useState({
    nome: '',
    instituicao: '',
    categoria: '',
    periodo: '',
    cargaHoraria: ''
  });
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  useEffect(() => {
    if (!localStorage.getItem('token')) navigate('/login');
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Por favor, anexe o documento comprobatório antes de enviar.');
      return;
    }

    setLoading(true);
    setError('');
    
    const token = localStorage.getItem('token');
    const configAuth = { headers: { Authorization: `Bearer ${token}` } };

    try {
      const actResponse = await api.post('/activities/', {
        title: formData.nome,
        description: `Instituição: ${formData.instituicao} | Período: ${formData.periodo}`,
        category: formData.categoria,
        declared_hours: Number(formData.cargaHoraria.replace(/\D/g, '')) || 0,
      }, configAuth);

      const activityId = actResponse.data.id;

      const fileData = new FormData();
      fileData.append('file', file);
      
      await api.post(`/activities/${activityId}/documents`, fileData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          Authorization: `Bearer ${token}`
        }
      });

      const submitRes = await api.post(`/activities/${activityId}/submit`, {}, configAuth);

      navigate('/sucesso', { 
        state: { 
          protocol: submitRes.data.protocol,
          formData: formData,
          fileName: file.name
        } 
      });

    } catch (err) {
      console.error(err);
      setError('Erro ao enviar a solicitação. Verifique os dados e tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header className="top-bar">
        <div className="logo-area">
          <h1 className="brand-title">ValidaHoras</h1>
          <span className="brand-subtitle">Submeter Atividade Complementar</span>
        </div>
        <div className="user-profile-area">
          <div className="user-info">
            <span className="user-email">{user.email}</span>
            <span className="badge-acesso">{user.role}</span>
          </div>
          <button onClick={handleLogout} className="btn-logout">Sair</button>
        </div>
      </header>

      <main className="dashboard-content">
        <h2 className="page-title">Nova atividade complementar</h2>
        
        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}

        <form onSubmit={handleSubmit} className="new-activity-form">
          <div className="form-grid-2">
            <div className="form-group">
              <label>Nome da atividade</label>
              <input 
                type="text" 
                placeholder="Ex.: Curso de IA" 
                value={formData.nome}
                onChange={e => setFormData({...formData, nome: e.target.value})}
                required
              />
            </div>
            <div className="form-group">
              <label>Instituição</label>
              <input 
                type="text" 
                placeholder="Ex.: Mackenzie" 
                value={formData.instituicao}
                onChange={e => setFormData({...formData, instituicao: e.target.value})}
                required
              />
            </div>
          </div>

          <div className="form-grid-3">
            <div className="form-group">
              <label>Categoria</label>
              <input 
                type="text" 
                placeholder="Curso | Evento | Projeto" 
                value={formData.categoria}
                onChange={e => setFormData({...formData, categoria: e.target.value})}
                required
              />
            </div>
            <div className="form-group">
              <label>Período</label>
              <input 
                type="text" 
                placeholder="Ago/2026 - Set/2026" 
                value={formData.periodo}
                onChange={e => setFormData({...formData, periodo: e.target.value})}
                required
              />
            </div>
            <div className="form-group">
              <label>Carga horária</label>
              <input 
                type="text" 
                placeholder="40 horas" 
                value={formData.cargaHoraria}
                onChange={e => setFormData({...formData, cargaHoraria: e.target.value})}
                required
              />
            </div>
          </div>

          <div className="document-section">
            <h3 className="section-title">Documento comprobatório</h3>
            <p className="section-subtitle">Formatos: PDF, JPG, PNG. Tamanho máximo: 10MB.</p>
            
            <label 
              className={`dropzone ${isDragging ? 'dragging' : ''}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <input 
                type="file" 
                accept=".pdf,.jpg,.jpeg,.png" 
                onChange={handleFileChange} 
                className="hidden-file-input"
              />
              <div className="dropzone-content">
                <p>Arraste o arquivo aqui ou clique para selecionar</p>
                {file && <p className="file-name">{file.name}</p>}
                {!file && <p className="file-name placeholder-text">certificado_curso_ia.pdf</p>}
              </div>
            </label>
          </div>

          <div className="form-footer-actions">
            <button type="button" className="btn-outline" onClick={() => navigate('/dashboard')}>Revisar resumo</button>
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Enviando...' : 'Confirmar envio'}
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}