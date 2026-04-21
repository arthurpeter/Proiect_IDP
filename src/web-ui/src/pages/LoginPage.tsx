import { useState } from 'react';
import { useAuth } from '../AuthContext';
import { apiLogin, apiRegister, ApiError } from '../api';

export default function LoginPage() {
  const { login } = useAuth();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!email || !password) {
      setError('Completează toate câmpurile');
      return;
    }

    if (mode === 'register' && password !== confirmPassword) {
      setError('Parolele nu coincid');
      return;
    }

    if (password.length < 6) {
      setError('Parola trebuie să aibă cel puțin 6 caractere');
      return;
    }

    setLoading(true);
    try {
      const response = mode === 'login'
        ? await apiLogin(email, password)
        : await apiRegister(email, password);

      login(response.access_token, {
        user_id: response.user_id,
        email: response.email,
      });
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Eroare de conexiune. Verifică serverul.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-header">
          <span className="logo-icon">✉</span>
          <h1>Remailder</h1>
          <p>Notification-as-a-Service</p>
        </div>

        <div className="auth-toggle">
          <button
            className={mode === 'login' ? 'active' : ''}
            onClick={() => { setMode('login'); setError(''); }}
          >
            Autentificare
          </button>
          <button
            className={mode === 'register' ? 'active' : ''}
            onClick={() => { setMode('register'); setError(''); }}
          >
            Înregistrare
          </button>
        </div>

        {error && (
          <div className="auth-error">
            <span>⚠️</span> {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="auth-email">Adresă Email</label>
            <input
              id="auth-email"
              className="form-input"
              type="email"
              placeholder="exemplu@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="auth-password">Parolă</label>
            <input
              id="auth-password"
              className="form-input"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
            />
          </div>

          {mode === 'register' && (
            <div className="form-group">
              <label className="form-label" htmlFor="auth-confirm">Confirmă Parola</label>
              <input
                id="auth-confirm"
                className="form-input"
                type="password"
                placeholder="••••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                autoComplete="new-password"
              />
            </div>
          )}

          <button
            type="submit"
            className="btn btn-primary btn-block btn-lg"
            disabled={loading}
          >
            {loading ? (
              <><div className="spinner" /> Se procesează...</>
            ) : (
              mode === 'login' ? 'Autentificare' : 'Creează Cont'
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
