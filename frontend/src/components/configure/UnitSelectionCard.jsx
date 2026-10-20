import { NumberedCard } from "./fields";

/** 5 · Unit Selection: the units of the stored syllabus; only the ticked ones can be used in the paper. */
export default function UnitSelectionCard({ units, selected, onToggle, error }) {
  return (
    <NumberedCard number={5} title="Unit Selection">
      <fieldset>
        <legend className="sr-only">Select the syllabus units to be covered in this question paper.</legend>
        <ul className="divide-y divide-slate-100 overflow-hidden rounded-md border border-slate-200">
          {units.map((unit) => (
            <li key={unit.unit_number}>
              <label className="flex cursor-pointer items-center gap-3 px-3 py-[5px] text-[13.5px] text-ink hover:bg-slate-50">
                <input
                  type="checkbox"
                  checked={selected.includes(unit.unit_number)}
                  onChange={() => onToggle(unit.unit_number)}
                  className="size-5 shrink-0 rounded accent-blue-600"
                />
                <span>
                  Unit {unit.unit_number} – {unit.unit_name}
                </span>
              </label>
            </li>
          ))}
        </ul>
      </fieldset>
      {error && <p className="mt-2 text-xs text-red-600">{error}</p>}
    </NumberedCard>
  );
}
