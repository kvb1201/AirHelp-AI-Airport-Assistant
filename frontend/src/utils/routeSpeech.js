/**
 * Flatten route copy for Piper TTS (plain sentences).
 */

export function buildRouteSpeechText(route) {
  if (!route) return '';
  const parts = [];
  const sub = route.simple_journey?.subtitle;
  if (sub) parts.push(sub);

  const bullets = route.simple_journey?.bullets;
  if (Array.isArray(bullets) && bullets.length > 0) {
    bullets.forEach((line) => {
      if (line && String(line).trim()) parts.push(String(line).trim());
    });
  } else if (Array.isArray(route.steps) && route.steps.length > 0) {
    parts.push('Here are the walking steps.');
    route.steps.forEach((s, i) => {
      if (s && String(s).trim()) parts.push(`Step ${i + 1}. ${String(s).trim()}`);
    });
  }

  return parts.join('. ').trim();
}

/** Current guided checkpoint question + cues. */
export function buildGuidedCheckpointSpeech(checkpoint) {
  if (!checkpoint) return '';
  const bits = [];
  if (checkpoint.question) bits.push(String(checkpoint.question).trim());
  if (Array.isArray(checkpoint.look_for) && checkpoint.look_for.length > 0) {
    const cues = checkpoint.look_for.map((x) => String(x).trim()).filter(Boolean);
    if (cues.length) bits.push(`Look for: ${cues.join(', ')}.`);
  }
  return bits.join(' ');
}
