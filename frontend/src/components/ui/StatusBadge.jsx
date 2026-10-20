const STYLES = {
  "Pending Approval": "bg-[#fff1cc] text-amber-700",
  Pending: "bg-[#fff1cc] text-amber-700",
  Approved: "bg-[#e1f6e6] text-green-700",
  Rejected: "bg-[#fde7e7] text-red-600",
  Draft: "bg-slate-100 text-slate-600",
};

const SIZES = {
  md: "px-3 py-1.5 text-sm",
  sm: "px-3 py-1 text-xs",
};

/**
 * The coloured pill for a paper's status. `label` can shorten it (e.g. "Pending" in a narrow table);
 * size="sm" is for compact tables.
 */
export default function StatusBadge({ status, label, size = "md", className = "" }) {
  return (
    <span
      className={`inline-block whitespace-nowrap rounded-md font-medium ${SIZES[size]} ${STYLES[status] || STYLES.Draft} ${className}`}
    >
      {label || status}
    </span>
  );
}
