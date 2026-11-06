import React, { useEffect, useRef, useState } from 'react';

/**
 * Asks a new golfer for their real name when their sign-in only gave us an
 * email address. It cannot be dismissed: the name is what admins and other
 * golfers see. A golfer who already plays with the club can instead connect
 * their player history, which supplies their club name.
 */
const NameRequiredModal = ({ updateName, onFindPlayerHistory = null }) => {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const dialogRef = useRef(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (dialog.showModal) dialog.showModal();
    else dialog.setAttribute('open', '');
    return () => dialog.close?.();
  }, []);

  const handleSubmit = async (event) => {
    event.preventDefault();
    const first = firstName.trim();
    const last = lastName.trim();
    if (!first || !last) {
      setError('Enter your first and last name.');
      return;
    }
    if (first.includes('@') || last.includes('@')) {
      setError("Your name can't be an email address.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await updateName(first, last);
    } catch (err) {
      setError(err.message);
      setSaving(false);
    }
  };

  const fieldStyle = { display: 'block', width: '100%', padding: 8, marginTop: 4, boxSizing: 'border-box' };

  return (
    <dialog
      ref={dialogRef}
      onCancel={(event) => event.preventDefault()}
      aria-labelledby="name-required-title"
      style={{ border: 0, borderRadius: 16, padding: 24, width: 'min(420px, calc(100vw - 40px))' }}
    >
      <h2 id="name-required-title" style={{ marginTop: 0, color: '#2d5a27' }}>{"What's your name?"}</h2>
      <p style={{ color: '#555' }}>Your sign-in only shared your email address. Add your name so the club knows who you are.</p>
      {error && <div role="alert" style={{ background: '#ffebee', color: '#c62828', padding: 10, borderRadius: 8 }}>{error}</div>}
      <form onSubmit={handleSubmit}>
        <label style={{ display: 'block', marginTop: 12 }}>
          First name
          <input value={firstName} onChange={(e) => setFirstName(e.target.value)} autoComplete="given-name" maxLength={50} disabled={saving} style={fieldStyle} />
        </label>
        <label style={{ display: 'block', marginTop: 12 }}>
          Last name
          <input value={lastName} onChange={(e) => setLastName(e.target.value)} autoComplete="family-name" maxLength={50} disabled={saving} style={fieldStyle} />
        </label>
        <button type="submit" disabled={saving} style={{ marginTop: 16 }}>
          {saving ? 'Saving…' : 'Save my name'}
        </button>
      </form>
      {onFindPlayerHistory && (
        <p style={{ marginBottom: 0 }}>
          Already play with the club?{' '}
          <button type="button" onClick={onFindPlayerHistory} disabled={saving}>Find my player history</button>
        </p>
      )}
    </dialog>
  );
};

export default NameRequiredModal;
