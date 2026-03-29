/**
 * Rich demo fallbacks when the API returns no rows (or null).
 *
 * - **Default**: empty responses are filled with realistic sample data so charts and tables work
 *   without a running backend. Opt out with `NEXT_PUBLIC_USE_DEMO_DATA=false` (e.g. production with a real empty DB).
 * - `NEXT_PUBLIC_FORCE_DEMO_DATA=true`: always use demo lists for those resources (ignores non-empty API).
 */

export function forceDemoOnly(): boolean {
  return process.env.NEXT_PUBLIC_FORCE_DEMO_DATA === "true";
}

export function demoFallbackEnabled(): boolean {
  return process.env.NEXT_PUBLIC_USE_DEMO_DATA !== "false";
}

export function emptyOrDemo<T>(api: T[] | undefined | null, demo: T[]): T[] {
  if (forceDemoOnly()) return demo;
  const list = api ?? [];
  if (list.length > 0) return list;
  if (demoFallbackEnabled()) return demo;
  return [];
}

export function nullOrDemo<T>(api: T | null | undefined, demo: T): T | null {
  if (forceDemoOnly()) return demo;
  if (api != null) return api;
  if (demoFallbackEnabled()) return demo;
  return null;
}
