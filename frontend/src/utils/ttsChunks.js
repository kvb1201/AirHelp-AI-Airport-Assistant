/**
 * Split assistant text for sequential Piper calls: prefer real newlines, else sentence-ish chunks.
 * @param {string} text
 * @returns {string[]}
 */
export function splitTextForTts(text) {
  const raw = String(text || '')
    .replace(/\r\n/g, '\n')
    .trim();
  if (!raw) return [];

  let lines = raw
    .split('\n')
    .map((l) => l.trim())
    .filter(Boolean);

  if (lines.length > 1) return lines;

  const single = lines[0] || raw;
  if (single.length <= 420) return [single];

  const parts = [];
  let buf = '';
  const bits = single.split(/(?<=[.!?])\s+/).filter(Boolean);
  for (const b of bits) {
    const next = buf ? `${buf} ${b}` : b;
    if (next.length > 420 && buf) {
      parts.push(buf.trim());
      buf = b;
    } else {
      buf = next;
    }
  }
  if (buf.trim()) parts.push(buf.trim());
  return parts.length ? parts : [single.slice(0, 420), single.slice(420)].filter(Boolean);
}
