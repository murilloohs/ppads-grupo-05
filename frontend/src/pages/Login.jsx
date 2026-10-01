import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { getUserData } from '../services/auth';
import Brand from '../components/Brand';
import Icon from '../components/Icon';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const formData = new URLSearchParams();
      formData.append('username', email); 
      formData.append('password', password);

      const response = await api.post('/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });

      localStorage.setItem('token', response.data.access_token);
      const user = getUserData();
      
      if (user.role === 'Administrador') {
        navigate('/admin');
      } else if (user.role === 'Avaliador') {
        navigate('/avaliador');
      } else {
        navigate('/dashboard'); 
      }
    } catch (err) {
      console.error(err);
      setError('E-mail ou senha incorretos. Verifique e tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  return <main className="login-layout">
    <section className="login-story"><Brand/><div className="login-story-main"><span className="story-kicker">SEU TEMPO. SEU CONHECIMENTO.</span><h1>Aprendizado<br/>que vira <em>conquista.</em></h1><p>Um lugar para registrar suas experiências e acompanhar suas atividades complementares.</p><div className="brand-emblem" aria-hidden="true"><svg viewBox="0 0 160 160" fill="none"><circle cx="80" cy="80" r="65" stroke="currentColor" strokeWidth="1"/><circle cx="80" cy="80" r="47" stroke="currentColor" strokeWidth="1" strokeDasharray="2 9"/><path d="M80 38v44l25 16M108 50l12 12 24-30" stroke="currentColor" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round"/></svg><span>cada hora<br/><strong>conta.</strong></span></div></div><div className="login-story-footer"><span>ValidaHoras</span><span>Aprender. Registrar. Evoluir.</span></div></section>
    <section className="login-form-side"><div className="mobile-brand"><Brand/></div><div className="login-card"><span className="login-icon"><Icon name="book" size={25}/></span><span className="eyebrow">BEM-VINDO AO SEU ESPAÇO</span><h2>Bom ter você aqui.</h2><p className="login-subtitle">Entre para acompanhar seu percurso acadêmico.</p><form onSubmit={handleSubmit}>
      {error && <div className="error-message" role="alert">{error}</div>}
      <div className="form-group"><label htmlFor="email">E-mail institucional</label><input id="email" type="email" autoComplete="username" placeholder="seu.email@instituicao.br" value={email} onChange={e => setEmail(e.target.value)} required/></div>
      <div className="form-group"><label htmlFor="password">Senha</label><input id="password" type="password" autoComplete="current-password" placeholder="Digite sua senha" value={password} onChange={e => setPassword(e.target.value)} required/></div>
      <button type="submit" className="btn-primary login-submit" disabled={loading}>{loading ? 'Entrando...' : 'Entrar na minha conta'}</button>
    </form><div className="login-note"><Icon name="shield" size={17}/><span>Suas atividades, em um espaço só seu.</span></div></div><span className="login-footnote">Plataforma de atividades complementares</span></section>
  </main>;
}
