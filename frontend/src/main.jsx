import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { TtsPlaybackProvider } from './context/TtsPlaybackContext';
import './styles/lotus-tokens.css';
import './styles.css';
import './styles/lotus-components.css';
import './styles/lotus-motion.css';
import './styles/home-experience.css';
import './styles/home-unified.css';
import './styles/home-motion.css';
import './styles/home-pillars.css';
import './styles/home-reviews.css';
import './styles/chat-drawer.css';
import './styles/boarding-pass-upload.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <TtsPlaybackProvider>
      <App />
    </TtsPlaybackProvider>
  </React.StrictMode>,
);
