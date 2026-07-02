export interface Ticket {
    id: number;
    title: string;
    description: string | null;
    status: 'new' | 'in_progress' | 'done';
    priority: 'low' | 'normal' | 'high';
    created_at: string;
    updated_at: string | null;
  }
  
  export interface TicketListResponse {
    items: Ticket[];
    total: number;
    page: number;
    pages: number;
  }