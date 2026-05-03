/**
 * Human-readable walking time from navigation payload (includes congestion bands when present).
 */
export function formatRouteTimeLine(route, navPayload) {
  const c = route?.congestion || navPayload?.congestion;
  const mid = route?.total_time_minutes ?? c?.total_time_minutes_mid;
  if (mid == null) return null;
  if (
    c &&
    typeof c.total_time_minutes_low === 'number' &&
    typeof c.total_time_minutes_high === 'number' &&
    c.total_time_minutes_low !== c.total_time_minutes_high
  ) {
    return `Est. ${mid} min (typical range about ${c.total_time_minutes_low}–${c.total_time_minutes_high} min)`;
  }
  return `About ${mid} min walking`;
}

/** Short line for route cards (e.g. map option buttons). */
export function formatRouteTimeCompact(route) {
  const c = route?.congestion;
  const mid = route?.total_time_minutes;
  if (mid == null) return '—';
  if (
    c &&
    typeof c.total_time_minutes_low === 'number' &&
    typeof c.total_time_minutes_high === 'number' &&
    c.total_time_minutes_low !== c.total_time_minutes_high
  ) {
    return `${mid} min · about ${c.total_time_minutes_low}–${c.total_time_minutes_high}`;
  }
  return `${mid} min`;
}
