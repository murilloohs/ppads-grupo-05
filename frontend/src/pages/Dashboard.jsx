import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AppShell from '../components/AppShell';
import Icon from '../components/Icon';
import { api } from '../services/api';

export default function Dashboard({ all = false }) {
  const navigate = useNavigate();

  
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [stats, setStats] = useState({ emAnalise: 0, aprovadas: 0, correcoes: 0, horasValidadas: 0 });

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }

    const fetchActivities = async () => {
      try {
        const response = await api.get('/activities/', {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        const data = response.data;
        setActivities(data);

        let analise = 0, aprov = 0, corr = 0, horas = 0;
        
        data.forEach(act => {
          const statusAtual = act.status || 'Em análise';

          if (statusAtual === 'Em análise') {
            analise++;
          } else if (statusAtual === 'Aprovada') {
            aprov++;
            horas += Number(act.declared_hours) || 0; 
          } else if (statusAtual === 'Correções') {
            corr++;
          }
        });

        setStats({ emAnalise: analise, aprovadas: aprov, correcoes: corr, horasValidadas: horas });

      } catch (error) {
        console.error("Erro ao buscar atividades", error);
        setError("Não foi possível carregar as solicitações. Atualize a página para tentar novamente.");
      } finally {
        setLoading(false);
      }
    };

    fetchActivities();
  }, [navigate]);

  const rows = all ? [...activities].reverse() : activities.slice(-3).reverse();
  const hourFormat = value => Number(value).toLocaleString('pt-BR', { maximumFractionDigits: 2 });
  const statusClass = value => ({ 'Em análise': 'pending', 'Aprovada': 'approved', 'Correções': 'correction', 'Reprovada': 'rejected' }[value] || 'draft');
  return <AppShell title={all ? 'Minhas solicitações' : 'Visão geral'}>
    <div className="page-heading"><div><span className="eyebrow">SEU PERCURSO ACADÊMICO</span><h1>{all ? 'Minhas solicitações' : 'Cada experiência conta.'}</h1><p>{all ? 'Seus envios, protocolos e status em um só lugar.' : 'Acompanhe suas horas e dê o próximo passo na sua formação.'}</p></div><button className="btn-primary" onClick={() => navigate('/nova-atividade')}><Icon name="plus"/>Nova atividade</button></div>
    {error && <div className="error-message" role="alert">{error}</div>}
    {loading ? <div className="loading-state" role="status"><span className="loading-spinner"/>Carregando suas atividades...</div> : <>
     <section className="stats-grid" aria-label="Resumo das atividades">
      <div className="stat-card stat-featured"><div className="stat-top"><span>Horas validadas</span><Icon name="clock"/></div><strong className="stat-number">{hourFormat(stats.horasValidadas)}<small>h</small></strong><span className="stat-caption">Aprendizado reconhecido</span><div className="stat-decoration" aria-hidden="true"/></div>
      <div className="stat-card"><div className="stat-top"><span>Em análise</span><span className="stat-icon pending"><Icon name="clock"/></span></div><strong className="stat-number">{stats.emAnalise.toString().padStart(2,'0')}</strong><span className="stat-caption">Aguardando avaliação</span></div>
      <div className="stat-card"><div className="stat-top"><span>Aprovadas</span><span className="stat-icon approved"><Icon name="circleCheck"/></span></div><strong className="stat-number">{stats.aprovadas.toString().padStart(2,'0')}</strong><span className="stat-caption">Atividades reconhecidas</span></div>
      <div className="stat-card"><div className="stat-top"><span>Correções</span><span className="stat-icon correction"><Icon name="edit"/></span></div><strong className="stat-number">{stats.correcoes.toString().padStart(2,'0')}</strong><span className="stat-caption">Precisam da sua atenção</span></div>
     </section>
     <div className={all ? 'dashboard-lower list-view' : 'dashboard-lower'}>
      <section className="panel requests-panel"><div className="panel-heading"><div><h2>{all ? 'Todas as solicitações' : 'Atividades recentes'}</h2><p>{all ? `${activities.length} atividade(s) registrada(s)` : 'Acompanhe seus últimos envios.'}</p></div>{!all && <button className="text-button" onClick={() => navigate('/minhas-solicitacoes')}>Ver todas</button>}</div>
       {rows.length === 0 ? <div className="empty-state"><span className="empty-icon"><Icon name="file" size={30}/></span><h3>Seu próximo aprendizado começa aqui.</h3><p>Registre uma atividade e acompanhe o envio por aqui.</p><button className="btn-outline" onClick={() => navigate('/nova-atividade')}>Cadastrar primeira atividade</button></div> : <div className="table-scroll"><table className="activity-table"><thead><tr><th>ATIVIDADE / PROTOCOLO</th><th>CARGA</th><th>STATUS</th></tr></thead><tbody>{rows.map(act => <tr key={act.id}><td><div className="activity-name"><span className="file-icon"><Icon name="file"/></span><div><strong>{act.title}</strong><span className="protocol-id">{act.protocol || `ID-${act.id}`}</span></div></div></td><td className="hours-cell">{hourFormat(act.declared_hours)} h</td><td><span className={`status-badge ${statusClass(act.status)}`}>{act.status || 'Rascunho'}</span></td></tr>)}</tbody></table></div>}
       <div className="panel-footnote"><Icon name="shield" size={15}/><span>Somente as suas atividades aparecem neste espaço.</span></div>
      </section>
      {!all && <aside className="next-step"><div className="step-label"><span>PRÓXIMO PASSO</span><Icon name="plus"/></div><h2>Mais uma conquista<br/>para registrar?</h2><p>Cursos, eventos ou projetos. Reúna seu comprovante e envie uma nova atividade.</p><button className="btn-outline" onClick={() => navigate('/nova-atividade')}><Icon name="upload" size={17}/>Enviar atividade</button><div className="next-step-bottom"><Icon name="file" size={15}/>PDF, JPG ou PNG · até 10 MB</div></aside>}
     </div>
     {!all && <section className="journey-strip" aria-label="Como funciona"><div><span className="eyebrow">DO APRENDIZADO AO REGISTRO</span><h2>Um caminho simples.</h2></div><div className="journey-item"><span>01</span><div><strong>Cadastre</strong><small>Conte o que você aprendeu.</small></div></div><div className="journey-item"><span>02</span><div><strong>Comprove</strong><small>Anexe seu documento.</small></div></div><div className="journey-item"><span>03</span><div><strong>Acompanhe</strong><small>Consulte o protocolo e o status.</small></div></div></section>}
    </>}
  </AppShell>;
}
