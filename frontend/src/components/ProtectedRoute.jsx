import { Navigate, useLocation } from 'react-router-dom';
import { getUserData } from '../services/auth';

export default function ProtectedRoute({ children, allowedRole }) {
  const token = localStorage.getItem('token');
  const location = useLocation();

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  const user = getUserData();

  if (allowedRole && user.role !== allowedRole) {
    
    if (user.role === 'Administrador' && location.pathname !== '/admin') return <Navigate to="/admin" replace />;
    if (user.role === 'Avaliador' && location.pathname !== '/avaliador') return <Navigate to="/avaliador" replace />;
    if (user.role === 'Aluno' && location.pathname !== '/dashboard') return <Navigate to="/dashboard" replace />;
    
    localStorage.removeItem('token');
    return <Navigate to="/login" replace />;
  }

  return children;
}