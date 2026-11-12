import axios from 'axios';
import type {
  CurrentUser,
  Ticket,
  TicketListResponse,
  TicketPayload,
  TicketQuery,
} from './types';

// Событие, которое слушает App: сессия перестала быть валидной
export const UNAUTHORIZED_EVENT = 'auth:unauthorized';

// Создаем клиент axios.
// По умолчанию бьем по относительному /api: в проде фронтенд и backend
// отдает один сервис (same-origin), а в разработке /api проксирует Vite.
// withCredentials нужен, чтобы браузер отправлял httpOnly-куку с токеном.
const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '/api',
  withCredentials: true,
});

// Если сессия истекла или отозвана — сообщаем об этом App
API.interceptors.response.use(
  (response) => response,
  (error) => {
    const isLoginRequest = error.config?.url?.includes('/login');
    if (error.response?.status === 401 && !isLoginRequest) {
      window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
    }
    return Promise.reject(error);
  }
);

// Функции для работы с API
export const login = (username: string, password: string) =>
  API.post<CurrentUser>('/login', { username, password });

export const logout = () =>
  API.post('/logout');

export const me = () =>
  API.get<CurrentUser>('/me');

export const getTickets = (params: TicketQuery) =>
  API.get<TicketListResponse>('/tickets', { params });

export const createTicket = (data: TicketPayload) =>
  API.post<Ticket>('/tickets', data);

export const updateTicket = (id: number, data: Partial<TicketPayload>) =>
  API.put<Ticket>(`/tickets/${id}`, data);

export const deleteTicket = (id: number) =>
  API.delete(`/tickets/${id}`);

// Сетевая ошибка (запрос не дошел до сервера) — в отличие от ответа с кодом 4xx/5xx
export const isNetworkError = (error: unknown) =>
  axios.isAxiosError(error) && !error.response;

// Достаем текст ошибки, который вернул backend
export const getErrorMessage = (error: unknown, fallback: string) => {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    // При ошибках валидации (422) FastAPI отдает detail массивом
    if (Array.isArray(detail)) {
      const messages = detail
        .map((item: { msg?: string }) => item?.msg)
        .filter((msg): msg is string => Boolean(msg));
      if (messages.length > 0) return messages.join('; ');
    }
  }
  return fallback;
};
