import axios from 'axios';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
});
api.interceptors.response.use(response => response, error => {
  if ([401, 403].includes(error.response?.status) && !error.config?.url?.includes('/auth/login')) {
    localStorage.removeItem('token');
    window.location.assign('/login');
  }
  return Promise.reject(error);
});
