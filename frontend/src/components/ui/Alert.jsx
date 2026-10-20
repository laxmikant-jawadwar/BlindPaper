import { AlertTriangle, CheckCircle2, Info, XCircle } from "lucide-react";

const TONES = {
  error: { box: "border-red-200 bg-red-50 text-red-800", icon: XCircle },
  warning: { box: "border-amber-200 bg-amber-50 text-amber-800", icon: AlertTriangle },
  success: { box: "border-green-200 bg-green-50 text-green-800", icon: CheckCircle2 },
  info: { box: "border-blue-200 bg-blue-50 text-blue-800", icon: Info },
};

/** A coloured message box. `title` is optional; children can be text or a list. */
export default function Alert({ tone = "info", title, children, className = "" }) {
  const { box, icon: Icon } = TONES[tone];
  return (
    <div role={tone === "error" ? "alert" : "status"} className={`flex gap-3 rounded-lg border px-4 py-3 text-sm ${box} ${className}`}>
      <Icon className="mt-0.5 size-5 shrink-0" aria-hidden="true" />
      <div className="min-w-0">
        {title && <p className="font-semibold">{title}</p>}
        <div>{children}</div>
      </div>
    </div>
  );
}
