import { create } from 'zustand'
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  role: string
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  setTokens: (accessToken: string, refreshToken: string) => void
  setRole: (role: string) => void
  logout: () => void
}

const ACCESS_TOKEN_KEY = 'tt_access_token'
const REFRESH_TOKEN_KEY = 'tt_refresh_token'
const ROLE_KEY = 'tt_role'

export const useAuthStore = create<AuthState>((set, get) => ({
  accessToken: localStorage.getItem(ACCESS_TOKEN_KEY),
  refreshToken: localStorage.getItem(REFRESH_TOKEN_KEY),
  role: localStorage.getItem(ROLE_KEY) || 'worker',
  isAuthenticated: !!localStorage.getItem(ACCESS_TOKEN_KEY),

  login: async (email, password) => {
    const { data } = await axios.post(`${BASE_URL}/v1/auth/login`, { email, password })
    get().setTokens(data.access_token, data.refresh_token)
    try {
      const meRes = await axios.get(`${BASE_URL}/v1/auth/me`, {
        headers: { Authorization: `Bearer ${data.access_token}` },
      })
      get().setRole(meRes.data.role ?? 'worker')
    } catch {
      // fall back to 'worker' if endpoint not available
    }
  },

  setTokens: (accessToken, refreshToken) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
    set({ accessToken, refreshToken, isAuthenticated: true })
  },

  setRole: (role) => {
    localStorage.setItem(ROLE_KEY, role)
    set({ role })
  },

  logout: () => {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    localStorage.removeItem(ROLE_KEY)
    set({ accessToken: null, refreshToken: null, role: 'worker', isAuthenticated: false })
  },
}))
