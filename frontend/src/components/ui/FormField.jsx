import { useId } from "react";

export const inputClasses =
  "h-11 w-full rounded-lg border border-slate-300 bg-white px-3.5 text-[15px] text-ink placeholder:text-slate-400 " +
  "focus:border-brand focus:outline-2 focus:outline-brand/25 disabled:bg-slate-50 disabled:text-slate-500";

/**
 * A labelled input (or select, when `options` is given). `error` shows a message under the field.
 * Extra props (value, onChange, type, ...) go straight to the control.
 */
export default function FormField({ label, hint, error, options, className = "", ...props }) {
  const id = useId();
  const describedBy = error ? `${id}-error` : hint ? `${id}-hint` : undefined;
  const control = options ? (
    <select id={id} aria-invalid={Boolean(error)} aria-describedby={describedBy} className={`${inputClasses} pr-8`} {...props}>
      {options.map((option) => {
        const { value, label: text } = typeof option === "string" ? { value: option, label: option } : option;
        return (
          <option key={value} value={value}>
            {text}
          </option>
        );
      })}
    </select>
  ) : (
    <input id={id} aria-invalid={Boolean(error)} aria-describedby={describedBy} className={inputClasses} {...props} />
  );

  return (
    <div className={className}>
      <label htmlFor={id} className="mb-1.5 block text-sm font-medium text-slate-700">
        {label}
      </label>
      {control}
      {error ? (
        <p id={`${id}-error`} className="mt-1 text-sm text-red-600">
          {error}
        </p>
      ) : (
        hint && (
          <p id={`${id}-hint`} className="mt-1 text-xs text-slate-500">
            {hint}
          </p>
        )
      )}
    </div>
  );
}
