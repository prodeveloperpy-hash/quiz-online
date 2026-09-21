const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('token')
  const response = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {'Content-Type': 'application/json', ...(token ? {Authorization: `Bearer ${token}`} : {}), ...options.headers}
  })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(data.detail || 'Something went wrong')
  return data
}

