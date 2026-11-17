import axios from 'axios';
import { SystemHealth } from '../types';

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('prepgenius_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => Promise.reject(error));

export const healthApi = {
  checkHealth: async (): Promise<SystemHealth> => {
    const response = await api.get<SystemHealth>('/health');
    return response.data;
  },
};

export default api;
