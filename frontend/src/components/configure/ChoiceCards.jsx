import { DIFFICULTIES, EXAM_TYPES } from "../../lib/constants";
import { NumberedCard } from "./fields";

/** A selectable card with a radio look. The real radio input stays in the page for keyboards and screen readers. */
function RadioCard({ name, value, checked, onChange, label, description, compact = false }) {
  return (
    <label
      className={`flex cursor-pointer items-center gap-2.5 rounded-md border px-2.5 transition-colors sm:gap-3 sm:px-3.5 has-focus-visible:outline-2 has-focus-visible:outline-offset-2 has-focus-visible:outline-brand ${
        compact ? "h-10" : "py-3.5"
      } ${checked ? "border-[#266efe] bg-[#e3f0fe]" : "border-slate-200 bg-white hover:bg-slate-50"}`}
    >
      <input type="radio" name={name} value={value} checked={checked} onChange={() => onChange(value)} className="sr-only" />
      <span
        aria-hidden="true"
        className={`grid size-[22px] shrink-0 place-items-center rounded-full border-2 ${checked ? "border-brand bg-white" : "border-slate-300 bg-white"}`}
      >
        {checked && <span className="size-2.5 rounded-full bg-brand" />}
      </span>
      <span className="min-w-0">
        <span className={`block font-semibold text-ink ${compact ? "text-[14px]" : "text-[17px]"}`}>{label}</span>
        {description && <span className="block text-[13px] text-slate-500">{description}</span>}
      </span>
    </label>
  );
}

/** 2 · Exam Type: MSE or ESE. Choosing one also switches the template shown on the right. */
export function ExamTypeCard({ value, onChange }) {
  return (
    <NumberedCard number={2} title="Exam Type">
      <div role="radiogroup" aria-label="Exam type" className="grid gap-3 sm:grid-cols-2">
        {Object.entries(EXAM_TYPES).map(([type, { label, description }]) => (
          <RadioCard key={type} name="exam-type" value={type} checked={value === type} onChange={onChange} label={label} description={description} />
        ))}
      </div>
    </NumberedCard>
  );
}

/** 3 · Difficulty Level: Easy, Balanced or Difficult. */
export function DifficultyCard({ value, onChange }) {
  return (
    <NumberedCard number={3} title="Difficulty Level">
      <div role="radiogroup" aria-label="Difficulty level" className="grid grid-cols-3 gap-3">
        {DIFFICULTIES.map((level) => (
          <RadioCard key={level} name="difficulty" value={level} checked={value === level} onChange={onChange} label={level} compact />
        ))}
      </div>
    </NumberedCard>
  );
}
