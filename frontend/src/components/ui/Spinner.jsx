import { Loader2 } from "lucide-react";

export default function Spinner({ label, className = "" }) {
  return (
    <span role="status" className={`inline-flex items-center gap-2 text-slate-500 ${className}`}>
      <Loader2 className="size-5 animate-spin text-brand" aria-hidden="true" />
      {label && <span className="text-sm font-medium">{label}</span>}
    </span>
  );
}
