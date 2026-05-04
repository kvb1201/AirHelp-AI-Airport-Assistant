import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { TtsPlaybackProvider } from './context/TtsPlaybackContext';
import './styles.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <TtsPlaybackProvider>
      <App />
    </TtsPlaybackProvider>
  </React.StrictMode>,
);
