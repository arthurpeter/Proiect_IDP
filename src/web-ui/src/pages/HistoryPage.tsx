import { useState, useEffect } from 'react';
import { useAuth } from '../AuthContext';
import { apiGetHistory, EmailLog } from '../api';

export default function HistoryPage() {
  const { token, user } = useAuth();
  const [logs, setLogs] = useState<EmailLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'sent' | 'pending' | 'failed'>('all');

  const fetchLogs = () => {
    if (!token || !user) return;
    setLoading(true);
    apiGetHistory(token, user.user_id)
      .then(setLogs)
      .catch(() => setLogs([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchLogs();
  }, [token, user]);

  const filteredLogs = filter === 'all'
    ? logs
    : logs.filter((l) => l.status === filter);

  const sortedLogs = [...filteredLogs].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  const sentCount = logs.filter(l => l.status === 'sent').length;
  const pendingCount = logs.filter(l => l.status === 'pending').length;
  const failedCount = logs.filter(l => l.status === 'failed').length;

  return (
    <>
      <div className="page-header">
        <h2>📋 Istoric Email-uri</h2>
        <p>Vizualizează toate email-urile programate și trimise</p>
      </div>

      {/* Filter Bar */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <button
              className={`btn btn-sm ${filter === 'all' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setFilter('all')}
            >
              Toate ({logs.length})
            </button>
            <button
              className={`btn btn-sm ${filter === 'sent' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setFilter('sent')}
            >
              ✅ Trimise ({sentCount})
            </button>
            <button
              className={`btn btn-sm ${filter === 'pending' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setFilter('pending')}
            >
              ⏳ În Așteptare ({pendingCount})
            </button>
            <button
              className={`btn btn-sm ${filter === 'failed' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setFilter('failed')}
            >
              ❌ Eșuate ({failedCount})
            </button>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={fetchLogs}>
            🔄 Reîncarcă
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="card">
        {loading ? (
          <div className="loading-page">
            <div className="spinner" style={{ borderColor: 'rgba(99,102,241,0.3)', borderTopColor: '#6366f1' }} />
            Se încarcă istoricul...
          </div>
        ) : sortedLogs.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📭</div>
            <h3>
              {filter === 'all'
                ? 'Niciun email în istoric'
                : `Niciun email cu status "${filter}"`}
            </h3>
            <p>
              {filter === 'all'
                ? 'Programează primul tău email pentru a vedea istoricul aici'
                : 'Încearcă un alt filtru'}
            </p>
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Destinatar</th>
                  <th>Subiect</th>
                  <th>Status</th>
                  <th>Creat La</th>
                  <th>Programat La</th>
                </tr>
              </thead>
              <tbody>
                {sortedLogs.map((log, idx) => (
                  <tr key={log.id}>
                    <td style={{ color: 'var(--text-muted)' }}>{idx + 1}</td>
                    <td style={{ color: 'var(--text-primary)', fontWeight: 500 }}>
                      {log.recipient}
                    </td>
                    <td>{log.subject || '—'}</td>
                    <td>
                      <span className={`badge badge-${log.status}`}>
                        <span className="badge-dot" />
                        {log.status}
                      </span>
                    </td>
                    <td>{new Date(log.created_at).toLocaleString('ro-RO')}</td>
                    <td>
                      {log.scheduled_at
                        ? new Date(log.scheduled_at).toLocaleString('ro-RO')
                        : '—'}
                    </td>
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
