import React, { useState } from 'react';

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

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      // Call the OCR API
      const response = await fetch('/api/ocr/boarding-pass', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (data.success) {
        setResult(data.data);
        if (onBoardingPassProcessed) {
          onBoardingPassProcessed(data.data);
        }
      } else {
        setError(data.message || 'Failed to process boarding pass');
      }
    } catch (err) {
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
        <h3 className="section-title">📷 Boarding Pass Scanner</h3>
        
        <div className="file-input-wrapper">
          <input
            type="file"
            id="boarding-pass-file"
            accept="image/*"
            onChange={handleFileSelect}
            className="file-input"
          />
          <label htmlFor="boarding-pass-file" className="file-input-label">
            <span className="ms">upload_file</span>
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

      <style jsx>{`
        .boarding-pass-upload {
          background: var(--surface-container-low);
          border-radius: var(--radius-md);
          padding: 20px;
          margin: 20px 0;
          border: 1px solid var(--outline-variant);
        }

        .upload-section h3 {
          margin-bottom: 20px;
          color: var(--on-surface);
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .file-input-wrapper {
          position: relative;
          margin-bottom: 16px;
        }

        .file-input {
          display: none;
        }

        .file-input-label {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 16px;
          background: var(--surface-container-highest);
          border: 2px dashed var(--outline-variant);
          border-radius: var(--radius-md);
          cursor: pointer;
          transition: all 0.2s ease;
          color: var(--on-surface-variant);
        }

        .file-input-label:hover {
          border-color: var(--primary);
          background: var(--surface-container);
          color: var(--primary);
        }

        .selected-file {
          margin-bottom: 16px;
          padding: 8px 12px;
          background: var(--surface-container);
          border-radius: var(--radius-sm);
          color: var(--on-surface);
        }

        .button-group {
          display: flex;
          gap: 12px;
          margin-bottom: 16px;
        }

        .upload-btn, .chat-btn {
          padding: 10px 16px;
          border-radius: var(--radius-md);
          border: none;
          font-family: var(--font-body);
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .upload-btn {
          background: var(--primary);
          color: white;
        }

        .upload-btn:hover:not(:disabled) {
          background: var(--primary-container);
          color: var(--on-primary-container);
        }

        .chat-btn {
          background: var(--secondary);
          color: white;
        }

        .chat-btn:hover:not(:disabled) {
          background: var(--secondary-container);
          color: var(--on-secondary-container);
        }

        .upload-btn:disabled, .chat-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .error-message {
          padding: 12px;
          background: var(--error-container);
          color: var(--on-error-container);
          border-radius: var(--radius-sm);
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .result-section {
          margin-top: 24px;
          padding-top: 20px;
          border-top: 1px solid var(--outline-variant);
        }

        .result-title {
          color: var(--primary);
          margin-bottom: 16px;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .info-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 12px;
          margin-bottom: 20px;
        }

        .info-item {
          display: flex;
          justify-content: space-between;
          padding: 8px 12px;
          background: var(--surface-container);
          border-radius: var(--radius-sm);
        }

        .info-label {
          font-weight: 600;
          color: var(--on-surface-variant);
        }

        .info-value {
          color: var(--on-surface);
          font-weight: 500;
        }

        .chat-response {
          margin-top: 20px;
          padding: 16px;
          background: var(--surface-container);
          border-radius: var(--radius-md);
          border-left: 4px solid var(--primary);
        }

        .chat-response h5 {
          margin-bottom: 8px;
          color: var(--primary);
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .response-text {
          color: var(--on-surface);
          line-height: 1.5;
        }

        .method-info {
          margin-top: 16px;
          text-align: center;
          color: var(--on-surface-variant);
        }
      `}</style>
    </div>
  );
};

export default BoardingPassUpload;
