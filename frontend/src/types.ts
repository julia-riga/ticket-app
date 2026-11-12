export type TicketStatus = 'new' | 'in_progress' | 'done';
export type TicketPriority = 'low' | 'normal' | 'high';

export interface Ticket {
  id: number;
  title: string;
  description: string | null;
  status: TicketStatus;
  priority: TicketPriority;
  created_at: string;
  updated_at: string | null;
}

export interface TicketPayload {
  title: string;
  description: string | null;
  status: TicketStatus;
  priority: TicketPriority;
}

export interface TicketQuery {
  page: number;
  page_size: number;
  search?: string;
  status?: TicketStatus | '';
  priority?: TicketPriority | '';
}

export interface TicketListResponse {
  items: Ticket[];
  total: number;
  page: number;
  pages: number;
}

export interface CurrentUser {
  username: string;
  is_admin: boolean;
}
