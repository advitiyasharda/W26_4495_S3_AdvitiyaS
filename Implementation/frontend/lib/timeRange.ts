export type TimeRangeId = "24h" | "7d" | "30d" | "all";

export const TIME_RANGE_OPTIONS: { id: TimeRangeId; label: string }[] = [
  { id: "24h", label: "Last 24 hours" },
  { id: "7d", label: "Last 7 days" },
  { id: "30d", label: "Last 30 days" },
  { id: "all", label: "All loaded data" },
];

/** Milliseconds from now for range start (exclusive of 'all'). */
export function rangeStartMs(id: TimeRangeId): number | null {
  if (id === "all") return null;
  const now = Date.now();
  if (id === "24h") return now - 24 * 60 * 60 * 1000;
  if (id === "7d") return now - 7 * 24 * 60 * 60 * 1000;
  return now - 30 * 24 * 60 * 60 * 1000;
}

export function filterByTimeRange<T>(items: T[], getTime: (item: T) => string, range: TimeRangeId): T[] {
  const start = rangeStartMs(range);
  if (start === null) return items;
  return items.filter((item) => new Date(getTime(item)).getTime() >= start);
}

export function rangeLabelForExport(range: TimeRangeId): string {
  return TIME_RANGE_OPTIONS.find((o) => o.id === range)?.label ?? range;
}
