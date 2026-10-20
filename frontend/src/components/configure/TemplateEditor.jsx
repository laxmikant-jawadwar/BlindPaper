import { GripVertical, Plus, Trash2, X } from "lucide-react";
import { useState } from "react";
import { EXAM_TYPES } from "../../lib/constants";
import { formatMarks, subLabel } from "../../lib/format";
import { NumberedCard, Select } from "./fields";
import {
  addSubQuestion,
  moveSubQuestion,
  newGroup,
  removeGroup,
  removeSubQuestion,
  updateGroup,
  updateSubQuestion,
} from "./template";

// handle | label | description | CO | marks | unit | remove (from `sm` up; on a phone the row is stacked)
const COLUMNS = "sm:grid-cols-[18px_22px_minmax(0,1fr)_88px_68px_108px_24px] sm:gap-1.5";
const ROW = `flex flex-col gap-2 sm:grid sm:items-center ${COLUMNS}`;
const HEADER_ROW = `hidden sm:grid sm:items-center ${COLUMNS}`;

const TAB_LABELS = {
  MSE: "MSE Template (Mid Semester)",
  ESE: "ESE Template (End Semester)",
};

const inputBase =
  "h-9 w-full rounded border bg-white px-3 text-[14px] text-ink placeholder:text-slate-400 " +
  "focus:border-brand focus:outline-2 focus:outline-brand/25";

/**
 * 6 · Examination Template: the MSE / ESE tabs and the editable question groups.
 * `groups` belongs to the active exam type; `onGroupsChange` takes a function (groups) => groups.
 */
export default function TemplateEditor({
  examType,
  onExamTypeChange,
  groups,
  onGroupsChange,
  coCodes,
  unitNumbers,
  errors,
  total,
}) {
  const fallback = { co: coCodes[0], unitNumber: unitNumbers[0] };

  return (
    <NumberedCard
      className="min-w-0"
      number={6}
      title="Examination Template"
      subtitle="Configure the structure of the question paper using the selected template."
      aside={
        <span className="shrink-0 rounded-full bg-tint-blue px-3 py-1 text-sm font-semibold text-blue-800" aria-live="polite">
          Total marks: {formatMarks(total)}
        </span>
      }
    >
      <div role="tablist" aria-label="Examination template" className="mb-3.5 grid grid-cols-2 gap-1">
        {Object.keys(EXAM_TYPES).map((type) => (
          <button
            key={type}
            type="button"
            role="tab"
            id={`tab-${type}`}
            aria-selected={examType === type}
            aria-controls="template-panel"
            onClick={() => onExamTypeChange(type)}
            className={`min-h-[42px] rounded-sm px-2 py-1.5 text-[13px] font-semibold transition-colors sm:text-[15px] ${
              examType === type ? "bg-[#0761fe] text-white" : "bg-[#dfe7f3] text-ink hover:bg-[#d3ddee]"
            }`}
          >
            {TAB_LABELS[type]}
          </button>
        ))}
      </div>

      <div id="template-panel" role="tabpanel" aria-labelledby={`tab-${examType}`} className="space-y-3.5">
        {groups.length === 0 && (
          <p className="rounded-md border border-dashed border-slate-300 px-4 py-6 text-center text-sm text-slate-500">
            This template has no question groups. Add one below.
          </p>
        )}

        {groups.map((group, index) => (
          <GroupEditor
            key={group.id}
            group={group}
            number={index + 1}
            coCodes={coCodes}
            unitNumbers={unitNumbers}
            errors={errors[group.id]}
            onInstruction={(instruction) => onGroupsChange((all) => updateGroup(all, group.id, { instruction }))}
            onRemoveGroup={() => onGroupsChange((all) => removeGroup(all, group.id))}
            onAddSub={() => onGroupsChange((all) => addSubQuestion(all, group.id, fallback))}
            onRemoveSub={(subId) => onGroupsChange((all) => removeSubQuestion(all, group.id, subId))}
            onChangeSub={(subId, patch) => onGroupsChange((all) => updateSubQuestion(all, group.id, subId, patch))}
            onMoveSub={(fromId, toId) => onGroupsChange((all) => moveSubQuestion(all, group.id, fromId, toId))}
          />
        ))}

        <button
          type="button"
          onClick={() => onGroupsChange((all) => [...all, newGroup(all.length, coCodes, unitNumbers)])}
          className="flex h-[52px] w-full items-center justify-center gap-2 rounded-md border border-dashed border-[#abcefe] bg-[#f7fbff] text-[15px] font-semibold text-brand hover:bg-[#eef5ff]"
        >
          <Plus className="size-5" aria-hidden="true" /> Add Question Group
        </button>
      </div>
    </NumberedCard>
  );
}

function GroupEditor({ group, number, coCodes, unitNumbers, errors, onInstruction, onRemoveGroup, onAddSub, onRemoveSub, onChangeSub, onMoveSub }) {
  const [dragging, setDragging] = useState(null); // id of the sub-question being dragged
  const [dropTarget, setDropTarget] = useState(null);
  const only = group.subQuestions.length === 1;

  return (
    <section aria-label={`Question Group ${number}`} className="overflow-hidden rounded-md border border-slate-200 bg-white">
      <div className="flex flex-wrap items-stretch border-b border-slate-200 bg-[#f6f8fc] sm:flex-nowrap">
        <h3 className="flex w-full shrink-0 items-center border-b border-slate-200 px-3.5 py-2 text-[15px] font-semibold text-ink sm:w-auto sm:border-b-0 sm:border-r">Question Group {number}</h3>
        <input
          value={group.instruction}
          onChange={(event) => onInstruction(event.target.value)}
          aria-label={`Attempt instruction for question group ${number}`}
          aria-invalid={Boolean(errors?.instruction)}
          placeholder="Attempt any two"
          className={`min-w-0 flex-1 bg-transparent px-3.5 py-2 text-[15px] font-semibold sm:py-0 text-ink placeholder:font-normal placeholder:text-slate-400 focus:bg-white focus:outline-2 focus:-outline-offset-2 focus:outline-brand/40 ${
            errors?.instruction ? "text-red-700" : ""
          }`}
        />
        <button
          type="button"
          onClick={onRemoveGroup}
          aria-label={`Delete question group ${number}`}
          className="grid w-12 shrink-0 place-items-center border-l border-slate-200 text-red-500 hover:bg-red-50"
        >
          <Trash2 className="size-[18px]" aria-hidden="true" />
        </button>
      </div>
      {(errors?.instruction || errors?.empty) && <p className="border-b border-slate-100 bg-red-50 px-3.5 py-1.5 text-xs text-red-700">{errors.instruction || errors.empty}</p>}

      <div className="px-3 pb-3 pt-2.5">
        <div className={`${HEADER_ROW} pb-1.5 text-[12px] font-bold text-ink`} aria-hidden="true">
          <span>#</span>
          <span />
          <span>Sub-question</span>
          <span>CO</span>
          <span>Marks</span>
          <span>Unit</span>
          <span />
        </div>

        <ul className="space-y-2.5">
          {group.subQuestions.map((sub, index) => {
            const problems = errors?.subs?.[sub.id];
            const label = `${number}${subLabel(index)}`;
            const unitOptions = unitNumbers.includes(sub.unitNumber)
              ? unitNumbers.map((n) => ({ value: n, label: `Unit ${n}` }))
              : [...unitNumbers, sub.unitNumber].map((n) => ({ value: n, label: unitNumbers.includes(n) ? `Unit ${n}` : `Unit ${n} (not selected)` }));
            return (
              <li
                key={sub.id}
                onDragOver={(event) => {
                  if (!dragging) return;
                  event.preventDefault();
                  setDropTarget(sub.id);
                }}
                onDrop={(event) => {
                  event.preventDefault();
                  const from = dragging;
                  setDragging(null);
                  setDropTarget(null);
                  if (from) onMoveSub(from, sub.id);
                }}
                className={`rounded ${dropTarget === sub.id && dragging ? "bg-blue-50 outline-2 outline-dashed outline-brand/50" : ""}`}
              >
                <div className={ROW}>
                  <span
                    draggable
                    onDragStart={(event) => {
                      setDragging(sub.id);
                      event.dataTransfer.effectAllowed = "move";
                      event.dataTransfer.setData("text/plain", sub.id);
                    }}
                    onDragEnd={() => {
                      setDragging(null);
                      setDropTarget(null);
                    }}
                    title="Drag to reorder"
                    className="hidden cursor-grab text-slate-400 active:cursor-grabbing sm:block"
                  >
                    <GripVertical className="size-[18px]" aria-hidden="true" />
                  </span>

                  <div className="flex items-center gap-1.5 sm:contents">
                    <span className="w-[22px] shrink-0 text-[15px] font-bold text-ink">{subLabel(index)}</span>
                    <input
                      value={sub.description}
                      onChange={(event) => onChangeSub(sub.id, { description: event.target.value })}
                      placeholder="Enter sub-question (optional)"
                      aria-label={`Question ${label} description (optional)`}
                      maxLength={300}
                      className={`${inputBase} min-w-0 flex-1 border-slate-300 sm:flex-none`}
                    />
                    <button
                      type="button"
                      onClick={() => onRemoveSub(sub.id)}
                      disabled={only}
                      title={only ? "A group needs at least one sub-question" : `Remove ${subLabel(index)}`}
                      aria-label={`Remove sub-question ${label}`}
                      className="grid size-[24px] shrink-0 place-items-center rounded text-slate-400 hover:bg-slate-100 hover:text-red-600 disabled:opacity-30 disabled:hover:bg-transparent disabled:hover:text-slate-400 sm:order-last"
                    >
                      <X className="size-4" aria-hidden="true" />
                    </button>
                  </div>

                  <div className="grid grid-cols-3 gap-1.5 pl-7 sm:contents">
                    <div>
                      <span className="mb-0.5 block text-[11px] font-medium text-slate-500 sm:hidden">CO</span>
                      <Select
                        aria-label={`Question ${label} course outcome`}
                        value={sub.co}
                        invalid={Boolean(problems?.co)}
                        onChange={(event) => onChangeSub(sub.id, { co: event.target.value })}
                        options={(coCodes.includes(sub.co) ? coCodes : [sub.co, ...coCodes]).map((code) => ({ value: code, label: code || "Select" }))}
                      />
                    </div>
                    <div>
                      <span className="mb-0.5 block text-[11px] font-medium text-slate-500 sm:hidden">Marks</span>
                      <input
                        type="number"
                        inputMode="decimal"
                        min="0"
                        max="100"
                        step="any"
                        value={sub.marks}
                        onChange={(event) => onChangeSub(sub.id, { marks: event.target.value })}
                        aria-label={`Question ${label} marks`}
                        aria-invalid={Boolean(problems?.marks)}
                        className={`${inputBase} ${problems?.marks ? "border-red-400" : "border-slate-300"}`}
                      />
                    </div>
                    <div>
                      <span className="mb-0.5 block text-[11px] font-medium text-slate-500 sm:hidden">Unit</span>
                      <Select
                        aria-label={`Question ${label} unit`}
                        value={sub.unitNumber}
                        invalid={Boolean(problems?.unit)}
                        onChange={(event) => onChangeSub(sub.id, { unitNumber: Number(event.target.value) })}
                        options={unitOptions}
                      />
                    </div>
                  </div>
                </div>
                {problems && <p className="mt-1 pl-7 text-xs text-red-600 sm:pl-10">{Object.values(problems).join(" ")}</p>}
              </li>
            );
          })}
        </ul>

        <button
          type="button"
          onClick={onAddSub}
          className="mt-3 inline-flex h-8 items-center gap-1.5 rounded-md border border-brand bg-white px-3 text-[13px] font-semibold text-brand hover:bg-blue-50"
        >
          <Plus className="size-4" aria-hidden="true" /> Add Sub-question
        </button>
      </div>
    </section>
  );
}
