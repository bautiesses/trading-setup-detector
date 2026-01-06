const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

class ApiClient {
  private token: string | null = null;

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
      response = await fetch(`${API_BASE_URL}${endpoint}`, {
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

    const response = await fetch(`${API_BASE_URL}/auth/login`, {
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
    return this.request(`/watchlist/?active_only=${activeOnly}`);
  }

  async addToWatchlist(symbol: string, timeframes: string[]) {
    return this.request('/watchlist/', {
      method: 'POST',
      body: JSON.stringify({ symbol, timeframes }),
    });
  }

  async updateWatchlistItem(id: number, data: Record<string, unknown>) {
    return this.request(`/watchlist/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async removeFromWatchlist(id: number) {
    return this.request(`/watchlist/${id}`, { method: 'DELETE' });
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
    return this.request('/binance/symbols');
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
    let url = `/trades/?skip=${skip}&limit=${limit}`;
    if (status) {
      url += `&status=${status}`;
    }
    return this.request(url);
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
    return this.request('/trades/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateTrade(id: number, data: Record<string, unknown>) {
    return this.request(`/trades/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async closeTrade(id: number, data: { exit_price: number; fees?: number; exit_notes?: string; exit_image_url?: string }) {
    return this.request(`/trades/${id}/close`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async deleteTrade(id: number) {
    return this.request(`/trades/${id}`, { method: 'DELETE' });
  }

  async getTradeStats() {
    return this.request('/trades/stats');
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
