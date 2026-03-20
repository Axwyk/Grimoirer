import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// Players
export const getPlayers = (search = '') =>
  api.get('/players/', { params: search ? { search } : {} });

export const getPlayer = (id) => api.get(`/players/${id}/`);

export const getPlayerStats = (id) => api.get(`/players/${id}/stats/`);

// Ranking
export const getRanking = () => api.get('/ranking/');

// Battles
export const getBattles = () => api.get('/battles/');

export const getBattle = (id) => api.get(`/battles/${id}/`);

// Stats
export const getStats = () => api.get('/stats/');

export default api;
