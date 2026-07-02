import axios from 'axios';

// Создаем клиент axios
const API = axios.create({
  baseURL: 'http://localhost:8000/api',
});

// Добавляем токен к каждому запросу автоматически
API.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Функции для работы с API
export const login = (username: string, password: string) =>
  API.post('/login', { username, password });

export const getTickets = (params: any) =>
  API.get('/tickets', { params });

export const createTicket = (data: any) =>
  API.post('/tickets', data);

export const updateTicket = (id: number, data: any) =>
  API.put(`/tickets/${id}`, data);

export const deleteTicket = (id: number) =>
  API.delete(`/tickets/${id}`);

export const saveToken = (token: string) =>
  localStorage.setItem('token', token);

export const getToken = () =>
  localStorage.getItem('token');

export const removeToken = () =>
  localStorage.removeItem('token');