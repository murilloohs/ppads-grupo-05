import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { getUserData } from '../services/auth';

export default function Success() {
  const navigate = useNavigate();
  const location = useLocation();

  const user = getUserData();

  const { protocol, formData, fileName } = location.state || {};

  useEffect(() => {
    if (!protocol) {
      navigate('/dashboard');
    }
  }, [protocol, navigate]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  if (!protocol) return null;

  return (
    <div className="app-container">
      <header className="top-bar">
        <div className="logo-area">
          <h1 className="brand-title">ValidaHoras</h1>
          <span className="brand-subtitle">Conclusão Atividade Complementar</span>
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
        <div className="dashboard-grid">
          
          <div className="card card-full">
            <h2 className="card-title" style={{marginBottom: '16px'}}>Solicitação registrada com sucesso</h2>
            <p className="protocol-text">Protocolo gerado: {protocol}</p>
            <p className="card-text text-muted" style={{marginTop: '20px'}}>Status inicial: Em análise</p>
            <p className="card-text text-muted" style={{marginBottom: '24px'}}>
              A análise automática será iniciada em instantes. Você poderá acompanhar atualizações em Minhas solicitações.
            </p>

            <div className="actions-group">
              <button className="btn-primary" onClick={() => navigate('/dashboard')}>
                Ir para Minhas solicitações
              </button>
              <button className="btn-outline" onClick={() => navigate('/nova-atividade')}>
                Enviar outra atividade
              </button>
            </div>
          </div>

          <div className="card card-full">
            <h2 className="card-title">Resumo enviado</h2>
            <div className="summary-list">
              <p>Atividade: {formData.nome}</p>
              <p>Instituição: {formData.instituicao}</p>
              <p>Categoria: {formData.categoria} <span className="separator">|</span> Período: {formData.periodo} <span className="separator">|</span> Carga: {formData.cargaHoraria}</p>
              <p>Documento: {fileName}</p>
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}