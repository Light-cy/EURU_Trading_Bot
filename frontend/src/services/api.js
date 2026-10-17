import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getAccountInfo = async () => {
  const response = await api.get('/account');
  return response.data;
};

export const getMarketQuote = async () => {
  const response = await api.get('/market/quote');
  return response.data;
};

export const getAccountPerformance = async (days = 30) => {
  const response = await api.get('/account/performance', { params: { days } });
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

export const getLatestAnalysis = async () => {
  const response = await api.get('/analysis/latest');
  return response.data;
};

export const getRecentTrades = async (limit = 50) => {
  const response = await api.get(`/trades/recent?limit=${limit}`);
  return response.data;
};

export default api;
