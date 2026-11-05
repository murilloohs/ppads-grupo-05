import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import AppShell from '../components/AppShell';
import Icon from '../components/Icon';
import { api } from '../services/api';

const statusClass = value => ({ 'Em análise': 'pending', 'Aprovada': 'approved', 'Correções': 'correction', 'Reprovada': 'rejected' }[value] || 'draft');
const hourFormat = value => Number(value).toLocaleString('pt-BR', { maximumFractionDigits: 2 });
const dateLabel = value => value ? new Date(`${value}T00:00:00`).toLocaleDateString('pt-BR') : '';
const whenLabel = value => new Date(value).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' });

const errorText = err => {
  const detail = err.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  return 'Não foi possível carregar esta solicitação.';
};

export default function RequestDetail() {
  const { activityId } = useParams();
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
        const response = await api.get(`/activities/${activityId}`, {
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
  }, [activityId, navigate]);

  const openCertificate = async id => {
    try {
      const {data} = await api.get(`/activities/${activityId}/documents/${id}`, {
        headers: {Authorization: `Bearer ${localStorage.getItem('token')}`}, responseType: 'blob'});
      const url = URL.createObjectURL(data);
      const link = document.createElement('a'); link.href = url;
      link.download = detail.certificates.find(item => item.id === id)?.original_name || 'certificado';
      link.click(); setTimeout(() => URL.revokeObjectURL(url), 10000);
    } catch { setError('Não foi possível obter o certificado. Tente novamente.'); }
  };

  const period = detail
    ? [detail.start_date, detail.end_date].filter(Boolean).map(dateLabel).join(' a ') || 'Não informado'
    : '';

  return <AppShell title="Detalhe da solicitação">
    <div className="page-heading"><div><span className="eyebrow">MINHAS SOLICITAÇÕES</span><h1>{detail?.title || 'Sua solicitação'}</h1><p>Protocolo, situação atual e o que mudou neste envio.</p></div><button className="btn-outline" type="button" onClick={() => navigate('/minhas-solicitacoes')}>Voltar</button></div>
    {error && <div className="error-message" role="alert">{error}</div>}
    {loading ? <div className="loading-state" role="status"><span className="loading-spinner"/>Carregando a solicitação...</div> : detail && <div className="detail-stack">
      <section className="panel receipt"><div className="panel-heading"><div><h2>Solicitação</h2><p>Dados atuais desta atividade.</p></div><span className={`status-badge ${statusClass(detail.status)}`}>{detail.status}</span></div>
        <dl>
          <div><dt>Protocolo</dt><dd className="protocol-id">{detail.protocol}</dd></div>
          <div><dt>Atividade</dt><dd>{detail.title}</dd></div>
          <div><dt>Categoria</dt><dd>{detail.category}</dd></div>
          <div><dt>Instituição promotora</dt><dd>{detail.provider_name || 'Não informada'}</dd></div>
          <div><dt>Período</dt><dd>{period}</dd></div>
          <div><dt>Carga horária</dt><dd>{hourFormat(detail.declared_hours)} h</dd></div>
          {detail.description && <div><dt>Descrição</dt><dd>{detail.description}</dd></div>}
          <div><dt>Status</dt><dd>{detail.status}</dd></div>
          <div><dt>Resultado</dt><dd>{detail.result}</dd></div>
        </dl>
        <div className="panel-footnote"><Icon name="shield" size={15}/><span>Somente você visualiza esta solicitação.</span></div>
      </section>
      <section className="panel"><h2>Comprovante</h2>{detail.certificates?.map(item => <button type="button" className="btn-outline" key={item.id} onClick={() => openCertificate(item.id)}>Baixar {item.original_name}</button>)}</section>
      {detail.status === 'Correções' && <section className="panel"><h2>Correção solicitada</h2><p>Confira a justificativa, ajuste os dados e anexe o comprovante para uma nova análise.</p><button type="button" className="btn-primary" onClick={() => navigate(`/nova-atividade?corrigir=${activityId}`)}>Corrigir e reenviar</button></section>}
      {detail.justification && <section className="panel"><div className="panel-heading"><div><h2>Justificativa do avaliador</h2><p>Registro deixado na avaliação.</p></div></div><p className="detail-copy">{detail.justification}</p></section>}
      <section className="panel"><div className="panel-heading"><div><h2>Histórico</h2><p>Mudanças registradas nesta solicitação.</p></div></div>
        {detail.history.length === 0 ? <div className="empty-state"><span className="empty-icon"><Icon name="clock" size={30}/></span><h3>Nenhuma mudança registrada.</h3><p>O histórico aparece quando a solicitação é enviada ou avaliada.</p></div> : <ol className="history-list">{[...detail.history].reverse().map((item, index) => <li key={`${item.changed_at}-${index}`}><time dateTime={item.changed_at}>{whenLabel(item.changed_at)}</time><div><strong>{item.status}</strong>{item.note && <p>{item.note}</p>}</div></li>)}</ol>}
      </section>
    </div>}
  </AppShell>;
}
