import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AppShell from '../components/AppShell';
import Icon from '../components/Icon';
import { api } from '../services/api';

const hourFormat = value => Number(value).toLocaleString('pt-BR', { maximumFractionDigits: 2 });
const whenLabel = value => new Date(value).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' });

const isToday = value => {
  const date = new Date(value);
  const now = new Date();
  return date.getFullYear() === now.getFullYear() && date.getMonth() === now.getMonth() && date.getDate() === now.getDate();
};

export default function EvaluatorDashboard() {
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }

    const fetchQueue = async () => {
      try {
        const response = await api.get('/reviews', { headers: { Authorization: `Bearer ${token}` } });
        setItems(response.data);
      } catch {
        setError('Não foi possível carregar a fila. Atualize a página para tentar novamente.');
      } finally {
        setLoading(false);
      }
    };

    fetchQueue();
  }, [navigate]);

  const todayCount = items.filter(item => isToday(item.submitted_at)).length;
  const withAnalysis = items.filter(item => item.has_analysis).length;
  const withoutRule = items.filter(item => !item.has_rule).length;
  const openItem = item => navigate(`/avaliador/solicitacoes/${item.id}`);

  return <AppShell title="Visão geral" variant="avaliador">
    <div className="page-heading"><div><span className="eyebrow">REVISÃO MANUAL</span><h1>O que pede o seu olhar.</h1><p>Solicitações que não foram concluídas pela aprovação automática.</p></div></div>
    {error && <div className="error-message" role="alert">{error}</div>}
    {loading ? <div className="loading-state" role="status"><span className="loading-spinner"/>Carregando a fila...</div> : <>
     <section className="stats-grid" aria-label="Resumo da fila">
      <div className="stat-card stat-featured"><div className="stat-top"><span>Na fila</span><Icon name="file"/></div><strong className="stat-number">{items.length.toString().padStart(2, '0')}</strong><span className="stat-caption">Aguardando revisão manual</span><div className="stat-decoration" aria-hidden="true"/></div>
      <div className="stat-card"><div className="stat-top"><span>Recebidas hoje</span><span className="stat-icon pending"><Icon name="clock"/></span></div><strong className="stat-number">{todayCount.toString().padStart(2, '0')}</strong><span className="stat-caption">Entraram na fila hoje</span></div>
      <div className="stat-card"><div className="stat-top"><span>Com análise</span><span className="stat-icon approved"><Icon name="circleCheck"/></span></div><strong className="stat-number">{withAnalysis.toString().padStart(2, '0')}</strong><span className="stat-caption">Já têm resultado automático</span></div>
      <div className="stat-card"><div className="stat-top"><span>Sem regra</span><span className="stat-icon correction"><Icon name="edit"/></span></div><strong className="stat-number">{withoutRule.toString().padStart(2, '0')}</strong><span className="stat-caption">Ainda sem regra associada</span></div>
     </section>
     <div className="dashboard-lower">
      <section className="panel requests-panel"><div className="panel-heading"><div><h2>Fila de revisão</h2><p>Selecione uma solicitação para ver o certificado, a leitura e a regra.</p></div></div>
       {items.length === 0 ? <div className="empty-state"><span className="empty-icon"><Icon name="circleCheck" size={30}/></span><h3>Nenhuma solicitação aguardando revisão.</h3><p>Quando a aprovação automática não concluir um envio, ele aparece aqui.</p></div> : <div className="table-scroll"><table className="activity-table"><thead><tr><th>ATIVIDADE / PROTOCOLO</th><th>ALUNO</th><th>CARGA</th><th>ENVIADA</th></tr></thead><tbody>{items.map(item => <tr key={item.id} className="clickable-row" tabIndex={0} role="button" aria-label={`Abrir revisão de ${item.title}`} onClick={() => openItem(item)} onKeyDown={event => { if (event.key !== 'Enter' && event.key !== ' ') return; event.preventDefault(); openItem(item); }}><td><div className="activity-name"><span className="file-icon"><Icon name="file"/></span><div><strong>{item.title}</strong><span className="protocol-id">{item.protocol}</span></div></div></td><td>{item.student_name}</td><td className="hours-cell">{hourFormat(item.declared_hours)} h</td><td>{whenLabel(item.submitted_at)}</td></tr>)}</tbody></table></div>}
       <div className="panel-footnote"><Icon name="shield" size={15}/><span>A fila mostra apenas solicitações da sua instituição que aguardam revisão manual.</span></div>
      </section>
      <aside className="next-step"><div className="step-label"><span>NO DETALHE</span><Icon name="file"/></div><h2>Tudo o que a leitura reuniu.</h2><p>Dados da atividade, certificado, leitura do documento, resultado automático e a regra usada.</p><div className="next-step-bottom"><Icon name="shield" size={15}/>Somente a fila da sua instituição</div></aside>
     </div>
     <section className="journey-strip" aria-label="Como a solicitação chega na fila"><div><span className="eyebrow">ATÉ A REVISÃO MANUAL</span><h2>O caminho do envio.</h2></div><div className="journey-item"><span>01</span><div><strong>Leitura</strong><small>O certificado terá os dados extraídos.</small></div></div><div className="journey-item"><span>02</span><div><strong>Análise</strong><small>Os dados serão comparados com a regra.</small></div></div><div className="journey-item"><span>03</span><div><strong>Fila</strong><small>O que não for aprovado chega aqui.</small></div></div></section>
    </>}
  </AppShell>;
}
