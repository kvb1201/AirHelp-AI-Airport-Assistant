import React, { useState } from 'react';
import { sendFlightDetails, extractBoardingPass } from '../services/api';

export default function FlightQueryModal({ visible, onClose, onSaved, defaultLocation = 'entrance' }) {
  const [mode, setMode] = useState(null); // 'scan' | 'enter'
  const [flightNumber, setFlightNumber] = useState('');
  const [boardingTime, setBoardingTime] = useState('');
  const [departureTime, setDepartureTime] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [ocrResult, setOcrResult] = useState(null);
  const [ocrProcessing, setOcrProcessing] = useState(false);

  if (!visible) return null;

  const reset = () => {
    setMode(null);
    setFlightNumber('');
    setBoardingTime('');
    setDepartureTime('');
    setLoading(false);
    setError(null);
    setSelectedFile(null);
    setOcrResult(null);
    setOcrProcessing(false);
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

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setError(null);
      setOcrResult(null);
    }
  };

  const handleOcrProcess = async () => {
    if (!selectedFile) {
      setError('Please select a boarding pass image first');
      return;
    }

    setOcrProcessing(true);
    setError(null);

    try {
      const result = await extractBoardingPass(selectedFile);
      
      if (result.success && result.data) {
        setOcrResult(result.data);
        
        // Auto-populate form fields from OCR results
        if (result.data.flight_number) setFlightNumber(result.data.flight_number);
        if (result.data.boarding_time) setBoardingTime(result.data.boarding_time);
        if (result.data.departure_time) setDepartureTime(result.data.departure_time);
        
        setError(null);
      } else {
        setError(result.message || 'Failed to process boarding pass');
        setOcrResult(null);
      }
    } catch (err) {
      setError('Error processing boarding pass: ' + err.message);
      setOcrResult(null);
    } finally {
      setOcrProcessing(false);
    }
  };

  const handleSaveFromOcr = async () => {
    if (!ocrResult || !ocrResult.flight_number) {
      setError('Please process a boarding pass first');
      return;
    }

    setError(null);
    setLoading(true);
    
    try {
      const resp = await sendFlightDetails({
        userId: 'user_123',
        flightNumber: ocrResult.flight_number,
        boardingTime: ocrResult.boarding_time || '',
        departureTime: ocrResult.departure_time || '',
        location: defaultLocation,
      });
      setLoading(false);
      onSaved && onSaved(resp);
      handleClose();
    } catch (err) {
      setLoading(false);
      setError('Failed to save flight details');
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
              <button type="button" className="modal-opt" onClick={() => setMode('scan')}>Scan boarding pass</button>
            </div>
          )}

          {mode === 'scan' && (
            <div className="scan-mode">
              <div className="file-upload-section">
                <label htmlFor="boarding-pass-file" className="file-upload-label">
                  <span>📷 Choose Boarding Pass Image</span>
                </label>
                <input
                  type="file"
                  id="boarding-pass-file"
                  accept="image/*"
                  onChange={handleFileSelect}
                  style={{ display: 'none' }}
                />
                
                {selectedFile && (
                  <div className="selected-file">
                    <span>📄 {selectedFile.name}</span>
                  </div>
                )}

                <div className="scan-buttons">
                  <button 
                    type="button" 
                    onClick={handleOcrProcess}
                    disabled={!selectedFile || ocrProcessing}
                    className="process-btn"
                  >
                    {ocrProcessing ? 'Processing...' : 'Scan Boarding Pass'}
                  </button>
                </div>

                {ocrResult && (
                  <div className="ocr-results">
                    <h4>✅ Extracted Information:</h4>
                    <div className="ocr-info">
                      <div><strong>Flight:</strong> {ocrResult.flight_number || 'N/A'}</div>
                      <div><strong>Route:</strong> {ocrResult.from_to || 'N/A'}</div>
                      <div><strong>Date:</strong> {ocrResult.date || 'N/A'}</div>
                      <div><strong>Departure:</strong> {ocrResult.departure_time || 'N/A'}</div>
                      <div><strong>Boarding:</strong> {ocrResult.boarding_time || 'N/A'}</div>
                      <div><strong>Gate:</strong> {ocrResult.gate || 'N/A'}</div>
                      <div><strong>Seat:</strong> {ocrResult.seat || 'N/A'}</div>
                      <div><strong>Terminal:</strong> {ocrResult.terminal || 'N/A'}</div>
                    </div>
                    
                    <button 
                      type="button" 
                      onClick={handleSaveFromOcr}
                      disabled={loading}
                      className="save-ocr-btn"
                    >
                      {loading ? 'Saving...' : 'Save Flight Details'}
                    </button>
                  </div>
                )}
              </div>

              {error && <div className="form-error">{error}</div>}

              <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                <button type="button" onClick={() => setMode(null)}>Back</button>
                <button type="button" onClick={handleClose}>Close</button>
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

      <style jsx>{`
        .scan-mode {
          padding: 16px 0;
        }

        .file-upload-section {
          margin-bottom: 16px;
        }

        .file-upload-label {
          display: inline-block;
          padding: 12px 16px;
          background: #f0f0f0;
          border: 2px dashed #ccc;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.2s ease;
          margin-bottom: 12px;
        }

        .file-upload-label:hover {
          border-color: #007bff;
          background: #f8f9fa;
        }

        .selected-file {
          margin: 8px 0;
          padding: 8px 12px;
          background: #e9ecef;
          border-radius: 4px;
          font-size: 14px;
        }

        .scan-buttons {
          margin: 12px 0;
        }

        .process-btn, .save-ocr-btn {
          padding: 10px 16px;
          background: #007bff;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
          margin-right: 8px;
        }

        .process-btn:hover:not(:disabled), .save-ocr-btn:hover:not(:disabled) {
          background: #0056b3;
        }

        .process-btn:disabled, .save-ocr-btn:disabled {
          background: #6c757d;
          cursor: not-allowed;
        }

        .ocr-results {
          margin-top: 16px;
          padding: 16px;
          background: #f8f9fa;
          border-radius: 8px;
          border: 1px solid #dee2e6;
        }

        .ocr-results h4 {
          margin: 0 0 12px 0;
          color: #28a745;
        }

        .ocr-info {
          margin-bottom: 16px;
        }

        .ocr-info div {
          margin: 4px 0;
          font-size: 14px;
        }

        .ocr-info strong {
          display: inline-block;
          width: 80px;
          color: #495057;
        }

        .save-ocr-btn {
          background: #28a745;
        }

        .save-ocr-btn:hover:not(:disabled) {
          background: #1e7e34;
        }
      `}</style>
    </div>
  );
}
