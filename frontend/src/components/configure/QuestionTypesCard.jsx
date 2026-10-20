import { QUESTION_TYPES } from "../../lib/constants";
import { NumberedCard } from "./fields";

/** 4 · Question Types: any combination of MCQ, Descriptive and Numericals. */
export default function QuestionTypesCard({ selected, onToggle, error }) {
  return (
    <NumberedCard number={4} title="Question Types">
      <fieldset>
        <legend className="sr-only">Question types</legend>
        <div className="flex flex-wrap gap-x-3 gap-y-2.5">
          {QUESTION_TYPES.map(({ value, label }) => (
            <label key={value} className="flex cursor-pointer items-center gap-1.5 whitespace-nowrap text-[11.5px] text-ink">
              <input
                type="checkbox"
                checked={selected.includes(value)}
                onChange={() => onToggle(value)}
                className="size-[18px] rounded accent-blue-600"
              />
              {label}
            </label>
          ))}
        </div>
      </fieldset>
      {error && <p className="mt-2 text-xs text-red-600">{error}</p>}
    </NumberedCard>
  );
}
