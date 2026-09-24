import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { getUserData } from '../services/auth';

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

  return (
    <div className="app-container">
      <header className="top-bar">
        <div className="logo-area">
          <h1 className="brand-title">ValidaHoras</h1>
          <span className="brand-subtitle">Autenticação por perfil</span>
        </div>
        <div className="badge-acesso">Acesso</div>
      </header>

      <main className="main-content">
        <div className="login-card">
          <h2 className="login-title">Entrar no ValidaHoras</h2>
          <p className="login-subtitle">Acesso para aluno, avaliador e administrador acadêmico.</p>

          <form onSubmit={handleSubmit} className="login-form">
            {error && <div className="error-message">{error}</div>}

            <div className="form-group">
              <label>E-mail institucional</label>
              <input
                type="email"
                placeholder="nome.sobrenome@aluno.mackenzie.br"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label>Senha</label>
              <input
                type="password"
                placeholder="••••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            <div className="form-actions">
              <button type="submit" className="btn-entrar" disabled={loading}>
                {loading ? 'Entrando...' : 'Entrar'}
              </button>
            </div>
          </form>
        </div>
      </main>
    </div>
  );
}