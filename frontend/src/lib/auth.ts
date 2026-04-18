export type JwtClaims = {
  exp?: number
  preferred_username?: string
  realm_access?: { roles?: string[] }
  email?: string
  given_name?: string
  family_name?: string
  iss?: string
  sub?: string
}

export type AuthSession = {
  accessToken: string
  refreshToken: string
  expiresAt: number
}

const CLIENT_ID = 'ent-frontend'
const REALM_BASE = '/realms/ent-est/protocol/openid-connect'
const REDIRECT_PATH = '/login'
const CODE_VERIFIER_KEY = 'ent_pkce_code_verifier'
const PKCE_STATE_KEY = 'ent_pkce_state'
export const AUTH_SESSION_KEY = 'ent_auth_session'

function redirectUri(): string {
  return `${window.location.origin}${REDIRECT_PATH}`
}

function b64url(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer)
  let binary = ''
  bytes.forEach((b) => {
    binary += String.fromCharCode(b)
  })
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
}

function randomString(size = 64): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~'
  const bytes = new Uint8Array(size)
  crypto.getRandomValues(bytes)
  return Array.from(bytes)
    .map((b) => chars[b % chars.length])
    .join('')
}

async function buildCodeChallenge(verifier: string): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(verifier))
  return b64url(digest)
}

export function decodeJwtClaims(token: string): JwtClaims | null {
  try {
    const payload = token.split('.')[1]
    if (!payload) return null
    const json = atob(payload.replace(/-/g, '+').replace(/_/g, '/'))
    return JSON.parse(json) as JwtClaims
  } catch {
    return null
  }
}

function expiresAtFromToken(token: string): number {
  const claims = decodeJwtClaims(token)
  if (!claims?.exp) return Math.floor(Date.now() / 1000) + 60
  return claims.exp
}

export function roleBadgeVariant(role: string | undefined): 'default' | 'secondary' | 'outline' {
  if (role === 'admin') return 'default'
  if (role === 'teacher') return 'secondary'
  return 'outline'
}

export async function beginPkceLogin(): Promise<void> {
  const verifier = randomString(96)
  const state = randomString(40)
  const challenge = await buildCodeChallenge(verifier)
  sessionStorage.setItem(CODE_VERIFIER_KEY, verifier)
  sessionStorage.setItem(PKCE_STATE_KEY, state)

  const params = new URLSearchParams({
    client_id: CLIENT_ID,
    response_type: 'code',
    scope: 'openid profile email',
    redirect_uri: redirectUri(),
    code_challenge: challenge,
    code_challenge_method: 'S256',
    state,
  })
  window.location.href = `${REALM_BASE}/auth?${params.toString()}`
}

async function tokenRequest(payload: URLSearchParams): Promise<AuthSession> {
  const res = await fetch(`${REALM_BASE}/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: payload,
  })
  const data = (await res.json()) as {
    access_token?: string
    refresh_token?: string
    error_description?: string
  }
  if (!res.ok || !data.access_token || !data.refresh_token) {
    throw new Error(data.error_description || 'Authentication failed')
  }
  return {
    accessToken: data.access_token,
    refreshToken: data.refresh_token,
    expiresAt: expiresAtFromToken(data.access_token),
  }
}

export async function completePkceLogin(code: string, state: string): Promise<AuthSession> {
  const expectedState = sessionStorage.getItem(PKCE_STATE_KEY)
  const verifier = sessionStorage.getItem(CODE_VERIFIER_KEY)
  if (!expectedState || !verifier || expectedState !== state) {
    throw new Error('Invalid PKCE state')
  }

  const payload = new URLSearchParams({
    grant_type: 'authorization_code',
    client_id: CLIENT_ID,
    code,
    redirect_uri: redirectUri(),
    code_verifier: verifier,
  })
  const session = await tokenRequest(payload)
  sessionStorage.removeItem(PKCE_STATE_KEY)
  sessionStorage.removeItem(CODE_VERIFIER_KEY)
  return session
}

export async function refreshPkceSession(refreshToken: string): Promise<AuthSession> {
  const payload = new URLSearchParams({
    grant_type: 'refresh_token',
    client_id: CLIENT_ID,
    refresh_token: refreshToken,
  })
  return tokenRequest(payload)
}

/**
 * Direct Access Grant — username/password login via Keycloak token endpoint.
 * Suitable for dev / first-party login pages.
 */
export async function directAccessGrant(username: string, password: string): Promise<AuthSession> {
  const payload = new URLSearchParams({
    grant_type: 'password',
    client_id: CLIENT_ID,
    username,
    password,
    scope: 'openid profile email',
  })
  return tokenRequest(payload)
}

export function isSessionExpired(session: AuthSession): boolean {
  const now = Math.floor(Date.now() / 1000)
  return session.expiresAt <= now + 20
}
