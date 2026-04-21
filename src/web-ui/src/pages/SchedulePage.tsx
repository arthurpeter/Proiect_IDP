import { useState, useEffect } from 'react';
import { useAuth } from '../AuthContext';
import { apiGetTemplates, apiScheduleEmail, EmailTemplate, ApiError } from '../api';

const TEMPLATE_ICONS: Record<string, string> = {
  modern_professional: '💼',
  minimalist_clean: '✨',
  bold_alert: '🚨',
  elegant_soft: '💜',
};

export default function SchedulePage() {
  const { token, user } = useAuth();
  const [templates, setTemplates] = useState<Record<string, EmailTemplate>>({});
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [to, setTo] = useState('');
  const [subject, setSubject] = useState('');
  const [scheduledAt, setScheduledAt] = useState('');
  const [placeholders, setPlaceholders] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  useEffect(() => {
    if (!token) return;
    apiGetTemplates(token)
      .then(setTemplates)
      .catch(() => {});
  }, [token]);

  useEffect(() => {
    if (selectedTemplate && templates[selectedTemplate]) {
      const tmpl = templates[selectedTemplate];
      const defaults: Record<string, string> = {};
      tmpl.placeholders.forEach((p) => {
        if (p !== 'subject') defaults[p] = '';
      });
      setPlaceholders(defaults);
    }
  }, [selectedTemplate, templates]);

  const buildBody = (): string => {
    if (!selectedTemplate || !templates[selectedTemplate]) return '';
    let html = templates[selectedTemplate].html;
    html = html.replace('{{subject}}', subject);
    Object.entries(placeholders).forEach(([key, value]) => {
      html = html.replace(new RegExp(`\\{\\{${key}\\}\\}`, 'g'), value || `[${key}]`);
    });
    return html;
  };

  const showToast = (type: 'success' | 'error', message: string) => {
    setToast({ type, message });
    setTimeout(() => setToast(null), 3000);
  };

  const getMinDateTime = () => {
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    return now.toISOString().slice(0, 16);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!to || !subject || !scheduledAt) {
      showToast('error', 'Completează toate câmpurile obligatorii');
      return;
    }

    if (!selectedTemplate) {
      showToast('error', 'Selectează un template');
      return;
    }

    setLoading(true);
    try {
      const body = buildBody();
      const scheduledDate = new Date(scheduledAt).toISOString();

      await apiScheduleEmail(
        { to, subject, body, scheduled_at: scheduledDate, is_html: true },
        token!,
        user!.user_id
      );

      showToast('success', 'Email-ul a fost programat cu succes! 🎉');
      setTo('');
      setSubject('');
      setScheduledAt('');
      setPlaceholders({});
    } catch (err) {
      if (err instanceof ApiError) {
        showToast('error', err.message);
      } else {
        showToast('error', 'Eroare la programarea email-ului');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="page-header">
        <h2>📧 Programează Email</h2>
        <p>Alege un template, completează detaliile și programează trimiterea</p>
      </div>

      {toast && (
        <div className={`toast toast-${toast.type}`}>
          {toast.type === 'success' ? '✅' : '❌'} {toast.message}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {/* Step 1: Template Selection */}
        <div className="card" style={{ marginBottom: '24px' }}>
          <div className="card-header">
            <h3>1️⃣ Alege Template-ul</h3>
          </div>
          <div className="template-grid">
            {Object.entries(templates).map(([key, tmpl]) => (
              <div
                key={key}
                className={`template-card ${selectedTemplate === key ? 'selected' : ''}`}
                onClick={() => setSelectedTemplate(key)}
              >
                <div className="template-preview">
                  {TEMPLATE_ICONS[key] || '📄'}
                </div>
                <div className="template-name">{tmpl.style_name}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Step 2: Email Details */}
        <div className="card" style={{ marginBottom: '24px' }}>
          <div className="card-header">
            <h3>2️⃣ Detalii Email</h3>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label" htmlFor="schedule-to">Destinatar *</label>
              <input
                id="schedule-to"
                className="form-input"
                type="email"
                placeholder="destinatar@email.com"
                value={to}
                onChange={(e) => setTo(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="schedule-subject">Subiect *</label>
              <input
                id="schedule-subject"
                className="form-input"
                type="text"
                placeholder="Subiectul email-ului"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="schedule-date">Data și Ora Trimiterii *</label>
            <input
              id="schedule-date"
              className="form-input"
              type="datetime-local"
              value={scheduledAt}
              onChange={(e) => setScheduledAt(e.target.value)}
              min={getMinDateTime()}
              required
            />
          </div>
        </div>

        {/* Step 3: Template Placeholders */}
        {selectedTemplate && Object.keys(placeholders).length > 0 && (
          <div className="card" style={{ marginBottom: '24px' }}>
            <div className="card-header">
              <h3>3️⃣ Conținut Template</h3>
            </div>
            {Object.entries(placeholders).map(([key, value]) => (
              <div className="form-group" key={key}>
                <label className="form-label" htmlFor={`ph-${key}`}>
                  {key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                </label>
                {key.includes('text') || key.includes('content') || key.includes('message') ? (
                  <textarea
                    id={`ph-${key}`}
                    className="form-textarea"
                    placeholder={`Introdu ${key.replace(/_/g, ' ')}...`}
                    value={value}
                    onChange={(e) =>
                      setPlaceholders((prev) => ({ ...prev, [key]: e.target.value }))
                    }
                  />
                ) : (
                  <input
                    id={`ph-${key}`}
                    className="form-input"
                    type={key.includes('url') ? 'url' : 'text'}
                    placeholder={`Introdu ${key.replace(/_/g, ' ')}...`}
                    value={value}
                    onChange={(e) =>
                      setPlaceholders((prev) => ({ ...prev, [key]: e.target.value }))
                    }
                  />
                )}
              </div>
            ))}
          </div>
        )}

        {/* Submit */}
        <button
          type="submit"
          className="btn btn-primary btn-lg"
          disabled={loading}
          style={{ minWidth: '200px' }}
        >
          {loading ? (
            <><div className="spinner" /> Se programează...</>
          ) : (
            '🚀 Programează Trimiterea'
          )}
        </button>
      </form>
    </>
  );
}
