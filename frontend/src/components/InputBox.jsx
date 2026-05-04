import React, { useState, useRef } from 'react';
import { transcribeAudio } from '../services/api';

/** Shown in chat fields so users phrase navigation as start → goal (matches backend parsers). */
export const CHAT_PLACEHOLDER = 'Type in English, Hindi, or Hinglish...';

/**
 * Chat input bar with voice support.
 * 
 * onSend signature: onSend(text, location?, opts?)
 *   opts: { inputMode: 'text'|'voice', whisperLang?: string }
 */
export default function InputBox({ onSend, isLoading, placeholder = CHAT_PLACEHOLDER }) {
  const [value, setValue] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [voiceMeta, setVoiceMeta] = useState(null); // { whisperLang }
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || isLoading) return;

    // If text came from voice transcription, pass voice metadata
    if (voiceMeta) {
      onSend(trimmed, null, { inputMode: 'voice', whisperLang: voiceMeta.whisperLang });
      setVoiceMeta(null);
    } else {
      onSend(trimmed, null, { inputMode: 'text' });
    }
    setValue('');
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        setIsRecording(false);
        try {
          const data = await transcribeAudio(audioBlob);
          if (data.transcript) {
            setValue(data.transcript);
            // Store voice metadata so we send input_mode=voice when user hits send
            setVoiceMeta({
              whisperLang: data.detected_language || null,
            });
          }
        } catch (err) {
          console.error("Transcription failed:", err);
        }
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Mic access denied:", err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
  };

  // Clear voice metadata when user manually types
  const handleInputChange = (e) => {
    setValue(e.target.value);
    if (voiceMeta) setVoiceMeta(null);
  };

  return (
    <form className="input-bar" onSubmit={handleSubmit} aria-label="Send a message">
      <button
        type="button"
        className={`voice-btn ${isRecording ? 'recording' : ''}`}
        onClick={isRecording ? stopRecording : startRecording}
        disabled={isLoading}
        aria-label={isRecording ? "Stop recording" : "Start voice input"}
      >
        <span className="ms">{isRecording ? 'mic_off' : 'mic'}</span>
      </button>
      <input
        className="chat-input"
        type="text"
        placeholder={placeholder}
        value={value}
        onChange={handleInputChange}
        disabled={isLoading}
        autoComplete="off"
        aria-label="Chat message"
      />
      {voiceMeta && (
        <span className="voice-badge" title={`Detected: ${voiceMeta.whisperLang || 'auto'}`}>
          🎤
        </span>
      )}
      <button
        className="send-btn"
        type="submit"
        disabled={!value.trim() || isLoading}
        aria-label="Send message"
      >
        <span className="ms">send</span>
      </button>
    </form>
  );
}
