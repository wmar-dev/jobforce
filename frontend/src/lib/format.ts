/**
 * Parse a plain "YYYY-MM-DD" date (no time/zone, e.g. `posted_at`) into a
 * `Date` in the browser's local timezone. `new Date("YYYY-MM-DD")` treats
 * the string as UTC midnight, which can render as the previous day in
 * timezones behind UTC — this avoids that off-by-one.
 */
export function parseDateOnly(isoDate: string): Date {
  const [year, month, day] = isoDate.split("-").map(Number);
  return new Date(year, month - 1, day);
}
