import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import {
  AUTH_SESSION_KEY,
  beginPkceLogin,
  completePkceLogin,
  decodeJwtClaims,
  directAccessGrant,
  isSessionExpired,
  refreshPkceSession,
} from '@/lib/auth'

import type { AuthSession, JwtClaims } from '@/lib/auth'

type AuthContextValue = {
  session: AuthSession | null
  claims: JwtClaims | null
  username: string
  roles: string[]
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<void>
  beginLogin: () => Promise<void>
  handleLoginCallback: (code: string, state: string) => Promise<void>
  logout: () => void
  hasAnyRole: (allowed: string[]) => boolean
  apiFetch: <T>(path: string, init?: RequestInit) => Promise<T>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

type ApiError = { detail?: string }

function parseApiResponse<T>(res: Response, payload: unknown): T {
  if (!res.ok) {
    const detail =
      typeof payload === 'object' && payload !== null && 'detail' in payload
        ? String((payload as ApiError).detail ?? '')
        : ''
    throw new Error(detail || `Request failed (${res.status})`)
  }
  return payload as T
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<AuthSession | null>(() => {
    const raw = localStorage.getItem(AUTH_SESSION_KEY)
    if (!raw) return null
    try {
      const parsed = JSON.parse(raw) as AuthSession
      return parsed
    } catch {
      localStorage.removeItem(AUTH_SESSION_KEY)
      return null
    }
  })

  const claims = useMemo(() => (session ? decodeJwtClaims(session.accessToken) : null), [session])
  const roles = claims?.realm_access?.roles ?? []
  const username = claims?.preferred_username ?? 'guest'

  useEffect(() => {
    let active = true
    async function ensureSession() {
      if (!session) return
      if (!isSessionExpired(session)) return
      try {
        const refreshed = await refreshPkceSession(session.refreshToken)
        if (!active) return
        setSession(refreshed)
        localStorage.setItem(AUTH_SESSION_KEY, JSON.stringify(refreshed))
      } catch {
        if (!active) return
        setSession(null)
        localStorage.removeItem(AUTH_SESSION_KEY)
      }
    }
    void ensureSession()
    return () => {
      active = false
    }
  }, [session])

  async function login(username: string, password: string) {
    const next = await directAccessGrant(username, password)
    setSession(next)
    localStorage.setItem(AUTH_SESSION_KEY, JSON.stringify(next))
  }

  async function beginLogin() {
    await beginPkceLogin()
  }

  async function handleLoginCallback(code: string, state: string) {
    const next = await completePkceLogin(code, state)
    setSession(next)
    localStorage.setItem(AUTH_SESSION_KEY, JSON.stringify(next))
  }

  function logout() {
    setSession(null)
    localStorage.removeItem(AUTH_SESSION_KEY)
  }

  function hasAnyRole(allowed: string[]): boolean {
    if (!allowed.length) return true
    return roles.some((role) => allowed.includes(role))
  }

  async function ensureAccessToken(): Promise<string> {
    if (!session) throw new Error('Please login first.')
    if (!isSessionExpired(session)) return session.accessToken
    const refreshed = await refreshPkceSession(session.refreshToken)
    setSession(refreshed)
    localStorage.setItem(AUTH_SESSION_KEY, JSON.stringify(refreshed))
    return refreshed.accessToken
  }

  async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
    const token = await ensureAccessToken()
    const headers = new Headers(init?.headers)
    headers.set('Authorization', `Bearer ${token}`)
    const res = await fetch(path, { ...init, headers })
    const ct = res.headers.get('content-type') ?? ''
    const payload = ct.includes('application/json') ? await res.json() : {}
    return parseApiResponse<T>(res, payload)
  }

  const value: AuthContextValue = {
    session,
    claims,
    username,
    roles,
    isAuthenticated: Boolean(session),
    login,
    beginLogin,
    handleLoginCallback,
    logout,
    hasAnyRole,
    apiFetch,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
