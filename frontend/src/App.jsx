import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import NewActivity from './pages/NewActivity';
import Success from './pages/Success';
import AdminDashboard from './pages/AdminDashboard';
import RequestDetail from './pages/RequestDetail';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        
        <Route path="/dashboard" element={
          <ProtectedRoute allowedRole="Aluno">
            <Dashboard />
          </ProtectedRoute>
        } />
        <Route path="/minhas-solicitacoes" element={<ProtectedRoute allowedRole="Aluno"><Dashboard all /></ProtectedRoute>} />
        <Route path="/minhas-solicitacoes/:activityId" element={<ProtectedRoute allowedRole="Aluno"><RequestDetail /></ProtectedRoute>} />
        <Route path="/nova-atividade" element={
          <ProtectedRoute allowedRole="Aluno">
            <NewActivity />
          </ProtectedRoute>
        } />
        <Route path="/sucesso" element={
          <ProtectedRoute allowedRole="Aluno">
            <Success />
          </ProtectedRoute>
        } />

        <Route path="/avaliador" element={
          <ProtectedRoute allowedRole="Avaliador">
            <div>Dashboard do Avaliador</div>
          </ProtectedRoute>
        } />

        <Route path="/admin" element={
          <ProtectedRoute allowedRole="Administrador">
            <AdminDashboard />
          </ProtectedRoute>
        } />
        
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;