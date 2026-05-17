import React, { useState } from 'react';
import { extractBoardingPass } from '../services/api';

const BoardingPassUpload = ({ onBoardingPassProcessed }) => {
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setError(null);
      setResult(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a boarding pass image first');
      return;
    }

    setUploading(true);
    setError(null);
    setResult(null);

    try {
      console.log('[Upload] Starting upload:', selectedFile.name, selectedFile.type);
      
      // Use the safe API function with all error handling
      const data = await extractBoardingPass(selectedFile);

      console.log('[Upload] Received data:', data.success, data.message);

      if (data.success) {
        setResult(data.data);
        if (onBoardingPassProcessed) {
          onBoardingPassProcessed(data.data);
        }
      } else {
        setError(data.message || 'Failed to process boarding pass');
      }
    } catch (err) {
      console.error('[Upload] Error:', err);
      setError('Error uploading file: ' + err.message);
    } finally {
      setUploading(false);
    }
  };

  const handleChatWithBoardingPass = async () => {
    if (!selectedFile || !result) {
      setError('Please upload and process a boarding pass first');
      return;
    }

    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('user_id', 'test_user');
    formData.append('message', 'I have uploaded my boarding pass, can you help me navigate to my gate?');
    formData.append('language', 'en');

    try {
      const response = await fetch('/api/chat/image', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (data.response) {
        setResult(prev => ({
          ...prev,
          chatResponse: data.response,
          context: data.context
        }));
      } else {
        setError('Failed to get chat response');
      }
    } catch (err) {
      setError('Error in chat: ' + err.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="boarding-pass-upload">
      <div className="upload-section">
        <h3 className="section-title">Boarding pass scanner</h3>
        
        <div className="file-input-wrapper">
          <input
            type="file"
            id="boarding-pass-file"
            accept="image/*"
            onChange={handleFileSelect}
            className="file-input"
          />
          <label htmlFor="boarding-pass-file" className="file-input-label">
            <span className="ms" aria-hidden="true">upload_file</span>
            <span>Choose Boarding Pass Image</span>
          </label>
        </div>

        {selectedFile && (
          <div className="selected-file">
            <span className="file-name">📄 {selectedFile.name}</span>
          </div>
        )}

        <div className="button-group">
          <button
            onClick={handleUpload}
            disabled={!selectedFile || uploading}
            className="btn btn-primary upload-btn"
          >
            {uploading ? (
              <>
                <span className="ms">hourglass_empty</span>
                Processing...
              </>
            ) : (
              <>
                <span className="ms">document_scanner</span>
                Scan Boarding Pass
              </>
            )}
          </button>

          {result && (
            <button
              onClick={handleChatWithBoardingPass}
              disabled={uploading}
              className="btn btn-secondary chat-btn"
            >
              <span className="ms">chat</span>
              Chat with Assistant
            </button>
          )}
        </div>

        {error && (
          <div className="error-message">
            <span className="ms">error</span>
            {error}
          </div>
        )}
      </div>

      {result && (
        <div className="result-section">
          <h4 className="result-title">✅ Boarding Pass Information</h4>
          <div className="boarding-pass-info">
            <div className="info-grid">
              <div className="info-item">
                <span className="info-label">Flight:</span>
                <span className="info-value">{result.flight_number || 'N/A'}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Route:</span>
                <span className="info-value">{result.from_to || 'N/A'}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Date:</span>
                <span className="info-value">{result.date || 'N/A'}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Time:</span>
                <span className="info-value">{result.departure_time || 'N/A'}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Gate:</span>
                <span className="info-value">{result.gate || 'N/A'}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Seat:</span>
                <span className="info-value">{result.seat || 'N/A'}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Terminal:</span>
                <span className="info-value">{result.terminal || 'N/A'}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Boarding Time:</span>
                <span className="info-value">{result.boarding_time || 'N/A'}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Confidence:</span>
                <span className="info-value">{result.confidence || 0}%</span>
              </div>
            </div>
          </div>

          {result.chatResponse && (
            <div className="chat-response">
              <h5>💬 Assistant Response:</h5>
              <div className="response-text">{result.chatResponse}</div>
            </div>
          )}

          {result.method && (
            <div className="method-info">
              <small>🔧 Extraction Method: {result.method} | 📱 Offline Mode: {result.offline ? 'Yes' : 'No'}</small>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default BoardingPassUpload;
