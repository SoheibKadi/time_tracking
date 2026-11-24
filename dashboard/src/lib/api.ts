import axios from 'axios'
import { useAuthStore } from '@/stores/authStore'
import type { AdminUser, AuditLog, BlocklistItem } from '@/types'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: BASE_URL,
})

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

let isRefreshing = false
let failedQueue: Array<{ resolve: (value: string) => void; reject: (reason: unknown) => void }> = []

function processQueue(error: unknown, token: string | null = null) {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) reject(error)
    else resolve(token!)
  })
  failedQueue = []
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return api(originalRequest)
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      const refreshToken = useAuthStore.getState().refreshToken
      if (!refreshToken) {
        useAuthStore.getState().logout()
        window.location.href = '/login'
        return Promise.reject(error)
      }

      try {
        const response = await axios.post(`${BASE_URL}/v1/auth/refresh`, {
          refresh_token: refreshToken,
        })
        const { access_token, refresh_token } = response.data
        useAuthStore.getState().setTokens(access_token, refresh_token)
        processQueue(null, access_token)
        originalRequest.headers.Authorization = `Bearer ${access_token}`
        return api(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError, null)
        useAuthStore.getState().logout()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

export const publicApi = axios.create({
  baseURL: BASE_URL,
})

export const getMe = () =>
  api.get<{ id: string; email: string; name: string; role: string; is_active: boolean }>('/v1/auth/me')

export const adminApi = {
  listUsers: () => api.get<AdminUser[]>('/v1/admin/users'),
  updateUser: (id: string, body: { is_active?: boolean }) => api.patch(`/v1/admin/users/${id}`, body),
  inviteUser: (body: { email: string; name: string; role?: string }) =>
    api.post<{ temp_password: string }>('/v1/admin/users/invite', body),
  getAuditLog: () => api.get<AuditLog[]>('/v1/admin/audit'),
}

export const registerUser = (body: { email: string; name: string; password: string }) =>
  publicApi.post('/v1/auth/register', body)

export const exportContractCSV = (contractId: string, fromDate: string, toDate: string) =>
  api.get(`/v1/contracts/${contractId}/export`, {
    params: { from_date: fromDate, to_date: toDate },
    responseType: 'blob',
  })

export const deleteScreenshot = (screenshotId: string) =>
  api.delete(`/v1/screenshots/${screenshotId}`)

export const blocklistApi = {
  list: () => api.get<BlocklistItem[]>('/v1/blocklist'),
  add: (pattern: string) => api.post<BlocklistItem>('/v1/blocklist', { pattern }),
  remove: (id: string) => api.delete(`/v1/blocklist/${id}`),
}
