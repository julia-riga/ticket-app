import React, { useState, useEffect } from 'react';
import type { Ticket } from './types';
import { login, getTickets, createTicket, updateTicket, deleteTicket, saveToken, getToken, removeToken } from './api';
import './App.css';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  
  // Фильтры
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  
  // Формы
  const [showForm, setShowForm] = useState(false);
  const [editingTicket, setEditingTicket] = useState<Ticket | null>(null);

  // Проверяем вход при загрузке
  useEffect(() => {
    const token = getToken();
    if (token) {
      setIsLoggedIn(true);
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        setIsAdmin(payload.sub === 'admin');
      } catch {}
    }
  }, []);

  // Загружаем заявки
  useEffect(() => {
    if (isLoggedIn) {
      loadTickets();
    }
  }, [isLoggedIn, page, search, statusFilter, priorityFilter]);

  const loadTickets = async () => {
    setLoading(true);
    setError('');
    try {
      const params: any = { page, page_size: 10 };
      if (search) params.search = search;
      if (statusFilter) params.status = statusFilter;
      if (priorityFilter) params.priority = priorityFilter;
      
      const res = await getTickets(params);
      setTickets(res.data.items);
      setTotalPages(res.data.pages);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка загрузки');
    } finally {
      setLoading(false);
    }
  };

  // Логин
  const handleLogin = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const username = (form.elements.namedItem('username') as HTMLInputElement).value;
    const password = (form.elements.namedItem('password') as HTMLInputElement).value;
    try {
      const res = await login(username, password);
      saveToken(res.data.access_token);
      setIsLoggedIn(true);
      setIsAdmin(username === 'admin');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка входа');
    }
  };

  // Выход
  const handleLogout = () => {
    removeToken();
    setIsLoggedIn(false);
    setIsAdmin(false);
  };

  // Создание
  const handleCreate = async (data: any) => {
    await createTicket(data);
    setShowForm(false);
    loadTickets();
  };

  // Обновление
  const handleUpdate = async (id: number, data: any) => {
    await updateTicket(id, data);
    setEditingTicket(null);
    loadTickets();
  };

  // Удаление
  const handleDelete = async (id: number) => {
    if (!window.confirm('Удалить заявку?')) return;
    try {
      await deleteTicket(id);
      loadTickets();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Ошибка удаления');
    }
  };

  // Смена статуса
  const handleStatusChange = async (ticket: Ticket, newStatus: string) => {
    if (ticket.status === 'done') {
      alert('Нельзя менять статус у выполненных заявок');
      return;
    }
    try {
      await updateTicket(ticket.id, { status: newStatus });
      loadTickets();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Ошибка');
    }
  };

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
        <input placeholder="Поиск..." value={search} onChange={e => setSearch(e.target.value)} />
        <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
          <option value="">Все статусы</option>
          <option value="new">Новая</option>
          <option value="in_progress">В работе</option>
          <option value="done">Готово</option>
        </select>
        <select value={priorityFilter} onChange={e => setPriorityFilter(e.target.value)}>
          <option value="">Любой приоритет</option>
          <option value="low">Низкий</option>
          <option value="normal">Нормальный</option>
          <option value="high">Высокий</option>
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
                <span className={`tag status-${t.status}`}>{t.status}</span>
                <span className={`tag priority-${t.priority}`}>{t.priority}</span>
              </div>
            </div>
            {t.description && <p>{t.description}</p>}
            <div className="ticket-foot">
              <small>{new Date(t.created_at).toLocaleString()}</small>
              <div>
                <select value={t.status} onChange={e => handleStatusChange(t, e.target.value)} disabled={t.status === 'done'}>
                  <option value="new">Новая</option>
                  <option value="in_progress">В работе</option>
                  <option value="done">Готово</option>
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

// Компонент формы
function TicketForm({ ticket, onSubmit, onCancel }: any) {
  const [title, setTitle] = useState(ticket?.title || '');
  const [description, setDescription] = useState(ticket?.description || '');
  const [priority, setPriority] = useState(ticket?.priority || 'normal');
  const [status, setStatus] = useState(ticket?.status || 'new');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ title, description: description || null, priority, status });
  };

  return (
    <form className="form" onSubmit={handleSubmit}>
      <h2>{ticket ? 'Редактировать' : 'Создать'} заявку</h2>
      <input placeholder="Заголовок (3-120 символов)" value={title} onChange={e => setTitle(e.target.value)} required minLength={3} maxLength={120} />
      <textarea placeholder="Описание (необязательно)" value={description} onChange={e => setDescription(e.target.value)} maxLength={1000} />
      <select value={priority} onChange={e => setPriority(e.target.value)}>
        <option value="low">Низкий приоритет</option>
        <option value="normal">Нормальный приоритет</option>
        <option value="high">Высокий приоритет</option>
      </select>
      {!ticket && (
        <select value={status} onChange={e => setStatus(e.target.value)}>
          <option value="new">Новая</option>
          <option value="in_progress">В работе</option>
          <option value="done">Готово</option>
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
