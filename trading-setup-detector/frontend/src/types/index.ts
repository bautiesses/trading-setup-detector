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

// Solana types
export interface SolanaWallet {
  id: number;
  address: string;
  label: string | null;
  is_active: boolean;
  helius_webhook_id: string | null;
  created_at: string;
}

export interface SolanaTrade {
  id: number;
  wallet_id: number;
  tx_signature: string;
  block_time: string;
  side: 'buy' | 'sell';

  token_in_address: string;
  token_in_symbol: string | null;
  token_in_name: string | null;
  token_in_amount: number;
  token_in_usd_value: number | null;

  token_out_address: string;
  token_out_symbol: string | null;
  token_out_name: string | null;
  token_out_amount: number;
  token_out_usd_value: number | null;

  price_per_token: number | null;
  price_usd: number | null;

  fee_sol: number | null;
  fee_usd: number | null;

  linked_trade_id: number | null;
  pnl: number | null;
  pnl_percent: number | null;

  chart_image_url: string | null;
  notes: string | null;
  dex_name: string;

  created_at: string;
}

export interface SolanaTradeStats {
  total_trades: number;
  buy_trades: number;
  sell_trades: number;
  total_volume_usd: number;
  total_fees_sol: number;
  linked_pnl: number;
  winning_trades: number;
  losing_trades: number;
}
