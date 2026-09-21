const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

function readableError(data: any, status: number): string {
  const detail = data?.detail
  if (Array.isArray(detail)) {
    return detail.map((issue: any) => {
      const field = issue.loc?.filter((part: unknown) => part !== 'body').join(' → ') || 'Input'
      const label = field.charAt(0).toUpperCase() + field.slice(1).replaceAll('_', ' ')
      if (issue.type === 'missing') return `${label} is required.`
      if (issue.type === 'string_too_short') return `${label} must be at least ${issue.ctx?.min_length || 1} characters.`
      if (issue.type === 'string_too_long') return `${label} must not exceed ${issue.ctx?.max_length} characters.`
      if (issue.type === 'value_error' && field === 'email') return 'Enter a valid email address.'
      if (issue.type === 'greater_than') return `${label} must be greater than ${issue.ctx?.gt}.`
      if (issue.type === 'greater_than_equal') return `${label} must be at least ${issue.ctx?.ge}.`
      return `${label}: ${String(issue.msg || 'Invalid value').replace(/^Value error,\s*/i, '')}`
    }).join(' ')
  }
  if (typeof detail === 'string') return detail
  if (status === 401) return 'Your session has expired. Please sign in again.'
  if (status === 403) return 'You do not have permission to perform this action.'
  if (status === 404) return 'The requested record was not found.'
  if (status >= 500) return 'The server encountered an error. Please try again.'
  return 'The request could not be completed.'
}

function announceError(message: string) {
  window.dispatchEvent(new CustomEvent('quiz-api-error', {detail: message}))
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('token')
  let response: Response
  try {
    response = await fetch(`${BASE}${path}`, {
      ...options,
      headers: {'Content-Type': 'application/json', ...(token ? {Authorization: `Bearer ${token}`} : {}), ...options.headers}
    })
  } catch {
    const message = 'Cannot connect to the server. Please confirm that the backend and MySQL are running.'
    announceError(message)
    throw new Error(message)
  }
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    const message = readableError(data, response.status)
    announceError(message)
    throw new Error(message)
  }
  return data
}
