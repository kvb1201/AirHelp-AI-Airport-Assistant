export const lotusEase = [0.22, 1, 0.36, 1];
export const lotusEaseOut = [0.16, 1, 0.3, 1];
export const lotusSpring = { type: 'spring', stiffness: 380, damping: 36 };
export const lotusSpringSoft = { type: 'spring', stiffness: 280, damping: 32 };

export const VIEW_ORDER = {
  home: 0,
  chat: 1,
  nav: 2,
  facilities: 3,
  lostfound: 4,
  map: 5,
  operator: 6,
  profile: 7,
};

export function viewDirection(fromKey, toKey) {
  const a = VIEW_ORDER[fromKey] ?? 0;
  const b = VIEW_ORDER[toKey] ?? 0;
  if (b === a) return 0;
  return b > a ? 1 : -1;
}
