import { Check } from "lucide-react";

const STEPS = ["Configure", "Generate", "Preview"];

/** Configure → Generate → Preview. `current` is 1, 2 or 3; earlier steps show a tick. */
export default function StepIndicator({ current }) {
  return (
    <ol aria-label="Progress" className="flex items-center gap-2 text-sm">
      {STEPS.map((name, index) => {
        const number = index + 1;
        const done = number < current;
        const active = number === current;
        return (
          <li key={name} className="flex items-center gap-2" aria-current={active ? "step" : undefined}>
            {index > 0 && <span className={`h-px w-5 sm:w-8 ${done || active ? "bg-brand" : "bg-slate-300"}`} aria-hidden="true" />}
            <span
              className={`grid size-6 place-items-center rounded-full text-xs font-bold ${
                active ? "bg-brand text-white" : done ? "bg-brand/15 text-brand" : "bg-slate-200 text-slate-500"
              }`}
            >
              {done ? <Check className="size-3.5" strokeWidth={3} aria-hidden="true" /> : number}
            </span>
            <span className={`hidden sm:inline ${active ? "font-semibold text-ink" : "text-slate-500"}`}>{name}</span>
          </li>
        );
      })}
    </ol>
  );
}
