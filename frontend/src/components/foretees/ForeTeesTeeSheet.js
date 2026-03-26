import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../../theme/Provider';
import useTeeTimes from '../../hooks/useTeeTimes';
import BookingModal from './BookingModal';

const formatDate = (d) => d.toISOString().split('T')[0];

const ForeTeesTeeSheet = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const {
    teeTimes, bookings, loading, error,
    fetchTeeTimes, fetchBookings,
    bookTeeTime, cancelTeeTime, bookingLoading, clearBookingError,
  } = useTeeTimes();
  const [selectedDate, setSelectedDate] = useState(formatDate(new Date()));
  const [bookingSlot, setBookingSlot] = useState(null);
  const [bookingResult, setBookingResult] = useState(null);
  const [cancellingTtdata, setCancellingTtdata] = useState(null);

  useEffect(() => {
    fetchTeeTimes(selectedDate);
  }, [selectedDate, fetchTeeTimes]);

  useEffect(() => {
    fetchBookings();
    // Pre-wake the booking service so it's ready when user clicks Book
    fetch('https://wolf-goat-pig-booking.onrender.com/health', { mode: 'no-cors' }).catch(() => {});
  }, [fetchBookings]);

  useEffect(() => {
    if (bookingResult) {
      const timer = setTimeout(() => setBookingResult(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [bookingResult]);

  const handleDateChange = (offset) => {
    const d = new Date(selectedDate + 'T12:00:00');
    d.setDate(d.getDate() + offset);
    setSelectedDate(formatDate(d));
  };

  const handleBookConfirm = async ({ transportMode }) => {
    const result = await bookTeeTime(bookingSlot.ttdata, transportMode, bookingSlot.date, bookingSlot.time);

    if (!result) {
      setBookingResult({
        type: 'error',
        message: 'Booking request failed — the service may be starting up. Wait 30 seconds and try again.',
      });
      setBookingSlot(null);
      return;
    }

    const success = result?.data?.success || result?.success;
    if (success) {
      const msg = result?.data?.messages?.[0] || result?.message || 'Tee time booked!';
      setBookingResult({ type: 'success', message: msg });
      setBookingSlot(null);
      fetchTeeTimes(selectedDate);
      fetchBookings();
    } else {
      const msg = result?.detail
        || result?.data?.messages?.join('. ')
        || result?.data?.message
        || result?.data?.error
        || result?.message
        || result?.error
        || 'Booking failed. Please try again.';
      setBookingResult({ type: 'error', message: msg });
      setBookingSlot(null);
    }
  };

  const displayDate = new Date(selectedDate + 'T12:00:00').toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      {/* Booking Result Toast */}
      {bookingResult && (
        <div
          style={{
            padding: 16,
            marginBottom: 16,
            background: bookingResult.type === 'success' ? '#ecfdf5' : '#fef2f2',
            color: bookingResult.type === 'success' ? '#166534' : '#991b1b',
            borderLeft: `4px solid ${bookingResult.type === 'success' ? '#10b981' : '#ef4444'}`,
            borderRadius: 8,
            cursor: 'pointer',
          }}
          onClick={() => setBookingResult(null)}
        >
          {bookingResult.message}
          {bookingResult.showAccountLink && (
            <button
              onClick={(e) => { e.stopPropagation(); navigate('/account'); }}
              style={{
                display: 'block',
                marginTop: 8,
                padding: '6px 16px',
                borderRadius: 8,
                border: '1px solid #991b1b',
                background: 'transparent',
                color: '#991b1b',
                fontSize: 13,
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Set up ForeTees credentials
            </button>
          )}
        </div>
      )}

      {/* My Bookings */}
      {bookings.length > 0 && (
        <div style={{
          background: '#f0fdf4',
          border: '1px solid #bbf7d0',
          borderRadius: 8,
          marginBottom: 20,
          padding: 16,
        }}>
          <h3 style={{ color: '#166534', margin: '0 0 12px', fontSize: 15, fontWeight: 700 }}>
            My Upcoming Tee Times
          </h3>
          {bookings.map((b, i) => (
            <div
              key={i}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '8px 0',
                borderBottom: i < bookings.length - 1 ? '1px solid #dcfce7' : 'none',
                color: '#1f2937',
                fontSize: 14,
              }}
            >
              <span>{b.date}</span>
              <span style={{ fontWeight: 600 }}>{b.time}</span>
              <span style={{ color: '#6b7280', flex: 1 }}>{b.course}</span>
              {cancellingTtdata === b.ttdata ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12 }}>
                  <span style={{ color: '#6b7280' }}>Cancelling… this takes ~30s</span>
                  <span style={{
                    display: 'inline-block',
                    width: 14,
                    height: 14,
                    border: '2px solid #d1d5db',
                    borderTopColor: '#991b1b',
                    borderRadius: '50%',
                    animation: 'spin 0.8s linear infinite',
                  }} />
                </div>
              ) : (
                <button
                  onClick={async () => {
                    if (!window.confirm(`Cancel your tee time on ${b.date}?`)) return;
                    setBookingResult(null);
                    setCancellingTtdata(b.ttdata);
                    const result = await cancelTeeTime(b.date, b.time, b.ttdata);
                    setCancellingTtdata(null);
                    if (result?.success || result?.data?.success) {
                      setBookingResult({ type: 'success', message: result?.data?.messages?.[1] || result.message || 'Tee time cancelled' });
                      fetchTeeTimes(selectedDate);
                      fetchBookings();
                    } else {
                      setBookingResult({
                        type: 'error',
                        message: result?.detail || result?.data?.error || result?.message || 'Cancellation failed',
                      });
                    }
                  }}
                  disabled={!!cancellingTtdata}
                  style={{
                    background: '#fee2e2',
                    color: '#991b1b',
                    border: '1px solid #fca5a5',
                    borderRadius: 6,
                    padding: '4px 10px',
                    fontSize: 12,
                    fontWeight: 600,
                    cursor: cancellingTtdata ? 'not-allowed' : 'pointer',
                    opacity: cancellingTtdata ? 0.5 : 1,
                  }}
                >
                  Cancel
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Date Picker */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 16,
          marginBottom: 20,
        }}
      >
        <button
          onClick={() => handleDateChange(-1)}
          style={{
            padding: '8px 16px',
            fontSize: 18,
            background: 'transparent',
            color: theme.colors.primary,
            border: `1px solid ${theme.colors.primary}`,
            borderRadius: 6,
            cursor: 'pointer',
            fontWeight: 600,
          }}
        >
          &larr;
        </button>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontWeight: 700, fontSize: 18, color: theme.colors.textPrimary }}>
            {displayDate}
          </div>
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            style={{
              marginTop: 4,
              padding: '4px 8px',
              borderRadius: 6,
              border: `1px solid ${theme.colors.border || '#ccc'}`,
              background: theme.colors.surface || theme.colors.background,
              color: theme.colors.textPrimary,
              fontSize: 14,
            }}
          />
        </div>
        <button
          onClick={() => handleDateChange(1)}
          style={{
            padding: '8px 16px',
            fontSize: 18,
            background: 'transparent',
            color: theme.colors.primary,
            border: `1px solid ${theme.colors.primary}`,
            borderRadius: 6,
            cursor: 'pointer',
            fontWeight: 600,
          }}
        >
          &rarr;
        </button>
      </div>

      {/* Loading / Error */}
      {loading && (
        <div style={{ textAlign: 'center', padding: 40, color: '#6b7280' }}>
          Loading tee times...
        </div>
      )}
      {error && (
        <div
          style={{
            padding: 16,
            marginBottom: 16,
            background: '#fef2f2',
            color: '#991b1b',
            borderLeft: '4px solid #ef4444',
            borderRadius: 8,
          }}
        >
          {error}
        </div>
      )}

      {/* Tee Time Slots */}
      {!loading && teeTimes.length === 0 && !error && (
        <div style={{ textAlign: 'center', padding: 40, color: '#6b7280' }}>
          No tee times available for this date.
        </div>
      )}

      {teeTimes.map((slot, idx) => (
        <div
          key={idx}
          style={{
            background: '#fff',
            border: '1px solid #e5e7eb',
            borderRadius: 8,
            marginBottom: 10,
            padding: 14,
            display: 'flex',
            gap: 16,
            alignItems: 'flex-start',
          }}
        >
          {/* Time */}
          <div style={{ minWidth: 80, textAlign: 'center', padding: '8px 0' }}>
            <div style={{ fontWeight: 700, fontSize: 18, color: theme.colors.primary }}>
              {slot.time}
            </div>
            <div style={{ fontSize: 12, color: '#6b7280' }}>
              {slot.front_back === 'F' ? 'Front' : 'Back'}
            </div>
          </div>

          {/* Players */}
          <div style={{ flex: 1 }}>
            {slot.players.length > 0 ? (
              slot.players.map((p, pi) => (
                <div
                  key={pi}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    padding: '4px 0',
                    color: '#1f2937',
                    fontSize: 14,
                  }}
                >
                  <span>{p.name}</span>
                  {p.transport && (
                    <span
                      style={{
                        fontSize: 12,
                        color: '#6b7280',
                        background: '#f3f4f6',
                        padding: '2px 8px',
                        borderRadius: 4,
                      }}
                    >
                      {p.transport}
                    </span>
                  )}
                </div>
              ))
            ) : (
              <div style={{ color: '#9ca3af', fontStyle: 'italic', fontSize: 14 }}>
                Open
              </div>
            )}
          </div>

          {/* Open Slots + Book */}
          <div style={{ minWidth: 70, textAlign: 'center', padding: '8px 0' }}>
            {slot.open_slots > 0 ? (
              <>
                <span
                  style={{
                    display: 'inline-block',
                    background: '#10b981',
                    color: '#fff',
                    borderRadius: 12,
                    padding: '4px 12px',
                    fontSize: 13,
                    fontWeight: 600,
                  }}
                >
                  {slot.open_slots} open
                </span>
                <button
                  onClick={() => {
                    clearBookingError();
                    setBookingSlot(slot);
                  }}
                  style={{
                    display: 'block',
                    marginTop: 8,
                    padding: '6px 16px',
                    borderRadius: 8,
                    border: 'none',
                    background: theme.colors.primary,
                    color: '#fff',
                    fontSize: 13,
                    fontWeight: 600,
                    cursor: 'pointer',
                    width: '100%',
                  }}
                >
                  Book
                </button>
              </>
            ) : (
              <span
                style={{
                  display: 'inline-block',
                  background: '#e5e7eb',
                  color: '#6b7280',
                  borderRadius: 12,
                  padding: '4px 12px',
                  fontSize: 13,
                  fontWeight: 600,
                }}
              >
                Full
              </span>
            )}
          </div>
        </div>
      ))}

      {/* Booking Modal */}
      <BookingModal
        isOpen={bookingSlot !== null}
        onClose={() => {
          setBookingSlot(null);
          clearBookingError();
        }}
        onConfirm={handleBookConfirm}
        slot={bookingSlot}
        loading={bookingLoading}
      />
    </div>
  );
};

export default ForeTeesTeeSheet;
