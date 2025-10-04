export type UserRole =
  | 'system_admin'
  | 'supervisor'
  | 'analyst'
  | 'communication_officer'
  | 'auditor'
  | 'entity_admin'
  | 'submitter'
  | 'representative'
  | 'read_only';

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  role_display: string;
  phone_number: string;
  department: string;
  position_title: string;
  preferred_language: string;
  is_active: boolean;
  is_staff: boolean;
  is_internal: boolean;
}

export interface RegulatedEntity {
  id: number;
  name: string;
  registration_number: string;
  sector: string;
  address: string;
  postal_code: string;
  city: string;
  country: string;
  contact_email: string;
  contact_phone: string;
  website?: string;
  status: string;
  data_source?: string;
  last_verified_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReportTimelineEntry {
  id: number;
  status: string;
  notes: string;
  created_at: string;
  created_by?: User | null;
}

export interface Report {
  id: number;
  entity: RegulatedEntity;
  title: string;
  report_type: string;
  period_start: string;
  period_end: string;
  status: string;
  submitted_at?: string | null;
  validated_at?: string | null;
  validation_errors?: string;
  comments?: string;
  submitted_by?: User | null;
  timeline: ReportTimelineEntry[];
  created_at: string;
  updated_at: string;
}

export interface CaseTimelineEntry {
  id: number;
  status: string;
  notes: string;
  created_at: string;
  created_by?: User | null;
}

export interface CaseItem {
  id: number;
  entity: RegulatedEntity;
  reference_code: string;
  title: string;
  description: string;
  status: string;
  assigned_to?: User | null;
  due_date?: string | null;
  opened_at: string;
  closed_at?: string | null;
  timeline: CaseTimelineEntry[];
  updated_at: string;
}

export interface Message {
  id: number;
  sender: User | null;
  body: string;
  attachments: string[];
  is_internal_note: boolean;
  created_at: string;
}

export interface MessageThread {
  id: number;
  entity: RegulatedEntity;
  subject: string;
  created_by?: User | null;
  is_internal_only: boolean;
  participants: User[];
  created_at: string;
  updated_at: string;
  messages: Message[];
}

export interface Announcement {
  id: number;
  title: string;
  summary: string;
  content: string;
  published_at: string;
  expires_at?: string | null;
  requires_acknowledgement: boolean;
  target_roles: string[];
  acknowledgement_rate: number;
}

export interface LibraryDocument {
  id: number;
  title: string;
  category: string;
  version: string;
  published_at: string;
  description: string;
  document_url: string;
  is_mandatory: boolean;
}

export interface FaqEntry {
  id: number;
  question: string;
  answer: string;
  category?: string;
  order: number;
  is_active: boolean;
  updated_at: string;
}

export interface ProfileResponse {
  user: User;
  memberships: Array<{
    id: number;
    role: string;
    is_primary: boolean;
    created_at: string;
    entity: RegulatedEntity;
  }>;
  session: {
    id: number;
    acting_entity: RegulatedEntity | null;
    updated_at: string;
  };
}
