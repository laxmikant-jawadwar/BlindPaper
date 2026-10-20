import { DEPARTMENTS } from "../../lib/constants";

/**
 * "Filter by Department": All Departments plus one chip per department. `value` is "" for all.
 * Used on the dashboard, where choosing a chip narrows the numbers and every table at once.
 */
export default function DepartmentFilter({ value, onChange }) {
  const chips = [{ label: "All Departments", value: "" }, ...DEPARTMENTS.map((name) => ({ label: name, value: name }))];
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-3 rounded-xl border border-slate-200 bg-white px-5 py-2.5">
      <span id="department-filter-label" className="text-lg font-semibold text-ink">
        Filter by Department
      </span>
      <div role="group" aria-labelledby="department-filter-label" className="flex flex-wrap gap-2.5">
        {chips.map((chip) => {
          const active = chip.value === value;
          return (
            <button
              key={chip.label}
              type="button"
              aria-pressed={active}
              onClick={() => onChange(chip.value)}
              className={`h-9 rounded-md px-4 text-[15px] transition-colors ${
                active ? "bg-brand font-medium text-white shadow-sm" : "bg-slate-100 text-slate-700 hover:bg-slate-200"
              }`}
            >
              {chip.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
