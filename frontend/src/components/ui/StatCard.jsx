const TONES = {
  blue: { card: "bg-tint-blue border-blue-100", ring: "bg-tint-blue-strong", solid: "", icon: "text-blue-600", value: "text-blue-950", label: "text-blue-900" },
  orange: { card: "bg-tint-orange border-orange-100", ring: "bg-tint-orange-strong", solid: "bg-amber-500", icon: "text-white", value: "text-amber-900", label: "text-amber-800" },
  green: { card: "bg-tint-green border-green-100", ring: "bg-tint-green-strong", solid: "bg-green-600", icon: "text-white", value: "text-green-900", label: "text-green-800" },
  red: { card: "bg-tint-red border-red-100", ring: "bg-tint-red-strong", solid: "bg-red-500", icon: "text-white", value: "text-red-900", label: "text-red-800" },
};

/**
 * A big number with its label, on a tinted card (blue, orange, green or red).
 * `compact` is the slimmer card used on the admin dashboard.
 */
export default function StatCard({ tone = "blue", icon: Icon, value, label, compact = false }) {
  const style = TONES[tone];
  const ring = compact ? "size-[62px]" : "size-[72px]";
  const solid = compact ? "size-[44px]" : "size-[52px]";
  return (
    <div className={`flex items-center rounded-xl border ${compact ? "gap-4 px-5 py-4" : "gap-5 px-6 py-6"} ${style.card}`}>
      <span className={`grid shrink-0 place-items-center rounded-full ${ring} ${style.ring}`}>
        {style.solid ? (
          <span className={`grid place-items-center rounded-full ${solid} ${style.solid}`}>
            <Icon className={`${compact ? "size-6" : "size-7"} ${style.icon}`} strokeWidth={2.5} aria-hidden="true" />
          </span>
        ) : (
          <Icon className={`${compact ? "size-8" : "size-9"} ${style.icon}`} fill="currentColor" fillOpacity={0.15} aria-hidden="true" />
        )}
      </span>
      <div className="min-w-0">
        <div className={`font-bold leading-tight ${compact ? "text-[30px]" : "text-[34px]"} ${style.value}`}>{value}</div>
        <div className={`${compact ? "text-[17px]" : "text-lg"} ${style.label}`}>{label}</div>
      </div>
    </div>
  );
}
