import React, {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
} from 'react';
import { fetchTtsAudio } from '../services/api';
import { splitTextForTts } from '../utils/ttsChunks';

const TtsPlaybackContext = createContext(null);

/**
 * English-only Piper: fetch WAV per line/chunk, play in order with pause/resume/stop.
 */
export function TtsPlaybackProvider({ children }) {
  const genRef = useRef(0);
  const pausedRef = useRef(false);
  const audioRef = useRef(null);
  const urlRef = useRef(null);

  const [activeSessionId, setActiveSessionId] = useState(null);
  const [phase, setPhase] = useState('idle'); // idle | fetching | playing | paused
  const [lineProgress, setLineProgress] = useState({ cur: 0, total: 0 });
  const [lastError, setLastError] = useState('');

  const cleanupAudio = useCallback(() => {
    if (audioRef.current) {
      try {
        audioRef.current.pause();
      } catch {
        /* ignore */
      }
      audioRef.current = null;
    }
    if (urlRef.current) {
      URL.revokeObjectURL(urlRef.current);
      urlRef.current = null;
    }
  }, []);

  const stop = useCallback(() => {
    genRef.current += 1;
    pausedRef.current = false;
    cleanupAudio();
    setActiveSessionId(null);
    setPhase('idle');
    setLineProgress({ cur: 0, total: 0 });
  }, [cleanupAudio]);

  const pause = useCallback(() => {
    pausedRef.current = true;
    if (audioRef.current && !audioRef.current.ended) {
      try {
        audioRef.current.pause();
      } catch {
        /* ignore */
      }
    }
    setPhase((p) => (p === 'playing' || p === 'fetching' ? 'paused' : p));
  }, []);

  const resume = useCallback(() => {
    pausedRef.current = false;
    setPhase((p) => (p === 'paused' ? 'playing' : p));
    if (audioRef.current && audioRef.current.paused && !audioRef.current.ended) {
      void audioRef.current.play().catch(() => {});
    }
  }, []);

  const playClip = useCallback(async (url, isAlive, isPaused) => {
    const audio = new Audio(url);
    audioRef.current = audio;
    await new Promise((resolve, reject) => {
      let settled = false;
      let tick = null;
      const finish = () => {
        if (tick) clearInterval(tick);
        tick = null;
      };
      const done = () => {
        if (settled) return;
        settled = true;
        finish();
        resolve();
      };
      const fail = (e) => {
        if (settled) return;
        settled = true;
        finish();
        reject(e);
      };
      audio.onended = done;
      audio.onerror = () => fail(new Error('Audio playback error'));
      tick = setInterval(() => {
        if (!isAlive()) {
          audio.pause();
          done();
          return;
        }
        if (isPaused()) {
          if (!audio.paused) audio.pause();
        } else if (audio.paused && !audio.ended) {
          void audio.play().catch(() => {});
        }
      }, 90);
      void audio.play().catch((e) => {
        fail(e);
      });
    });
  }, []);

  const play = useCallback(
    async (sessionId, text) => {
      const sid = sessionId ?? 'default';
      const chunks = splitTextForTts(text);
      if (!chunks.length) return { ok: false, error: 'Nothing to read.' };

      genRef.current += 1;
      const myGen = genRef.current;
      pausedRef.current = false;
      cleanupAudio();
      setLastError('');
      setActiveSessionId(sid);
      setLineProgress({ cur: 0, total: chunks.length });
      setPhase('fetching');

      try {
        for (let i = 0; i < chunks.length; i++) {
          if (genRef.current !== myGen) return { ok: false, error: 'Stopped.' };
          while (pausedRef.current && genRef.current === myGen) {
            setPhase('paused');
            await new Promise((r) => setTimeout(r, 100));
          }
          if (genRef.current !== myGen) return { ok: false, error: 'Stopped.' };

          setLineProgress({ cur: i + 1, total: chunks.length });
          setPhase('fetching');
          const blob = await fetchTtsAudio(chunks[i], 'en');
          if (genRef.current !== myGen) return { ok: false, error: 'Stopped.' };
          while (pausedRef.current && genRef.current === myGen) {
            setPhase('paused');
            await new Promise((r) => setTimeout(r, 100));
          }
          if (genRef.current !== myGen) return { ok: false, error: 'Stopped.' };

          cleanupAudio();
          const url = URL.createObjectURL(blob);
          urlRef.current = url;
          setPhase('playing');
          await playClip(url, () => genRef.current === myGen, () => pausedRef.current);
          cleanupAudio();
        }

        if (genRef.current === myGen) {
          setPhase('idle');
          setActiveSessionId(null);
          setLineProgress({ cur: 0, total: 0 });
        }
        return { ok: true };
      } catch (e) {
        const msg =
          e?.status === 503 || e?.status === 500
            ? 'Set up Piper on the laptop (see API /tts/status).'
            : e?.message || 'Could not play audio.';
        setLastError(msg);
        if (genRef.current === myGen) {
          setPhase('idle');
          setActiveSessionId(null);
          setLineProgress({ cur: 0, total: 0 });
        }
        cleanupAudio();
        return { ok: false, error: msg };
      }
    },
    [cleanupAudio, playClip],
  );

  const value = useMemo(
    () => ({
      play,
      stop,
      pause,
      resume,
      activeSessionId,
      phase,
      lineProgress,
      lastError,
      clearError: () => setLastError(''),
    }),
    [play, stop, pause, resume, activeSessionId, phase, lineProgress, lastError],
  );

  return <TtsPlaybackContext.Provider value={value}>{children}</TtsPlaybackContext.Provider>;
}

export function useTtsPlayback() {
  const ctx = useContext(TtsPlaybackContext);
  if (!ctx) throw new Error('useTtsPlayback must be used inside TtsPlaybackProvider');
  return ctx;
}
