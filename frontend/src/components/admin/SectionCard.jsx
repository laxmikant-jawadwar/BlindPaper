import { ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";

const TONES = {
  blue: "bg-tint-blue-strong text-blue-600",
  amber: "bg-tint-orange-strong text-amber-500",
};

/** A white card with a round icon, a title and an optional "View All" link, around a table or list. */
export default function SectionCard({ icon: Icon, tone = "blue", title, viewAllTo, subtitle, children, className = "" }) {
  return (
    <section className={`min-w-0 rounded-xl border border-slate-200 bg-white shadow-[0_1px_2px_rgba(15,27,51,0.04)] ${className}`}>
      <header className="flex items-center justify-between gap-3 px-5 pb-2.5 pt-3.5">
        <div className="flex min-w-0 items-center gap-3">
          <span className={`grid size-10 shrink-0 place-items-center rounded-full ${TONES[tone]}`}>
            <Icon className="size-5" aria-hidden="true" />
          </span>
          <div className="min-w-0">
            <h2 className="text-xl font-semibold text-ink">{title}</h2>
            {subtitle && <p className="text-sm text-slate-500">{subtitle}</p>}
          </div>
        </div>
        {viewAllTo && (
          <Link to={viewAllTo} className="inline-flex shrink-0 items-center gap-1.5 text-[15px] font-medium text-brand hover:underline">
            View All <ArrowRight className="size-4" aria-hidden="true" />
          </Link>
        )}
      </header>
      <div className="px-3 pb-4 sm:px-4">{children}</div>
    </section>
  );
}
