import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import AppShell from '../components/AppShell';
import Icon from '../components/Icon';
import { api } from '../services/api';

const hourFormat = value => Number(value).toLocaleString('pt-BR', { maximumFractionDigits: 2 });
const dateLabel = value => value ? new Date(`${value}T00:00:00`).toLocaleDateString('pt-BR') : '';
const whenLabel = value => new Date(value).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' });
const percentLabel = value => value == null ? 'Não informada' : `${Math.round(Number(value) * 100)}%`;
const sizeLabel = value => `${(Number(value) / 1024).toLocaleString('pt-BR', { maximumFractionDigits: 0 })} KB`;

const fieldLabel = value => {
  if (value == null || value === '') return 'Não informado';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
};

const errorText = err => {
  const detail = err.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  return 'Não foi possível carregar esta solicitação.';
};

export default function ReviewDetail() {
  const { submissionId } = useParams();
  const navigate = useNavigate();
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }

    const fetchDetail = async () => {
      try {
        const response = await api.get(`/reviews/${submissionId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setDetail(response.data);
      } catch (err) {
        setError(errorText(err));
      } finally {
        setLoading(false);
      }
    };

    fetchDetail();
  }, [submissionId, navigate]);

  const openCertificate = async documentId => {
    const token = localStorage.getItem('token');
    try {
      const response = await api.get(`/reviews/${submissionId}/certificates/${documentId}`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob',
      });
      const url = URL.createObjectURL(response.data);
      window.open(url, '_blank', 'noopener');
      setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch {
      setError('Não foi possível abrir o certificado.');
    }
  };

  const activity = detail?.activity;
  const period = activity
    ? [activity.start_date, activity.end_date].filter(Boolean).map(dateLabel).join(' a ') || 'Não informado'
    : '';
  const extracted = (detail?.certificates || []).filter(item => item.extracted_data || item.ocr_text);
  const rule = detail?.rule;

  return <AppShell title="Revisão da solicitação" variant="avaliador">
    <div className="page-heading"><div><span className="eyebrow">FILA DE REVISÃO</span><h1>{activity?.title || 'Solicitação'}</h1><p>Atividade, certificado, leitura, análise automática e regra utilizada.</p></div><button className="btn-outline" type="button" onClick={() => navigate('/avaliador')}>Voltar à fila</button></div>
    {error && <div className="error-message" role="alert">{error}</div>}
    {loading ? <div className="loading-state" role="status"><span className="loading-spinner"/>Carregando a solicitação...</div> : detail && <div className="detail-stack">
      <section className="panel receipt"><div className="panel-heading"><div><h2>Dados da atividade</h2><p>{detail.protocol} · {whenLabel(detail.submitted_at)}</p></div><span className="status-badge pending">{detail.status}</span></div>
        <dl>
          <div><dt>Protocolo</dt><dd className="protocol-id">{detail.protocol}</dd></div>
          <div><dt>Aluno</dt><dd>{activity.student_name}</dd></div>
          <div><dt>Atividade</dt><dd>{activity.title}</dd></div>
          <div><dt>Categoria</dt><dd>{activity.category}</dd></div>
          <div><dt>Instituição promotora</dt><dd>{activity.provider_name || 'Não informada'}</dd></div>
          <div><dt>Período</dt><dd>{period}</dd></div>
          <div><dt>Carga horária</dt><dd>{hourFormat(activity.declared_hours)} h</dd></div>
          {activity.description && <div><dt>Descrição</dt><dd>{activity.description}</dd></div>}
        </dl>
      </section>
      <section className="panel"><div className="panel-heading"><div><h2>Certificado</h2><p>Documento enviado com a solicitação.</p></div></div>
        {detail.certificates.length === 0 ? <div className="empty-state"><span className="empty-icon"><Icon name="file" size={30}/></span><h3>Nenhum certificado anexado.</h3><p>O arquivo aparece aqui quando o envio inclui um comprovante.</p></div> : detail.certificates.map(item => <div className="cert-row" key={item.id}><div><strong>{item.original_name}</strong><span>{item.mime_type} · {sizeLabel(item.size_bytes)}</span></div><button type="button" className="btn-outline" onClick={() => openCertificate(item.id)}>Abrir certificado</button></div>)}
      </section>
      <section className="panel"><div className="panel-heading"><div><h2>Dados extraídos pelo OCR</h2><p>Leitura do certificado para a análise automática.</p></div></div>
        {extracted.length === 0 ? <div className="empty-state"><span className="empty-icon"><Icon name="file" size={30}/></span><h3>Leitura ainda não disponível.</h3><p>Os dados extraídos aparecem aqui quando o certificado for lido.</p></div> : extracted.map(item => <div key={item.id}>{item.extracted_data && <dl className="receipt-data">{Object.entries(item.extracted_data).map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{fieldLabel(value)}</dd></div>)}</dl>}{item.ocr_text && <pre className="ocr-text">{item.ocr_text}</pre>}</div>)}
      </section>
      <section className="panel receipt"><div className="panel-heading"><div><h2>Resultado da análise automática</h2><p>O que a análise concluiu antes da fila.</p></div></div>
        {detail.analysis ? <dl><div><dt>Resultado</dt><dd>{detail.analysis.result}</dd></div><div><dt>Confiança</dt><dd>{percentLabel(detail.analysis.confidence)}</dd></div>{detail.analysis.explanation && <div><dt>Explicação</dt><dd>{detail.analysis.explanation}</dd></div>}</dl> : <div className="empty-state"><span className="empty-icon"><Icon name="clock" size={30}/></span><h3>Análise ainda não registrada.</h3><p>O resultado automático aparece aqui quando a avaliação do envio for concluída.</p></div>}
      </section>
      <section className="panel receipt"><div className="panel-heading"><div><h2>Regra utilizada</h2><p>Critério consultado para esta solicitação.</p></div></div>
        {rule ? <dl><div><dt>Categoria</dt><dd>{rule.category}</dd></div><div><dt>Período de vigência</dt><dd>{dateLabel(rule.valid_from)}{rule.valid_until ? ` a ${dateLabel(rule.valid_until)}` : ' em diante'}</dd></div><div><dt>Carga horária máxima</dt><dd>{rule.max_hours == null ? 'Sem limite' : `${hourFormat(rule.max_hours)} h`}</dd></div><div><dt>Documentos aceitos</dt><dd>{(rule.accepted_document_types || []).join(', ') || 'Não informados'}</dd></div><div><dt>Limite de confiança</dt><dd>{percentLabel(rule.confidence_threshold)}</dd></div><div><dt>Aprovação automática</dt><dd>{rule.allows_auto_approval ? 'Permitida' : 'Não permitida'}</dd></div></dl> : <div className="empty-state"><span className="empty-icon"><Icon name="shield" size={30}/></span><h3>Nenhuma regra associada.</h3><p>A regra usada na análise aparece aqui quando a solicitação for vinculada a um critério.</p></div>}
      </section>
    </div>}
  </AppShell>;
}
