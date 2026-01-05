// Pattern types
export interface Pattern {
  id: number;
  name: string;
  description: string | null;
  image_path: string;
  pattern_type: string;
  claude_analysis: ClaudeAnalysis | null;
  confidence_threshold: number;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface ClaudeAnalysis {
  pattern_identified: string;
  key_characteristics: string[];
  entry_conditions: string[];
  exit_conditions: string[];
  risk_level: string;
  typical_duration: string;
  success_indicators: string[];
  failure_indicators: string[];
  additional_notes?: string;
}

// Watchlist types
export interface WatchlistItem {
  id: number;
  symbol: string;
  timeframes: string[];
  is_active: boolean;
  created_at: string;
}

// Scanner types
export interface ScanResult {
  id: number;
  pattern_id: number;
  pattern_name?: string;
  symbol: string;
  timeframe: string;
  confidence_score: number | null;
  is_match: boolean;
  chart_image_path: string | null;
  claude_response: ComparisonResponse | null;
  created_at: string;
}

export interface ComparisonResponse {
  is_match: boolean;
  confidence_score: number;
  reasoning: string;
  pattern_stage: string;
  key_similarities: string[];
  key_differences: string[];
  action_suggestion: string;
}

export interface ScannerStatus {
  is_running: boolean;
  last_scan_at: string | null;
  next_scan_at: string | null;
  scan_interval_minutes: number;
  patterns_active: number;
  symbols_monitored: number;
  total_scans_today: number;
  matches_today: number;
}

// Alert types
export interface Alert {
  id: number;
  scan_result_id: number;
  channel: string;
  status: string;
  sent_at: string | null;
  error_message: string | null;
  created_at: string;
  symbol?: string;
  pattern_name?: string;
  confidence_score?: number;
}

export interface AlertSettings {
  telegram_enabled: boolean;
  telegram_chat_id: string | null;
  email_enabled: boolean;
  email_address: string | null;
  dashboard_enabled: boolean;
  min_confidence_threshold: number;
}

// Auth types
export interface User {
  id: number;
  email: string;
  is_active: boolean;
  created_at: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
}

// API response types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
}

// Binance types
export interface Symbol {
  symbol: string;
  base_asset: string;
  quote_asset: string;
  status: string;
}

export interface Kline {
  open_time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  close_time: number;
}
