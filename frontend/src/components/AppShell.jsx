import { NavLink, useNavigate } from 'react-router-dom';
import { getUserData } from '../services/auth';
import Brand from './Brand';
import Icon from './Icon';

export default function AppShell({ children, title }) {
 const user = getUserData();
 const navigate = useNavigate();
 const logout = () => { localStorage.removeItem('token'); navigate('/login'); };
 return <div className="workspace">
  <a className="skip-link" href="#main-content">Pular para o conteúdo</a>
  <aside className="sidebar">
   <NavLink to="/dashboard" className="brand-link" aria-label="ValidaHoras — início"><Brand /></NavLink>
   <div className="nav-caption">ESPAÇO DO ALUNO</div>
   <nav className="main-nav" aria-label="Navegação principal">
    <NavLink to="/dashboard"><Icon name="grid"/>Visão geral</NavLink>
    <NavLink to="/minhas-solicitacoes"><Icon name="file"/>Minhas solicitações</NavLink>
    <NavLink to="/nova-atividade"><Icon name="plus"/>Nova atividade</NavLink>
   </nav>
   <div className="sidebar-note"><span className="note-icon"><Icon name="book"/></span><strong>Conhecimento em movimento.</strong><p>Cada experiência faz parte da sua formação.</p><span className="note-line"/></div>
   <div className="sidebar-bottom"><span className="avatar">{(user.email || 'AL').slice(0,2).toUpperCase()}</span><div><strong>{user.role || 'Minha conta'}</strong><small title={user.email}>{user.email}</small></div><button className="icon-button" onClick={logout} aria-label="Sair da conta" title="Sair da conta"><Icon name="logout" size={18}/></button></div>
  </aside>
  <div className="workspace-body">
   <header className="workspace-header"><div className="breadcrumb"><span>Meu espaço</span><Icon name="chevron" size={14}/><strong>{title}</strong></div><span className="header-label"><Icon name="shield" size={16}/>Atividades complementares</span></header>
   <main id="main-content" className="page-content">{children}</main>
   <footer className="workspace-footer"><span>ValidaHoras</span><span>Aprender. Registrar. Evoluir.</span></footer>
  </div>
 </div>;
}
