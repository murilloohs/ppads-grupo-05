import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import AppShell from '../components/AppShell';
import Icon from '../components/Icon';

export default function NewActivity() {
  const navigate = useNavigate();



  const [formData, setFormData] = useState({
    nome: '',
    instituicao: '',
    categoria: '',
    inicio: '',
    fim: '',
    cargaHoraria: ''
  });
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [reviewing, setReviewing] = useState(false);
  const [draftId, setDraftId] = useState(null);

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
    if (loading || reviewing) return;
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  useEffect(() => {
    if (!localStorage.getItem('token')) navigate('/login');
  }, [navigate]);

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

    const hours = Number(formData.cargaHoraria.trim().replace(',', '.'));
    if (!Number.isFinite(hours) || hours <= 0 || hours > 99999.99) {
      setError('Informe uma carga horária válida, como 1,5 ou 40.'); return;
    }
    if (formData.fim < formData.inicio) { setError('Confira as datas do período.'); return; }
    if (!['application/pdf', 'image/jpeg', 'image/png'].includes(file.type) || file.size === 0 || file.size > 10 * 1024 * 1024) {
      setError('Anexe um PDF, JPG ou PNG válido de até 10 MB.'); return;
    }
    if (!reviewing) { setError(''); setReviewing(true); window.scrollTo({ top: 0, behavior: 'smooth' }); return; }
    setLoading(true);
    setError('');

    const token = localStorage.getItem('token');
    const configAuth = { headers: { Authorization: `Bearer ${token}` } };

    try {
      const actResponse = draftId ? { data: { id: draftId } } : await api.post('/activities/', {
        title: formData.nome,
        provider_name: formData.instituicao,
        start_date: formData.inicio,
        end_date: formData.fim,
        category: formData.categoria,
        declared_hours: hours,
      }, configAuth);

      const activityId = actResponse.data.id;
      setDraftId(activityId);

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
          formData: {...formData, periodo: `${formData.inicio} a ${formData.fim}`},
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

  return <AppShell title="Nova atividade">
   <div className="page-heading"><div><span className="eyebrow">UM NOVO APRENDIZADO</span><h1>Vamos registrar sua atividade.</h1><p>Preencha os dados e tenha seu comprovante em mãos.</p></div></div>
   <ol className="form-steps" aria-label="Etapas do envio"><li className={!reviewing ? 'current' : 'complete'} aria-current={!reviewing ? 'step' : undefined}><span>{reviewing ? <Icon name="check" size={16}/> : '1'}</span>Dados e comprovante</li><li className={reviewing ? 'current' : ''} aria-current={reviewing ? 'step' : undefined}><span>2</span>Revisão e envio</li><li><span>3</span>Protocolo</li></ol>
   {error && <div className="error-message" role="alert">{error}</div>}
   {reviewing && <section className="review-banner" role="status"><Icon name="circleCheck" size={25}/><div><h2>Tudo certo? Confira antes de enviar.</h2><p>{formData.nome} · {formData.instituicao} · {formData.cargaHoraria} horas</p><p>O envio gera um protocolo. A aprovação depende da avaliação.</p></div></section>}
   <div className="form-layout"><form onSubmit={handleSubmit} className="new-activity-form">
    <div className="form-section-heading"><span className="section-number">01</span><div><h2>Sobre a atividade</h2><p>Use as informações que constam no seu comprovante.</p></div></div>
    <fieldset disabled={loading || reviewing}>
     <div className="form-grid-2">
      <div className="form-group"><label htmlFor="activity-name">Nome da atividade</label><input id="activity-name" type="text" maxLength={200} placeholder="Ex.: Curso de Inteligência Artificial" value={formData.nome} onChange={e=>setFormData({...formData,nome:e.target.value})} required/></div>
      <div className="form-group"><label htmlFor="institution">Instituição promotora</label><input id="institution" type="text" maxLength={180} placeholder="Quem realizou a atividade?" value={formData.instituicao} onChange={e=>setFormData({...formData,instituicao:e.target.value})} required/></div>
      <div className="form-group"><label htmlFor="category">Categoria</label><input id="category" type="text" maxLength={100} placeholder="Ex.: Curso, evento ou projeto" value={formData.categoria} onChange={e=>setFormData({...formData,categoria:e.target.value})} required/></div>
      <div className="form-group"><label htmlFor="hours">Carga horária</label><div className="input-suffix"><input id="hours" type="text" placeholder="Ex.: 1,5" inputMode="decimal" pattern="[0-9]+([.,][0-9]{1,2})?" value={formData.cargaHoraria} onChange={e=>setFormData({...formData,cargaHoraria:e.target.value})} required/><span>horas</span></div></div>
      <div className="form-group"><label htmlFor="start-date">Data inicial</label><input id="start-date" type="date" value={formData.inicio} onChange={e=>setFormData({...formData,inicio:e.target.value})} required/></div>
      <div className="form-group"><label htmlFor="end-date">Data final</label><input id="end-date" type="date" min={formData.inicio || undefined} value={formData.fim} onChange={e=>setFormData({...formData,fim:e.target.value})} required/></div>
     </div>
     <div className="document-section"><div className="form-section-heading"><span className="section-number">02</span><div><h2>Seu comprovante</h2><p>Certificado, declaração ou comprovante de participação.</p></div></div>
      <label className={`dropzone ${isDragging ? 'dragging' : ''} ${file ? 'has-file' : ''}`} onDragOver={handleDragOver} onDragLeave={handleDragLeave} onDrop={handleDrop}>
       <input type="file" accept=".pdf,.jpg,.jpeg,.png" onChange={handleFileChange} className="hidden-file-input" aria-label="Selecionar documento comprobatório"/>
       <span className="upload-symbol"><Icon name={file ? 'circleCheck' : 'upload'} size={25}/></span><strong>{file ? file.name : 'Clique para selecionar ou arraste seu arquivo'}</strong><span>{file ? `${(file.size / 1024).toLocaleString('pt-BR', {maximumFractionDigits: 0})} KB · Arquivo selecionado` : 'PDF, JPG ou PNG · tamanho máximo de 10 MB'}</span>
      </label>
     </div>
    </fieldset>
    <div className="form-footer-actions"><button type="button" className="btn-outline" disabled={loading || Boolean(draftId)} onClick={()=>reviewing ? setReviewing(false) : navigate('/dashboard')}>{reviewing ? 'Editar dados' : 'Cancelar'}</button><button type="submit" className="btn-primary" disabled={loading}>{loading ? 'Enviando...' : reviewing ? 'Confirmar envio' : 'Revisar resumo'}<Icon name={reviewing ? 'check' : 'file'} size={17}/></button></div>
   </form><aside className="form-aside"><span className="note-icon"><Icon name="book"/></span><h2>Antes de enviar</h2><ul><li>Confira o nome da atividade e da instituição.</li><li>Informe as horas indicadas no documento.</li><li>Envie um comprovante legível e completo.</li></ul><div className="aside-divider"/><Icon name="shield" size={20}/><h3>Um registro para acompanhar.</h3><p>Após confirmar, você recebe um protocolo para consultar o status da sua solicitação.</p></aside></div>
  </AppShell>;
}
