import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getStatus = async () => {
  const response = await api.get('/status');
  return response.data;
};

export const getAnalyze = async () => {
  const response = await api.post('/analyze');
  return response.data;
};

export const getPositions = async () => {
  const response = await api.get('/positions');
  return response.data;
};

export const getSignalsHistory = async (pair = 'EURUSD', days = 7) => {
  const response = await api.get(`/signals/history?pair=${pair}&days=${days}`);
  return response.data;
};

export const startAnalysis = async () => {
  const response = await api.post('/analysis/start');
  return response.data;
};

export const stopAnalysis = async () => {
  const response = await api.post('/analysis/stop');
  return response.data;
};

export const getAnalysisStatus = async () => {
  const response = await api.get('/analysis/status');
  return response.data;
};

export const getSettings = async () => {
  const response = await api.get('/settings');
  return response.data;
};

export const updateSettings = async (settings) => {
  const response = await api.post('/settings/update', settings);
  return response.data;
};

export const getLatestAnalysis = async () => {
  const response = await api.get('/analysis/latest');
  return response.data;
};

export const getRecentTrades = async (limit = 50) => {
  const response = await api.get(`/trades/recent?limit=${limit}`);
  return response.data;
};

export default api;
