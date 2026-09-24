import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import NewActivity from './pages/NewActivity';
import Success from './pages/Success';
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
            <div>Configurações do Administrador</div>
          </ProtectedRoute>
        } />
        
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;