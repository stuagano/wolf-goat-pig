import React, { useRef, useState } from 'react';
import Button from '../components/ui/Button';
import { apiConfig } from '../config/api.config';
import { useAccessToken } from '../hooks/useAccessToken';
import { fetchJson } from '../services/fetchJson';
import { useTheme } from '../theme/Provider';

const EMPTY_FORM = { type: 'bug', title: '', description: '', steps: '' };
const ISSUES_URL = 'https://github.com/stuagano/wolf-goat-pig/issues';

export default function FeedbackPage() {
  const theme = useTheme();
  const { getToken, reauthenticate, isRecoverableAuthError } = useAccessToken();
  const [form, setForm] = useState(EMPTY_FORM);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const [needsLogin, setNeedsLogin] = useState(false);
  const [issue, setIssue] = useState(null);
  const submitting = useRef(false);
  const update = (event) => setForm(current => ({ ...current, [event.target.name]: event.target.value }));
  const fieldStyle = {
    width: '100%', boxSizing: 'border-box', padding: '12px', borderRadius: '8px',
    border: `1px solid ${theme.colors.borderMedium}`, background: theme.colors.inputBackground,
    color: theme.colors.textPrimary, font: 'inherit', marginTop: '6px',
  };

  const submit = async (event) => {
    event.preventDefault();
    if (submitting.current || issue) return;
    setError('');
    setNeedsLogin(false);
    if (!form.title.trim() || !form.description.trim()) {
      setError('Enter a title and description.');
      return;
    }
    submitting.current = true;
    setPending(true);
    try {
      const token = await getToken();
      const result = await fetchJson(`${apiConfig.baseUrl}/feedback`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          type: form.type, title: form.title.trim(), description: form.description.trim(),
          steps: form.type === 'bug' ? form.steps.trim() : '',
        }),
      });
      setIssue(result);
    } catch (err) {
      const authError = isRecoverableAuthError(err) || err.status === 401 || err.status === 403;
      setNeedsLogin(authError);
      setError(authError ? 'Please sign in again to submit your feedback.'
        : err.status === 422 ? 'Check the length of your title and description, then try again.'
        : err.status ? err.message
        : 'Could not confirm delivery. Check the GitHub issues before submitting again.');
    } finally {
      submitting.current = false;
      setPending(false);
    }
  };

  return (
    <section aria-labelledby="feedback-heading" style={{ ...theme.cardStyle, maxWidth: 640, margin: '0 auto 100px', padding: '24px' }}>
      <h1 id="feedback-heading" style={{ marginTop: 0 }}>Send feedback</h1>
      <p>Found a bug or have an idea? Help make Wolf Goat Pig better.</p>
      <p style={{ color: theme.colors.textSecondary }}>
        Your feedback becomes a public GitHub issue. Don’t include passwords, email addresses, or private information.{' '}
        <a href={ISSUES_URL} target="_blank" rel="noopener noreferrer" style={{ color: theme.colors.primary }}>Browse existing issues</a>
      </p>
      {issue ? (
        <div role="status">
          <h2>Thanks for the feedback!</h2>
          <p><a href={issue.url} target="_blank" rel="noopener noreferrer" style={{ color: theme.colors.primary }}>View issue #{issue.number}</a></p>
          <Button style={{ outline: 'revert' }} onClick={() => { setForm(EMPTY_FORM); setIssue(null); }}>Send more feedback</Button>
        </div>
      ) : (
        <form onSubmit={submit} aria-busy={pending}>
          <fieldset disabled={pending} style={{ border: 0, margin: 0, padding: 0, minWidth: 0, display: 'grid', gap: '18px' }}>
            <label htmlFor="feedback-type">Feedback type
              <select id="feedback-type" name="type" value={form.type} onChange={update} style={fieldStyle}>
                <option value="bug">Bug report</option>
                <option value="feature">Feature request</option>
                <option value="general">General feedback</option>
              </select>
            </label>
            <label htmlFor="feedback-title">Title
              <input id="feedback-title" name="title" value={form.title} onChange={update} required maxLength={120}
                placeholder="A short summary" style={fieldStyle} />
            </label>
            <label htmlFor="feedback-description">Description
              <textarea id="feedback-description" name="description" value={form.description} onChange={update} required maxLength={5000}
                placeholder="What happened, or what would you like to see?" rows={6} style={{ ...fieldStyle, resize: 'vertical' }} />
            </label>
            {form.type === 'bug' && (
              <label htmlFor="feedback-steps">Steps to reproduce (optional)
                <textarea id="feedback-steps" name="steps" value={form.steps} onChange={update} maxLength={3000}
                  placeholder="What did you do, and what did you expect to happen?" rows={4} style={{ ...fieldStyle, resize: 'vertical' }} />
              </label>
            )}
            <Button type="submit" disabled={pending} fullWidth style={{ outline: 'revert' }}>{pending ? 'Submitting…' : 'Submit feedback'}</Button>
          </fieldset>
          {error && <p role="alert" style={{ color: theme.colors.error }}>{error}</p>}
          {needsLogin && <Button onClick={reauthenticate} style={{ outline: 'revert' }}>Sign in again</Button>}
        </form>
      )}
    </section>
  );
}
