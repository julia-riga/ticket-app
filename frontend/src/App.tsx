import React, { useState, useEffect, useCallback, useRef } from 'react';
import type { Ticket, TicketPayload, TicketPriority, TicketStatus } from './types';
import {
  UNAUTHORIZED_EVENT,
  login,
  logout,
  me,
  getTickets,
  createTicket,
  updateTicket,
  deleteTicket,
  getErrorMessage,
  isNetworkError,
} from './api';
import './App.css';

// Единственный источник подписей: и теги в карточке, и селекты рендерятся отсюда
const STATUS_LABELS: Record<TicketStatus, string> = {
  new: 'Новая',
  in_progress: 'В работе',
  done: 'Готово',
};

const PRIORITY_LABELS: Record<TicketPriority, string> = {
  low: 'Низкий',
  normal: 'Обычный',
  high: 'Высокий',
};

const STATUS_OPTIONS = Object.entries(STATUS_LABELS) as [TicketStatus, string][];
const PRIORITY_OPTIONS = Object.entries(PRIORITY_LABELS) as [TicketPriority, string][];
// Заявку нельзя создать сразу закрытой — статус 'done' в форме создания не предлагаем
const CREATE_STATUS_OPTIONS = STATUS_OPTIONS.filter(([value]) => value !== 'done');

function App() {
  // null — сессия еще проверяется. Токен лежит в httpOnly-куке,
  // поэтому JS не может узнать о ней сам: спрашиваем backend.
  const [isLoggedIn, setIsLoggedIn] = useState<boolean | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // Фильтры
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<TicketStatus | ''>('');
  const [priorityFilter, setPriorityFilter] = useState<TicketPriority | ''>('');

  // Формы
  const [showForm, setShowForm] = useState(false);
  const [editingTicket, setEditingTicket] = useState<Ticket | null>(null);

  // Ищем заявки только после паузы в наборе
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search), 400);
    return () => clearTimeout(timer);
  }, [search]);

  // Пока идёт первичная проверка сессии, событие 401 игнорируем:
  // сообщение «Сессия истекла» здесь неуместно, экран входа покажем сами
  const sessionChecked = useRef(false);

  // Восстанавливаем сессию при загрузке: спрашиваем пользователя у backend
  useEffect(() => {
    let cancelled = false;
    me()
      .then(res => {
        if (cancelled) return;
        setError('');
        setIsLoggedIn(true);
        setIsAdmin(res.data.is_admin);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setIsLoggedIn(false);
        // Отличаем «не залогинен» от «сервер недоступен»
        if (isNetworkError(err)) {
          setError('Сервер недоступен, проверьте, что backend запущен');
        }
      })
      .finally(() => {
        sessionChecked.current = true;
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Если токен истек — возвращаемся на экран входа
  useEffect(() => {
    const handleUnauthorized = () => {
      if (!sessionChecked.current) return;
      setIsLoggedIn(false);
      setIsAdmin(false);
      setError('Сессия истекла, войдите заново');
    };
    window.addEventListener(UNAUTHORIZED_EVENT, handleUnauthorized);
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, handleUnauthorized);
  }, []);

  // Номер последнего запроса: ответы устаревших запросов игнорируем,
  // иначе при быстром переключении страниц старый ответ перезапишет новый
  const lastRequestId = useRef(0);

  const loadTickets = useCallback(async () => {
    const requestId = ++lastRequestId.current;
    setLoading(true);
    setError('');
    try {
      const res = await getTickets({
        page,
        page_size: 10,
        search: debouncedSearch || undefined,
        status: statusFilter || undefined,
        priority: priorityFilter || undefined,
      });
      if (requestId !== lastRequestId.current) return;
      setTickets(res.data.items);
      setTotalPages(res.data.pages);
      // Если страница опустела (удалили записи) — вернемся на предыдущую
      if (res.data.items.length === 0 && page > 1) {
        setPage(page - 1);
      }
    } catch (err) {
      if (requestId !== lastRequestId.current) return;
      setError(getErrorMessage(err, 'Ошибка загрузки'));
    } finally {
      if (requestId === lastRequestId.current) {
        setLoading(false);
      }
    }
  }, [page, debouncedSearch, statusFilter, priorityFilter]);

  // Загружаем заявки
  useEffect(() => {
    if (isLoggedIn) {
      // Загрузка данных в эффекте — это легитимный сайд-эффект:
      // setState здесь происходит в async-колбэках запроса, а не в теле эффекта.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      loadTickets();
    }
  }, [isLoggedIn, loadTickets]);

  // Логин
  const handleLogin = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const username = (form.elements.namedItem('username') as HTMLInputElement).value;
    const password = (form.elements.namedItem('password') as HTMLInputElement).value;
    try {
      const res = await login(username, password);
      // Токен уже в httpOnly-куке, в JS его хранить не нужно
      setIsLoggedIn(true);
      setIsAdmin(res.data.is_admin);
      setError('');
    } catch (err) {
      setError(getErrorMessage(err, 'Ошибка входа'));
    }
  };

  // Выход
  const handleLogout = async () => {
    try {
      await logout();
    } catch {
      // даже если запрос не прошел — локально сессию закрываем
    }
    setIsLoggedIn(false);
    setIsAdmin(false);
  };

  // Создание
  const handleCreate = async (data: TicketPayload) => {
    try {
      await createTicket(data);
      setShowForm(false);
      loadTickets();
    } catch (err) {
      setError(getErrorMessage(err, 'Ошибка создания заявки'));
    }
  };

  // Обновление
  const handleUpdate = async (id: number, data: Partial<TicketPayload>) => {
    try {
      await updateTicket(id, data);
      setEditingTicket(null);
      loadTickets();
    } catch (err) {
      setError(getErrorMessage(err, 'Ошибка обновления заявки'));
    }
  };

  // Удаление
  const handleDelete = async (id: number) => {
    if (!window.confirm('Удалить заявку?')) return;
    try {
      await deleteTicket(id);
      loadTickets();
    } catch (err) {
      setError(getErrorMessage(err, 'Ошибка удаления'));
    }
  };

  // Смена статуса
  const handleStatusChange = async (ticket: Ticket, newStatus: TicketStatus) => {
    if (ticket.status === 'done') {
      setError('Нельзя менять статус у выполненных заявок');
      return;
    }
    try {
      await updateTicket(ticket.id, { status: newStatus });
      loadTickets();
    } catch (err) {
      setError(getErrorMessage(err, 'Ошибка смены статуса'));
    }
  };

  // Пока проверяем сессию — держим заглушку, чтобы не мигал экран входа
  if (isLoggedIn === null) {
    return <div className="loading">Загрузка...</div>;
  }

  // Экран логина
  if (!isLoggedIn) {
    return (
      <div className="login-page">
        <form onSubmit={handleLogin} className="login-form">
          <h2>Вход в систему</h2>
          {error && <div className="error">{error}</div>}
          <input name="username" placeholder="Логин (admin)" defaultValue="admin" required />
          <input name="password" type="password" placeholder="Пароль (admin)" defaultValue="admin" required />
          <button type="submit">Войти</button>
        </form>
      </div>
    );
  }

  // Главный экран
  return (
    <div className="app">
      <header>
        <h1>Система заявок</h1>
        <div>
          {isAdmin && <span className="badge">Admin</span>}
          <button onClick={handleLogout}>Выйти</button>
        </div>
      </header>

      <div className="controls">
        <button onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Отмена' : '+ Новая заявка'}
        </button>
      </div>

      {showForm && <TicketForm onSubmit={handleCreate} onCancel={() => setShowForm(false)} />}
      {editingTicket && <TicketForm ticket={editingTicket} onSubmit={(d) => handleUpdate(editingTicket.id, d)} onCancel={() => setEditingTicket(null)} />}

      <div className="filters">
        <input placeholder="Поиск..." value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} />
        <select value={statusFilter} onChange={e => { setStatusFilter(e.target.value as TicketStatus | ''); setPage(1); }}>
          <option value="">Все статусы</option>
          {STATUS_OPTIONS.map(([value, label]) => (
            <option key={value} value={value}>{label}</option>
          ))}
        </select>
        <select value={priorityFilter} onChange={e => { setPriorityFilter(e.target.value as TicketPriority | ''); setPage(1); }}>
          <option value="">Любой приоритет</option>
          {PRIORITY_OPTIONS.map(([value, label]) => (
            <option key={value} value={value}>{label}</option>
          ))}
        </select>
      </div>

      {error && <div className="error">{error}</div>}
      {loading && <div className="loading">Загрузка...</div>}

      {!loading && tickets.length === 0 && <div className="empty">Заявок нет</div>}

      <div className="tickets">
        {tickets.map(t => (
          <div key={t.id} className="ticket">
            <div className="ticket-head">
              <h3>{t.title}</h3>
              <div>
                <span className={`tag status-${t.status}`}>{STATUS_LABELS[t.status]}</span>
                <span className={`tag priority-${t.priority}`}>{PRIORITY_LABELS[t.priority]}</span>
              </div>
            </div>
            {t.description && <p>{t.description}</p>}
            <div className="ticket-foot">
              <small>{new Date(t.created_at).toLocaleString()}</small>
              <div>
                <select value={t.status} onChange={e => handleStatusChange(t, e.target.value as TicketStatus)} disabled={t.status === 'done'}>
                  {STATUS_OPTIONS.map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
                {t.status !== 'done' && (
                  <>
                    <button onClick={() => setEditingTicket(t)}>Ред.</button>
                    {isAdmin && <button className="danger" onClick={() => handleDelete(t.id)}>Удалить</button>}
                  </>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {totalPages > 1 && (
        <div className="pagination">
          <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>Назад</button>
          <span>Стр. {page} из {totalPages}</span>
          <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}>Вперед</button>
        </div>
      )}
    </div>
  );
}

interface TicketFormProps {
  ticket?: Ticket;
  onSubmit: (data: TicketPayload) => void;
  onCancel: () => void;
}

// Компонент формы
function TicketForm({ ticket, onSubmit, onCancel }: TicketFormProps) {
  const [title, setTitle] = useState(ticket?.title ?? '');
  const [description, setDescription] = useState(ticket?.description ?? '');
  const [priority, setPriority] = useState<TicketPriority>(ticket?.priority ?? 'normal');
  const [status, setStatus] = useState<TicketStatus>(ticket?.status ?? 'new');

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    onSubmit({ title, description: description || null, priority, status });
  };

  return (
    <form className="form" onSubmit={handleSubmit}>
      <h2>{ticket ? 'Редактировать' : 'Создать'} заявку</h2>
      <input placeholder="Заголовок (3-120 символов)" value={title} onChange={e => setTitle(e.target.value)} required minLength={3} maxLength={120} />
      <textarea placeholder="Описание (необязательно)" value={description} onChange={e => setDescription(e.target.value)} maxLength={1000} />
      <select value={priority} onChange={e => setPriority(e.target.value as TicketPriority)}>
        {PRIORITY_OPTIONS.map(([value, label]) => (
          <option key={value} value={value}>{label} приоритет</option>
        ))}
      </select>
      {!ticket && (
        <select value={status} onChange={e => setStatus(e.target.value as TicketStatus)}>
          {CREATE_STATUS_OPTIONS.map(([value, label]) => (
            <option key={value} value={value}>{label}</option>
          ))}
        </select>
      )}
      <div>
        <button type="submit">{ticket ? 'Обновить' : 'Создать'}</button>
        <button type="button" onClick={onCancel}>Отмена</button>
      </div>
    </form>
  );
}

export default App;
