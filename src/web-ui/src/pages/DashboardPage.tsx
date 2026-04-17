import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import { apiGetHistory, EmailLog } from '../api';

export default function DashboardPage() {
  const { token, user } = useAuth();
  const navigate = useNavigate();
  const [logs, setLogs] = useState<EmailLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token || !user) return;
    apiGetHistory(token, user.user_id)
      .then(setLogs)
      .catch(() => setLogs([]))
      .finally(() => setLoading(false));
  }, [token, user]);

  const totalEmails = logs.length;
  const sentEmails = logs.filter(l => l.status === 'sent').length;
  const pendingEmails = logs.filter(l => l.status === 'pending').length;
  const failedEmails = logs.filter(l => l.status === 'failed').length;

  const recentLogs = [...logs]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 5);

  return (
    <>
      <div className="page-header">
        <h2>Dashboard</h2>
        <p>Sumar al activității tale de notificări</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon purple">📊</div>
          <div>
            <div className="stat-value">{totalEmails}</div>
            <div className="stat-label">Total Email-uri</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon green">✅</div>
          <div>
            <div className="stat-value">{sentEmails}</div>
            <div className="stat-label">Trimise</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon yellow">⏳</div>
          <div>
            <div className="stat-value">{pendingEmails}</div>
            <div className="stat-label">În Așteptare</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon red">❌</div>
          <div>
            <div className="stat-value">{failedEmails}</div>
            <div className="stat-label">Eșuate</div>
          </div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <h3>⚡ Acțiuni Rapide</h3>
        </div>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <button className="btn btn-primary" onClick={() => navigate('/schedule')}>
            📧 Programează Email Nou
          </button>
          <button className="btn btn-secondary" onClick={() => navigate('/history')}>
            📋 Vezi Istoricul Complet
          </button>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>📬 Ultimele Email-uri</h3>
        </div>

        {loading ? (
          <div className="loading-page">
            <div className="spinner" style={{ borderColor: 'rgba(99,102,241,0.3)', borderTopColor: '#6366f1' }} />
            Se încarcă...
          </div>
        ) : recentLogs.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📭</div>
            <h3>Niciun email încă</h3>
            <p>Programează primul tău email pentru a începe</p>
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Destinatar</th>
                  <th>Subiect</th>
                  <th>Status</th>
                  <th>Data</th>
                </tr>
              </thead>
              <tbody>
                {recentLogs.map((log) => (
                  <tr key={log.id}>
                    <td style={{ color: 'var(--text-primary)' }}>{log.recipient}</td>
                    <td>{log.subject || '—'}</td>
                    <td>
                      <span className={`badge badge-${log.status}`}>
                        <span className="badge-dot" />
                        {log.status}
                      </span>
                    </td>
                    <td>{new Date(log.created_at).toLocaleString('ro-RO')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}
