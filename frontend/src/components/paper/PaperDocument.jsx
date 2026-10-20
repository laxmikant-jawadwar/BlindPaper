import { Check, RefreshCw } from "lucide-react";
import { EXAM_TYPES } from "../../lib/constants";
import { formatMarks, subLabel } from "../../lib/format";

const TYPE_STYLES = {
  MCQ: "bg-violet-50 text-violet-700",
  Descriptive: "bg-sky-50 text-sky-700",
  Numerical: "bg-amber-50 text-amber-700",
};

const fieldClasses =
  "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-ink focus:border-brand focus:outline-2 focus:outline-brand/30";

/**
 * A question paper laid out like the printed sheet.
 *  - editable: the faculty can correct the questions in place (onChange(subQuestionId, patch))
 *  - onRegenerate(subQuestionId): shows a button on each question to have just that one written again;
 *    regeneratingId is the question being written right now
 *  - showAnswers: mark the correct MCQ option (for the faculty and the reviewer; never printed)
 */
export default function PaperDocument({ paper, editable = false, showAnswers = false, onChange, onRegenerate, regeneratingId = null, disabled = false }) {
  const questions = Object.fromEntries(paper.questions.map((q) => [q.sub_question_id, q]));
  const groupMarks = paper.analysis?.marks_by_group || [];

  return (
    <article className="mx-auto w-full max-w-4xl rounded-xl border border-slate-200 bg-white px-5 py-7 shadow-sm sm:px-10">
      <header className="border-b-2 border-ink pb-4 text-center">
        <p className="text-sm font-bold tracking-widest text-ink">{EXAM_TYPES[paper.exam_type].description.toUpperCase()}</p>
        <h2 className="mt-1 text-xl font-bold text-blue-900">
          {paper.course_name} <span className="font-semibold">({paper.course_code})</span>
        </h2>
        <p className="mt-0.5 text-sm text-slate-500">
          {paper.year} &nbsp;|&nbsp; {paper.semester}
        </p>
        <p className="mt-3 text-left text-sm font-bold text-ink">Maximum Marks: {formatMarks(paper.total_marks)}</p>
      </header>

      <div className="mt-5 space-y-6">
        {paper.groups.map((group, groupIndex) => (
          <section key={group.id} aria-label={`Question ${groupIndex + 1}`}>
            <div className="flex items-center justify-between gap-3 rounded-md bg-slate-100 px-3 py-2">
              <h3 className="text-sm font-bold text-ink">
                Q.{groupIndex + 1} &nbsp; {group.instruction}
              </h3>
              <span className="text-sm font-bold text-blue-900">[{formatMarks(groupMarks[groupIndex]?.marks ?? 0)} Marks]</span>
            </div>

            <ol className="divide-y divide-slate-100">
              {group.sub_questions.map((spec, subIndex) => {
                const question = questions[spec.id];
                const rewriting = regeneratingId === spec.id;
                return (
                  <li key={spec.id} className="flex gap-3 py-4" aria-busy={rewriting}>
                    <span className="w-6 shrink-0 text-sm font-bold text-ink">{subLabel(subIndex)}</span>
                    <div className="min-w-0 flex-1">
                      {!question ? (
                        <p className="text-sm italic text-red-600">No question was written for this part.</p>
                      ) : editable ? (
                        <EditableQuestion question={question} locked={rewriting || disabled} onChange={(patch) => onChange?.(spec.id, patch)} />
                      ) : (
                        <ReadOnlyQuestion question={question} showAnswers={showAnswers} />
                      )}
                      <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                        {question && (
                          <span className={`rounded px-2 py-0.5 font-medium ${TYPE_STYLES[question.question_type]}`}>{question.question_type}</span>
                        )}
                        <span className="rounded bg-slate-100 px-2 py-0.5 font-medium">{spec.co}</span>
                        <span className="rounded bg-slate-100 px-2 py-0.5 font-medium">Unit {spec.unit_number}</span>
                        {editable && question && onRegenerate && (
                          <button
                            type="button"
                            onClick={() => onRegenerate(spec.id)}
                            disabled={disabled || regeneratingId !== null}
                            aria-label={`Regenerate question ${groupIndex + 1}${subLabel(subIndex)}`}
                            className="ml-auto inline-flex items-center gap-1.5 rounded-md border border-slate-200 bg-white px-2.5 py-1 font-semibold text-slate-600 transition-colors hover:border-brand hover:text-brand disabled:opacity-50 disabled:hover:border-slate-200 disabled:hover:text-slate-600"
                          >
                            <RefreshCw className={`size-3.5 ${rewriting ? "animate-spin" : ""}`} aria-hidden="true" />
                            {rewriting ? "Writing a new question…" : "Regenerate this question"}
                          </button>
                        )}
                      </div>
                    </div>
                    <span className="shrink-0 text-sm font-bold text-ink">[{formatMarks(spec.marks)}]</span>
                  </li>
                );
              })}
            </ol>
          </section>
        ))}
      </div>

      <p className="mt-6 border-t border-slate-200 pt-3 text-center text-xs font-bold tracking-wide text-slate-400">— END OF QUESTION PAPER —</p>
    </article>
  );
}

function ReadOnlyQuestion({ question, showAnswers }) {
  return (
    <>
      <p className="whitespace-pre-line text-[15px] leading-relaxed text-ink">{question.question_text}</p>
      {question.question_type === "MCQ" && (
        <ul className="mt-2 space-y-1 pl-1">
          {question.options.map((option, index) => {
            const letter = "ABCD"[index];
            const correct = showAnswers && question.answer === letter;
            return (
              <li key={letter} className={`flex items-start gap-2 text-sm ${correct ? "font-semibold text-green-700" : "text-slate-700"}`}>
                <span className="w-5 shrink-0">{letter})</span>
                <span className="flex-1">{option}</span>
                {correct && <Check className="mt-0.5 size-4 shrink-0" aria-label="Correct answer" />}
              </li>
            );
          })}
        </ul>
      )}
    </>
  );
}

function EditableQuestion({ question, onChange, locked = false }) {
  const isMcq = question.question_type === "MCQ";
  const setOption = (index, value) => onChange({ options: question.options.map((o, i) => (i === index ? value : o)) });

  return (
    <div className={`space-y-2 transition-opacity ${locked ? "opacity-50" : ""}`}>
      <textarea
        disabled={locked}
        value={question.question_text}
        onChange={(event) => onChange({ question_text: event.target.value })}
        rows={Math.max(2, Math.ceil(question.question_text.length / 90))}
        aria-label="Question text"
        className={`${fieldClasses} resize-y leading-relaxed`}
      />
      {isMcq && (
        <fieldset className="space-y-1.5">
          <legend className="mb-1 text-xs font-medium text-slate-500">Options (select the correct one)</legend>
          {question.options.map((option, index) => {
            const letter = "ABCD"[index];
            return (
              <div key={letter} className="flex items-center gap-2">
                <input
                  type="radio"
                  disabled={locked}
                  name={`answer-${question.sub_question_id}`}
                  checked={question.answer === letter}
                  onChange={() => onChange({ answer: letter })}
                  aria-label={`Option ${letter} is correct`}
                  className="size-4 accent-brand"
                />
                <span className="w-5 text-sm font-medium text-slate-600">{letter})</span>
                <input
                  disabled={locked}
                  value={option}
                  onChange={(event) => setOption(index, event.target.value)}
                  aria-label={`Option ${letter}`}
                  className={fieldClasses}
                />
              </div>
            );
          })}
        </fieldset>
      )}
    </div>
  );
}
