import { useState, FormEvent } from 'react'
import { login } from '../services/api'
import './Login.css'

interface LoginProps {
  onLogin: (user: { id: number; username: string; email: string; role: string }) => void
}

function Login({ onLogin }: LoginProps) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    console.log('[Login] Attempting login for user:', username)

    try {
      const response = await login({ username, password })
      console.log('[Login] Login successful')

      // Store session_id for WebSocket authentication
      if (response.session_id) {
        sessionStorage.setItem('session_id', response.session_id)
        console.log('[Login] Session ID stored')
      }

      onLogin(response.user)
    } catch (err: unknown) {
      console.error('[Login] Login failed:', err)
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosError = err as { response?: { data?: { error?: string } } }
        setError(axiosError.response?.data?.error || 'Login failed. Please try again.')
      } else {
        setError('Login failed. Please check your connection.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <img src="/waddleperf-penguin.svg" alt="WaddlePerf Logo" className="login-logo" />
          <h1>WaddlePerf</h1>
          <p>Network Performance Testing</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter your username"
              required
              autoComplete="username"
              autoFocus
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
              autoComplete="current-password"
            />
          </div>

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? (
              <>
                <span className="spinner-small"></span>
                Logging in...
              </>
            ) : (
              'Login'
            )}
          </button>
        </form>

        <div className="login-footer">
          <p>Web Client v1.0.0</p>
        </div>
      </div>
    </div>
  )
}

export default Login
