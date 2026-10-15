const BASE = (import.meta.env.VITE_API_URL as string) || '/api'

export function role(): string {
  return localStorage.getItem('role') || 'admin'
}

export function setRole(r: string) {
  localStorage.setItem('role', r)
}

export async function api<T = any>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-Role': role(),
      'X-User': localStorage.getItem('user') || 'demo-user',
      ...(options.headers || {}),
    },
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`${res.status} ${res.statusText}: ${text.slice(0, 200)}`)
  }
  return res.json() as Promise<T>
}

export const fmt = (n: number | null | undefined, digits = 0) =>
  n === null || n === undefined || Number.isNaN(n)
    ? '—'
    : Number(n).toLocaleString('en-US', { maximumFractionDigits: digits })

export const pct = (n: number | null | undefined) =>
  n === null || n === undefined || Number.isNaN(n) ? '—' : `${(Number(n) * 100).toFixed(1)}%`
