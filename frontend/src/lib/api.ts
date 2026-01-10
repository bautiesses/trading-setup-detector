// Simple cache for API responses
interface CacheEntry<T> {
  data: T;
  timestamp: number;
}

const cache: Map<string, CacheEntry<unknown>> = new Map();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes default
const SYMBOLS_CACHE_TTL = 30 * 60 * 1000; // 30 minutes for symbols

class ApiClient {
  private token: string | null = null;

  private getCache<T>(key: string, ttl: number = CACHE_TTL): T | null {
    const entry = cache.get(key);
    if (entry && Date.now() - entry.timestamp < ttl) {
      return entry.data as T;
    }
    cache.delete(key);
    return null;
  }

  private setCache<T>(key: string, data: T): void {
    cache.set(key, { data, timestamp: Date.now() });
  }

  private getApiBaseUrl(): string {
    // Use environment variable if available (production)
    if (process.env.NEXT_PUBLIC_API_URL) {
      return process.env.NEXT_PUBLIC_API_URL;
    }

    // Check if running on localhost (development)
    if (typeof window !== 'undefined') {
      const hostname = window.location.hostname;
      if (hostname === 'localhost' || hostname === '127.0.0.1') {
        return 'http://localhost:8000/api/v1';
      }
    }

    // Fallback to hardcoded production URL
    return 'https://trading-scanner-production-310a.up.railway.app/api/v1';
  }

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('token');
    }
  }

  getToken(): string | null {
    if (this.token) return this.token;
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('token');
    }
    return this.token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = this.getToken();
    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string> || {}),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
    }

    let response: Response;
    try {
      response = await fetch(`${this.getApiBaseUrl()}${endpoint}`, {
        ...options,
        headers,
      });
    } catch (error) {
      console.error('Network error:', error);
      throw new Error('Error de conexión. Verificá que el backend esté corriendo en localhost:8000');
    }

    if (response.status === 401) {
      this.setToken(null);
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
      throw new Error('Unauthorized');
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Request failed');
    }

    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  }

  // Auth
  async login(username: string, password: string) {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await fetch(`${this.getApiBaseUrl()}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Login failed');
    }

    const data = await response.json();
    this.setToken(data.access_token);
    return data;
  }

  async register(email: string, password: string) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async getCurrentUser() {
    return this.request('/auth/me');
  }

  logout() {
    this.setToken(null);
  }

  // Watchlist
  async getWatchlist(activeOnly = false) {
    const cacheKey = `watchlist_${activeOnly}`;
    const cached = this.getCache(cacheKey, 60 * 1000); // 1 minute cache
    if (cached) return cached;

    const data = await this.request(`/watchlist/?active_only=${activeOnly}`);
    this.setCache(cacheKey, data);
    return data;
  }

  clearWatchlistCache() {
    cache.delete('watchlist_false');
    cache.delete('watchlist_true');
  }

  async addToWatchlist(symbol: string, timeframes: string[]) {
    const result = await this.request('/watchlist/', {
      method: 'POST',
      body: JSON.stringify({ symbol, timeframes }),
    });
    this.clearWatchlistCache();
    return result;
  }

  async updateWatchlistItem(id: number, data: Record<string, unknown>) {
    const result = await this.request(`/watchlist/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
    this.clearWatchlistCache();
    return result;
  }

  async removeFromWatchlist(id: number) {
    const result = await this.request(`/watchlist/${id}`, { method: 'DELETE' });
    this.clearWatchlistCache();
    return result;
  }

  // Scanner - Break & Retest
  async getScannerStatus() {
    return this.request('/scanner/status');
  }

  async runManualScan(sensitivity: string = 'medium', symbols?: string[], timeframes?: string[]) {
    return this.request('/scanner/scan', {
      method: 'POST',
      body: JSON.stringify({ sensitivity, symbols, timeframes }),
    });
  }

  async getScanResults(patternType?: string, skip = 0, limit = 50) {
    let url = `/scanner/results?skip=${skip}&limit=${limit}`;
    if (patternType) {
      url += `&pattern_type=${patternType}`;
    }
    return this.request(url);
  }

  async clearScanResults(days: number = 0) {
    // days=0 means clear ALL results
    return this.request(`/scanner/results?days=${days}`, { method: 'DELETE' });
  }

  async clearDuplicateSignals() {
    return this.request('/scanner/duplicates', { method: 'DELETE' });
  }

  // Binance
  async getSymbols() {
    const cacheKey = 'binance_symbols';
    const cached = this.getCache(cacheKey, SYMBOLS_CACHE_TTL);
    if (cached) return cached;

    const data = await this.request('/binance/symbols');
    this.setCache(cacheKey, data);
    return data;
  }

  async getKlines(symbol: string, interval: string, limit = 200) {
    return this.request(`/binance/klines/${symbol}?interval=${interval}&limit=${limit}`);
  }

  // Auto Scanner
  async startAutoScanner(intervalMinutes: number = 5) {
    return this.request('/scanner/auto/start', {
      method: 'POST',
      body: JSON.stringify({ interval_minutes: intervalMinutes }),
    });
  }

  async stopAutoScanner() {
    return this.request('/scanner/auto/stop', { method: 'POST' });
  }

  async getAutoScannerStatus() {
    return this.request('/scanner/auto/status');
  }

  async getNewSignals() {
    return this.request('/scanner/auto/new-signals');
  }

  // Trades
  async getTrades(status?: string, skip = 0, limit = 50) {
    const cacheKey = `trades_${status || 'all'}_${skip}_${limit}`;
    const cached = this.getCache(cacheKey, 30 * 1000); // 30 sec cache
    if (cached) return cached;

    let url = `/trades/?skip=${skip}&limit=${limit}`;
    if (status) {
      url += `&status=${status}`;
    }
    const data = await this.request(url);
    this.setCache(cacheKey, data);
    return data;
  }

  clearTradesCache() {
    // Clear all trades cache entries
    for (const key of cache.keys()) {
      if (key.startsWith('trades_') || key === 'trade_stats') {
        cache.delete(key);
      }
    }
  }

  async createTrade(data: {
    symbol: string;
    side: string;
    entry_price: number;
    size: number;
    stop_loss?: number;
    take_profit?: number;
    notes?: string;
    image_url?: string;
    timeframe?: string;
    strategy?: string;
  }) {
    const result = await this.request('/trades/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    this.clearTradesCache();
    return result;
  }

  async updateTrade(id: number, data: Record<string, unknown>) {
    const result = await this.request(`/trades/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
    this.clearTradesCache();
    return result;
  }

  async closeTrade(id: number, data: { exit_price: number; fees?: number; exit_notes?: string; exit_image_url?: string }) {
    const result = await this.request(`/trades/${id}/close`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
    this.clearTradesCache();
    return result;
  }

  async addTradeReview(id: number, data: { review_notes?: string; review_image_url?: string }) {
    const result = await this.request(`/trades/${id}/review`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
    this.clearTradesCache();
    return result;
  }

  async deleteTrade(id: number) {
    const result = await this.request(`/trades/${id}`, { method: 'DELETE' });
    this.clearTradesCache();
    return result;
  }

  async getTradeStats() {
    const cacheKey = 'trade_stats';
    const cached = this.getCache(cacheKey, 30 * 1000); // 30 sec cache
    if (cached) return cached;

    const data = await this.request('/trades/stats');
    this.setCache(cacheKey, data);
    return data;
  }

  async analyzeMonth(month: number, year: number) {
    return this.request('/trades/analyze-month', {
      method: 'POST',
      body: JSON.stringify({ month, year }),
    });
  }

  // ========== SOLANA ==========

  // Wallets
  async getSolanaWallets() {
    return this.request('/solana/wallets');
  }

  async addSolanaWallet(address: string, label?: string) {
    return this.request('/solana/wallets', {
      method: 'POST',
      body: JSON.stringify({ address, label }),
    });
  }

  async removeSolanaWallet(walletId: number) {
    return this.request(`/solana/wallets/${walletId}`, { method: 'DELETE' });
  }

  // Trades
  async getSolanaTrades(params?: {
    wallet_id?: number;
    side?: string;
    skip?: number;
    limit?: number;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.wallet_id) queryParams.set('wallet_id', params.wallet_id.toString());
    if (params?.side) queryParams.set('side', params.side);
    if (params?.skip) queryParams.set('skip', params.skip.toString());
    if (params?.limit) queryParams.set('limit', params.limit.toString());

    const queryString = queryParams.toString();
    return this.request(`/solana/trades${queryString ? `?${queryString}` : ''}`);
  }

  async getSolanaTrade(tradeId: number) {
    return this.request(`/solana/trades/${tradeId}`);
  }

  async getSolanaStats() {
    return this.request('/solana/trades/stats');
  }

  async linkSolanaTrades(entryTradeId: number, exitTradeId: number) {
    return this.request(`/solana/trades/${entryTradeId}/link/${exitTradeId}`, {
      method: 'POST',
    });
  }

  async updateSolanaTradeNotes(tradeId: number, notes: string) {
    return this.request(`/solana/trades/${tradeId}/notes`, {
      method: 'PUT',
      body: JSON.stringify({ notes }),
    });
  }

  async importSolanaTransaction(txSignature: string) {
    return this.request(`/solana/import/${txSignature}`, {
      method: 'POST',
    });
  }
}

export const api = new ApiClient();
