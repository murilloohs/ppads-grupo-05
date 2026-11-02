import { NavLink, useNavigate } from 'react-router-dom';
import { getUserData } from '../services/auth';
import Brand from './Brand';
import Icon from './Icon';

const shells = {
  aluno: {
    home: '/dashboard',
    caption: 'ESPAÇO DO ALUNO',
    crumb: 'Meu espaço',
    header: 'Atividades complementares',
    noteTitle: 'Conhecimento em movimento.',
    noteText: 'Cada experiência faz parte da sua formação.',
    links: [
      ['/dashboard', 'grid', 'Visão geral'],
      ['/minhas-solicitacoes', 'file', 'Minhas solicitações'],
      ['/nova-atividade', 'plus', 'Nova atividade'],
    ],
  },
  admin: {
    home: '/admin',
    caption: 'ESPAÇO DO ADMINISTRADOR',
    crumb: 'Administração',
    header: 'Regras de validação',
    noteTitle: 'Critérios claros para cada categoria.',
    noteText: 'Eles orientam a aprovação automática dos documentos.',
    links: [
      ['/admin', 'grid', 'Visão geral'],
    ],
  },
};

export default function AppShell({ children, title, variant = 'aluno' }) {
 const shell = shells[variant] || shells.aluno;
 const user = getUserData();
 const navigate = useNavigate();
 const logout = () => { localStorage.removeItem('token'); navigate('/login'); };
 return <div className="workspace">
  <a className="skip-link" href="#main-content">Pular para o conteúdo</a>
  <aside className="sidebar">
   <NavLink to={shell.home} className="brand-link" aria-label="ValidaHoras — início"><Brand /></NavLink>
   <div className="nav-caption">{shell.caption}</div>
   <nav className="main-nav" aria-label="Navegação principal">
    {shell.links.map(([to, icon, label]) => <NavLink key={to} to={to}><Icon name={icon}/>{label}</NavLink>)}
   </nav>
   <div className="sidebar-note"><span className="note-icon"><Icon name="book"/></span><strong>{shell.noteTitle}</strong><p>{shell.noteText}</p><span className="note-line"/></div>
   <div className="sidebar-bottom"><span className="avatar">{(user.email || 'AL').slice(0,2).toUpperCase()}</span><div><strong>{user.role || 'Minha conta'}</strong><small title={user.email}>{user.email}</small></div><button className="icon-button" onClick={logout} aria-label="Sair da conta" title="Sair da conta"><Icon name="logout" size={18}/></button></div>
  </aside>
  <div className="workspace-body">
   <header className="workspace-header"><div className="breadcrumb"><span>{shell.crumb}</span><Icon name="chevron" size={14}/><strong>{title}</strong></div><span className="header-label"><Icon name="shield" size={16}/>{shell.header}</span></header>
   <main id="main-content" className="page-content">{children}</main>
   <footer className="workspace-footer"><span>ValidaHoras</span><span>Aprender. Registrar. Evoluir.</span></footer>
  </div>
 </div>;
}
