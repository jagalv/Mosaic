// Number formatting for financial figures. All callers should render the result
// in tabular figures (the `.tnum` utility / Geist Mono).

/** Actual USD -> whole millions, negatives in parentheses, missing as —. */
export function fmtMillions(value: number | undefined): string {
  if (value === undefined || value === null) return "—";
  const millions = Math.round(value / 1_000_000);
  if (millions < 0) return `(${Math.abs(millions).toLocaleString("en-US")})`;
  return millions.toLocaleString("en-US");
}

/** Actual USD -> compact $ (T/B/M) for metric cards. */
export function fmtCompactUSD(value: number | undefined | null): string {
  if (value === undefined || value === null) return "—";
  const sign = value < 0 ? "-" : "";
  const abs = Math.abs(value);
  if (abs >= 1e12) return `${sign}$${(abs / 1e12).toFixed(2)}T`;
  if (abs >= 1e9) return `${sign}$${(abs / 1e9).toFixed(1)}B`;
  if (abs >= 1e6) return `${sign}$${(abs / 1e6).toFixed(0)}M`;
  return `${sign}$${abs.toLocaleString("en-US")}`;
}

/** Percentage change current vs prior; null when not computable. */
export function pctChange(
  curr: number | undefined,
  prev: number | undefined,
): number | null {
  if (curr == null || prev == null || prev === 0) return null;
  return ((curr - prev) / Math.abs(prev)) * 100;
}

/** A ratio (0..1) -> percentage string, e.g. 0.462 -> "46.2%". */
export function fmtPercent(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return "—";
  return `${(value * 100).toFixed(1)}%`;
}
