/** "2026-10-15T09:30:00+00:00" -> "15 Oct 2026". Returns "—" for missing dates. */
export function formatDate(iso) {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
}

export function formatDateTime(iso) {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return `${formatDate(iso)}, ${date.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" })}`;
}

const TITLES = new Set(["prof", "prof.", "dr", "dr.", "mr", "mr.", "ms", "ms.", "mrs", "mrs."]);

/** The letter shown in an avatar: the first letter of the name, skipping titles such as "Prof.". */
export function initial(name) {
  const word = (name || "").split(/\s+/).find((w) => w && !TITLES.has(w.toLowerCase()));
  return (word || name || "?").charAt(0).toUpperCase();
}

/** 0 -> "a)", 1 -> "b)" ... */
export function subLabel(index) {
  return `${String.fromCharCode(97 + index)})`;
}

/** 40 -> "40", 33.33 -> "33.33" */
export function formatMarks(value) {
  const number = Number(value);
  return Number.isInteger(number) ? String(number) : String(Number(number.toFixed(2)));
}
