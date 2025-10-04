const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:4000/api';

async function fetchJSON<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    cache: 'no-store',
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {})
    }
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`API ${response.status}: ${body}`);
  }

  return (await response.json()) as T;
}

export interface ReportListItem {
  id: string;
  name: string;
  period: string;
  status: string;
  submittedAt: string;
}

export interface MessageListItem {
  id: string;
  subject: string;
  counterpart: string;
  updatedAt: string;
}

export interface AnnouncementListItem {
  id: string;
  title: string;
  targetAudience: string;
  publishedAt: string;
  acknowledgementRate: number;
}

export interface EntityListItem {
  id: string;
  name: string;
  category: string;
  krs?: string;
  updatedAt: string;
}

export interface CaseListItem {
  id: string;
  reference: string;
  topic: string;
  status: string;
  updatedAt: string;
}

export interface LibraryItem {
  id: string;
  title: string;
  category: string;
  updatedAt: string;
  downloadUrl: string;
}

export interface FAQItem {
  id: string;
  question: string;
  answer: string;
  updatedAt: string;
}

export const api = {
  health: () => fetchJSON<{ status: string }>('/health'),
  reports: () => fetchJSON<ReportListItem[]>('/communication/reports'),
  messages: () => fetchJSON<MessageListItem[]>('/communication/messages'),
  cases: () => fetchJSON<CaseListItem[]>('/communication/cases'),
  announcements: () => fetchJSON<AnnouncementListItem[]>('/communication/announcements'),
  library: () => fetchJSON<LibraryItem[]>('/communication/library'),
  faq: () => fetchJSON<FAQItem[]>('/communication/faq'),
  entities: () => fetchJSON<EntityListItem[]>('/communication/entities')
};
