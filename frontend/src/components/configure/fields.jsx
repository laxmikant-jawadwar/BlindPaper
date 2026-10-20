import { ChevronDown } from "lucide-react";
import { useId } from "react";

const control =
  "h-[38px] w-full rounded border bg-white px-3 text-[15px] text-ink placeholder:text-slate-400 " +
  "focus:border-brand focus:outline-2 focus:outline-brand/25 disabled:bg-slate-50";

const borderFor = (invalid) => (invalid ? "border-red-400" : "border-slate-300");

/** A white card with the blue numbered circle and a title, as in the Configure reference. */
export function NumberedCard({ number, title, subtitle, aside, children, className = "" }) {
  return (
    <section className={`rounded-lg border border-slate-200 bg-white p-[15px] ${className}`}>
      <div className="mb-3.5 flex flex-wrap items-start justify-between gap-x-3 gap-y-2">
        <div className="flex items-center gap-3">
          <span className="grid size-9 shrink-0 place-items-center rounded-full bg-[#cfe5fd] text-[17px] font-bold text-brand">{number}</span>
          <div>
            <h2 className="text-[19px] font-bold leading-tight text-ink">{title}</h2>
            {subtitle && <p className="mt-0.5 text-sm text-slate-500">{subtitle}</p>}
          </div>
        </div>
        {aside}
      </div>
      {children}
    </section>
  );
}

/** A compact labelled text input with its error underneath. */
export function TextField({ label, error, className = "", ...props }) {
  const id = useId();
  return (
    <div className={className}>
      <label htmlFor={id} className="mb-1 block text-[13px] font-medium leading-4 text-slate-700">
        {label}
      </label>
      <input id={id} aria-invalid={Boolean(error)} className={`${control} ${borderFor(error)}`} {...props} />
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  );
}

/** A bare select with the chevron drawn by us, so it looks the same everywhere. */
export function Select({ options, invalid = false, className = "", ...props }) {
  return (
    <span className={`relative block ${className}`}>
      <select className={`${control} ${borderFor(invalid)} appearance-none pr-8`} aria-invalid={invalid} {...props}>
        {options.map(({ value, label }) => (
          <option key={value} value={value}>
            {label}
          </option>
        ))}
      </select>
      <ChevronDown className="pointer-events-none absolute right-2.5 top-1/2 size-4 -translate-y-1/2 text-slate-500" aria-hidden="true" />
    </span>
  );
}

/** A select with a label above it. */
export function SelectField({ label, error, options, className = "", ...props }) {
  const id = useId();
  return (
    <div className={className}>
      <label htmlFor={id} className="mb-1 block text-[13px] font-medium leading-4 text-slate-700">
        {label}
      </label>
      <Select id={id} options={options} invalid={Boolean(error)} {...props} />
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  );
}
