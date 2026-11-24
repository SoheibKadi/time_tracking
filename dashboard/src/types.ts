export type UserRole = 'worker' | 'admin'
export type ContractStatus = 'active' | 'paused' | 'closed'
export type WindowStatus = 'submitted' | 'deleted' | 'disputed' | 'accepted_dispute' | 'rejected_dispute'
export type InvoiceStatus = 'draft' | 'sent' | 'paid'

export interface ClientProfile {
  id: string
  name: string
  company_name?: string
  billing_email?: string
  billing_address?: string
}

export interface Contract {
  id: string
  title: string
  hourly_rate: number
  weekly_hour_limit?: number
  screenshot_interval_min: number
  status: ContractStatus
  share_token: string
  created_at: string
  client_profile?: ClientProfile
}

export interface WorkSession {
  id: string
  contract_id: string
  started_at: string
  ended_at?: string
  memo?: string
}

export interface TimeWindow {
  id: string
  session_id: string
  started_at: string
  ended_at: string
  activity_level?: number
  is_manual: boolean
  manual_reason?: string
  status: WindowStatus
  disputed_at?: string
  dispute_reason?: string
  resolved_at?: string
}

export interface Screenshot {
  id: string
  window_id: string
  captured_at: string
  sha256: string
  deleted_at?: string
}

export interface InvoiceLineItem {
  id: string
  description: string
  hours: number
  rate: number
  amount: number
}

export interface Invoice {
  id: string
  contract_id: string
  invoice_number: string
  period_start: string
  period_end: string
  total_hours: number
  hourly_rate: number
  subtotal: number
  tax_rate: number
  tax_amount: number
  total: number
  status: InvoiceStatus
  issued_at: string
  due_at?: string
  paid_at?: string
  notes?: string
  line_items: InvoiceLineItem[]
}

export interface ShareWindow {
  id: string
  started_at: string
  ended_at: string
  duration_minutes: number
  activity_level?: number
  is_manual: boolean
  manual_reason?: string
  status: WindowStatus
  disputed_at?: string
  dispute_reason?: string
  resolved_at?: string
  has_screenshot: boolean
  screenshot_id?: string
  thumbnail_url?: string
}

export interface ShareView {
  contract_title: string
  hourly_rate: number
  billable_hours: number
  refreshed_at: string
  windows: ShareWindow[]
}

export interface FreelancerProfile {
  id?: string
  company_name?: string
  address?: string
  tax_id?: string
  tax_label?: string
  invoice_prefix?: string
  payment_instructions?: string
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface AuditLog {
  id: string; user_id?: string; share_token?: string; action: string
  details?: string; ip_address?: string; created_at: string
}

export interface BlocklistItem {
  id: string; pattern: string; created_at: string
}

export interface AdminUser {
  id: string; email: string; name: string; role: string
  is_active: boolean; created_at: string
}
