import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getUserData } from '../services/auth';
import { api } from '../services/api';

export default function Dashboard() {
  const navigate = useNavigate();
  const user = getUserData();
  
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);

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
          } else if (statusAtual === 'Correção') {
            corr++;
          }
        });

        setStats({ emAnalise: analise, aprovadas: aprov, correcoes: corr, horasValidadas: horas });

      } catch (error) {
        console.error("Erro ao buscar atividades", error);
      } finally {
        setLoading(false);
      }
    };

    fetchActivities();
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  return (
    <div className="app-container">
      <header className="top-bar">
        <div className="logo-area">
          <h1 className="brand-title">ValidaHoras</h1>
          <span className="brand-subtitle">Resumo das atividades complementares</span>
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
        {loading ? (
          <p>Carregando seus dados...</p>
        ) : (
          <div className="dashboard-grid">
            
            <div className="card">
              <h2 className="card-title">Visão geral</h2>
              <div className="status-badges">
                <span className="badge badge-warning">{stats.emAnalise} Em análise</span>
                <span className="badge badge-success">{stats.aprovadas} Aprovadas</span>
                <span className="badge badge-danger">{stats.correcoes} Correções</span>
              </div>
              <p className="card-text">Horas já validadas: {stats.horasValidadas}h </p>
            </div>

            <div className="card">
              <h2 className="card-title">Ações rápidas</h2>
              <p className="card-text">Inicie um novo envio ou acompanhe suas solicitações.</p>
              <div className="actions-group">
                <button className="btn-primary" onClick={() => navigate('/nova-atividade')}>Nova atividade</button>
                <button className="btn-outline">Minhas solicitações</button>
              </div>
            </div>

            <div className="card card-full">
              <h2 className="card-title">Últimas movimentações</h2>
              {activities.length === 0 ? (
                <p className="card-text text-muted">Você ainda não enviou nenhuma atividade.</p>
              ) : (
                <ul className="activity-list">
                  {activities.slice(-3).reverse().map((act, index) => (
                    <li key={index}>
                      {act.protocol || `ID-${act.id}`} <span className="separator">|</span> {act.title} <span className="separator">|</span> {act.status || 'Em análise'}
                    </li>
                  ))}
                </ul>
              )}
            </div>

          </div>
        )}
      </main>
    </div>
  );
}