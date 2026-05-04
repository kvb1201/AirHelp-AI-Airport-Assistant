import React, { useState } from 'react';
import { sendFlightDetails } from '../services/api';

export default function FlightQueryModal({ visible, onClose, onSaved, defaultLocation = 'entrance' }) {
  const [mode, setMode] = useState(null); // 'scan' | 'enter'
  const [flightNumber, setFlightNumber] = useState('');
  const [boardingTime, setBoardingTime] = useState('');
  const [departureTime, setDepartureTime] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!visible) return null;

  const reset = () => {
    setMode(null);
    setFlightNumber('');
    setBoardingTime('');
    setDepartureTime('');
    setLoading(false);
    setError(null);
  };

  const handleClose = () => {
    reset();
    onClose && onClose();
  };

  const handleSave = async () => {
    setError(null);
    if (!flightNumber) return setError('Please enter a flight number');
    setLoading(true);
    try {
      const resp = await sendFlightDetails({
        userId: 'user_123',
        flightNumber,
        boardingTime,
        departureTime,
        location: defaultLocation,
      });
      setLoading(false);
      onSaved && onSaved(resp);
      handleClose();
    } catch (err) {
      setLoading(false);
      setError('Failed to save flight');
    }
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-card">
        <header className="modal-header">
          <h3>Flight Queries</h3>
          <button type="button" className="modal-close" onClick={handleClose}>✕</button>
        </header>

        <div className="modal-body">
          {!mode && (
            <div className="modal-options">
              <button type="button" className="modal-opt" onClick={() => setMode('enter')}>Enter flight details</button>
              <button type="button" className="modal-opt" onClick={() => setMode('scan')}>Scan boarding pass (dummy)</button>
            </div>
          )}

          {mode === 'scan' && (
            <div>
              <p>This is a dummy scan option for now. Use Enter flight details to save a flight.</p>
              <div style={{ display: 'flex', gap: 8 }}>
                <button type="button" onClick={handleClose}>Close</button>
                <button type="button" onClick={() => { setMode(null); }}>Back</button>
              </div>
            </div>
          )}

          {mode === 'enter' && (
            <div className="flight-form">
              <label>Flight number</label>
              <input value={flightNumber} onChange={(e) => setFlightNumber(e.target.value)} placeholder="AI 143" />

              <label>Boarding time (HH:MM)</label>
              <input value={boardingTime} onChange={(e) => setBoardingTime(e.target.value)} placeholder="10:35" />

              <label>Departure time (HH:MM)</label>
              <input value={departureTime} onChange={(e) => setDepartureTime(e.target.value)} placeholder="11:20" />

              {error && <div className="form-error">{error}</div>}

              <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                <button type="button" onClick={() => setMode(null)}>Back</button>
                <button type="button" onClick={handleSave} disabled={loading}>{loading ? 'Saving...' : 'Save flight'}</button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
