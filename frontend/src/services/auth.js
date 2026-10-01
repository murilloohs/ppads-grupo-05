import { jwtDecode } from 'jwt-decode';

export const getUserData = () => {
  const token = localStorage.getItem('token');
  if (!token) return { email: '', role: '' };

  try {
    const decoded = jwtDecode(token);
    
    if (!decoded.exp || decoded.exp * 1000 <= Date.now()) {
      localStorage.removeItem('token');
      return { email: '', role: '' };
    }
    const rawRole = String(decoded.role || 'Aluno').toLowerCase();
    
    let roleFormatado = 'Aluno';
    
    if (rawRole.includes('admin')) {
      roleFormatado = 'Administrador';
    } else if (rawRole.includes('avaliador') || rawRole.includes('evaluator') || rawRole === 'coordinator') {
      roleFormatado = 'Avaliador';
    }

    return { 
      email: decoded.email || '', 
      role: roleFormatado 
    };
  } catch (error) {
    console.error("Erro ao ler o token:", error);
    return { email: '', role: '' };
  }
};