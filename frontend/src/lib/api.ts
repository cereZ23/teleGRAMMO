import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from "axios";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

// Axios instance with auth header + refresh handling
const api: AxiosInstance = axios.create({ baseURL: BASE_URL });

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers = config.headers || {};
      (config.headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
    }
  }
  return config;
});

let isRefreshing = false;

api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const original = error.config as (AxiosRequestConfig & { _retry?: boolean }) | undefined;
    const status = error.response?.status;

    if (
      typeof window !== "undefined" &&
      status === 401 &&
      original &&
      !original._retry
    ) {
      original._retry = true;
      const refresh = localStorage.getItem("refresh_token");
      if (!refresh) {
        // No refresh token; clear and reject
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        return Promise.reject(error);
      }

      if (isRefreshing) {
        // Simple backoff if another request is refreshing
        await new Promise((r) => setTimeout(r, 300));
        return api(original);
      }

      try {
        isRefreshing = true;
        // Endpoint expects query param for refresh_token
        const resp = await axios.post(
          `${BASE_URL}/auth/refresh`,
          null,
          { params: { refresh_token: refresh } }
        );
        const { access_token, refresh_token } = resp.data as any;
        if (access_token) localStorage.setItem("access_token", access_token);
        if (refresh_token) localStorage.setItem("refresh_token", refresh_token);
        // Retry original request with new token
        original.headers = original.headers || {};
        (original.headers as Record<string, string>)["Authorization"] = `Bearer ${access_token}`;
        return api(original);
      } catch (e) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        return Promise.reject(error);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);

// ------------------ Auth ------------------
export const authApi = {
  async register(email: string, password: string) {
    const res = await api.post("/auth/register", { email, password });
    return res.data;
  },
  async login(email: string, password: string) {
    const res = await api.post("/auth/login", { email, password });
    return res.data as { access_token: string; refresh_token: string };
  },
  async me() {
    const res = await api.get("/auth/me");
    return res.data;
  },
};

// ---------------- Telegram Sessions ----------------
export const telegramApi = {
  async getSessions() {
    const res = await api.get("/telegram/sessions");
    const arr = (res.data || []) as any[];
    // Provide both array and arr.sessions for callers using either shape
    (arr as any).sessions = arr;
    return arr as any;
  },
  async createSession(apiId: number, apiHash: string, sessionName?: string) {
    const res = await api.post("/telegram/sessions", {
      api_id: apiId,
      api_hash: apiHash,
      session_name: sessionName,
    });
    return res.data;
  },
  async deleteSession(sessionId: string) {
    await api.delete(`/telegram/sessions/${sessionId}`);
  },
  async sendCode(sessionId: string, phoneNumber: string) {
    const res = await api.post(`/telegram/sessions/${sessionId}/send-code`, {
      phone_number: phoneNumber,
    });
    return res.data as { phone_code_hash?: string; timeout?: number };
  },
  async verifyCode(sessionId: string, code: string, phoneCodeHash?: string) {
    const res = await api.post(`/telegram/sessions/${sessionId}/verify-code`, {
      code,
      // API expects `phone_hash` which the service maps to `phone_code_hash`
      phone_hash: phoneCodeHash,
    });
    return res.data;
  },
  async verify2FA(sessionId: string, password: string) {
    const res = await api.post(`/telegram/sessions/${sessionId}/verify-2fa`, { password });
    return res.data;
  },
  async getDialogs(sessionId: string) {
    const res = await api.get(`/telegram/sessions/${sessionId}/dialogs`);
    return res.data as any[];
  },
};

// ---------------- Channels ----------------
export const channelsApi = {
  async getChannels() {
    const res = await api.get("/channels");
    return res.data;
  },
  async getAvailable(sessionId: string) {
    const res = await api.get("/channels/available", { params: { session_id: sessionId } });
    return res.data as any[];
  },
  async addChannel(sessionId: string, telegramId: number) {
    const res = await api.post("/channels", null, {
      params: { session_id: sessionId, telegram_id: telegramId },
    });
    return res.data;
  },
  async removeChannel(channelId: string) {
    await api.delete(`/channels/${channelId}`);
  },
  async getMessages(
    channelId: string,
    page = 1,
    limit = 50,
    opts?: {
      search?: string;
      mediaType?: string;
      dateFrom?: string;
      dateTo?: string;
      senderId?: number;
    }
  ) {
    const params: Record<string, any> = { page, limit };
    if (opts?.search) params.search = opts.search;
    if (opts?.mediaType) params.media_type = opts.mediaType;
    if (opts?.dateFrom) params.date_from = opts.dateFrom;
    if (opts?.dateTo) params.date_to = opts.dateTo;
    if (opts?.senderId) params.sender_id = opts.senderId;
    const res = await api.get(`/channels/${channelId}/messages`, { params });
    return res.data;
  },
  async getSchedule(channelId: string) {
    const res = await api.get(`/channels/${channelId}/schedule`);
    return res.data as { enabled: boolean; interval_hours?: number | null; last_scheduled_at?: string | null; next_scheduled_at?: string | null };
  },
  async updateSchedule(channelId: string, enabled: boolean, intervalHours?: number) {
    const res = await api.put(`/channels/${channelId}/schedule`, {
      enabled,
      interval_hours: intervalHours,
    });
    return res.data;
  },
};

// ---------------- Jobs ----------------
export const jobsApi = {
  async getJobs() {
    const res = await api.get("/jobs");
    return res.data;
  },
  async startScrape(channelId: string, jobType: string = "incremental", scrapeMedia = true) {
    const res = await api.post("/jobs/scrape", {
      channel_id: channelId,
      job_type: jobType,
      scrape_media: scrapeMedia,
    });
    return res.data;
  },
  async cancelJob(jobId: string) {
    const res = await api.post(`/jobs/${jobId}/cancel`);
    return res.data;
  },
};

// ---------------- Analytics ----------------
export const analyticsApi = {
  async getOverview() {
    const res = await api.get("/analytics/overview");
    return res.data;
  },
  async getMessagesOverTime(channelId?: string, days: number = 30) {
    const params: Record<string, any> = { days };
    if (channelId) params.channel_id = channelId;
    const res = await api.get("/analytics/messages-over-time", { params });
    return res.data;
  },
  async getTopSenders(channelId?: string, limit: number = 10) {
    const params: Record<string, any> = { limit };
    if (channelId) params.channel_id = channelId;
    const res = await api.get("/analytics/top-senders", { params });
    return res.data;
  },
  async getMediaBreakdown(channelId?: string) {
    const params: Record<string, any> = {};
    if (channelId) params.channel_id = channelId;
    const res = await api.get("/analytics/media-breakdown", { params });
    return res.data;
  },
  async getActivityHeatmap(channelId?: string, days: number = 90) {
    const params: Record<string, any> = { days };
    if (channelId) params.channel_id = channelId;
    const res = await api.get("/analytics/activity-heatmap", { params });
    return res.data;
  },
  async getChannelStats() {
    const res = await api.get("/analytics/channel-stats");
    return res.data;
  },
};

// ---------------- Export ----------------
export const exportApi = {
  async downloadCSV(channelId: string) {
    const res = await api.get(`/export/channels/${channelId}/csv`, { responseType: "blob" });
    return res;
  },
  async downloadJSON(channelId: string) {
    const res = await api.get(`/export/channels/${channelId}/json`, { responseType: "blob" });
    return res;
  },
};

// ---------------- Media ----------------
export const mediaApi = {
  async getMediaStats(channelId: string) {
    const res = await api.get(`/media/channel/${channelId}/stats`);
    return res.data;
  },
  async startBatchDownload(channelId: string, sessionId: string, limit = 10) {
    const res = await api.post(`/media/batch-download`, {
      channel_id: channelId,
      session_id: sessionId,
      limit,
    });
    return res.data;
  },
};

export default api;

