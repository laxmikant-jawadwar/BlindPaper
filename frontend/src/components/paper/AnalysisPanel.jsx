import { AlertTriangle, CheckCircle2, XCircle } from "lucide-react";
import { formatMarks } from "../../lib/format";

const CHECK_ICONS = {
  pass: { icon: CheckCircle2, className: "text-green-600" },
  warn: { icon: AlertTriangle, className: "text-amber-500" },
  fail: { icon: XCircle, className: "text-red-500" },
};

const CHECK_TITLES = {
  structure: "Structure",
  attempt_instructions: "Attempt instructions",
  marks: "Marks",
  question_types: "Question types",
  mcq_format: "MCQ format",
  unit_coverage: "Unit coverage",
  syllabus_relevance: "Syllabus relevance",
  duplicates: "Duplicates",
  formatting: "Formatting",
};

const OVERALL = {
  pass: { label: "All checks passed", box: "border-green-200 bg-green-50 text-green-800" },
  warnings: { label: "Passed with warnings", box: "border-amber-200 bg-amber-50 text-amber-800" },
  fail: { label: "Needs fixing", box: "border-red-200 bg-red-50 text-red-800" },
};

const RELEVANCE = {
  high: { label: "High", className: "bg-green-100 text-green-700" },
  review_required: { label: "Review", className: "bg-amber-100 text-amber-700" },
  low: { label: "Low", className: "bg-red-100 text-red-700" },
};

/**
 * What the system found when it checked the paper: the checks, the marks distribution and how
 * relevant every question is to the syllabus. Shown to the faculty before submitting and to the admin when reviewing.
 */
export default function AnalysisPanel({ analysis }) {
  const overall = OVERALL[analysis.status];
  return (
    <div className="space-y-6">
      <div className={`rounded-lg border px-4 py-3 text-sm font-semibold ${overall.box}`}>{overall.label}</div>

      <Section title="Checks">
        <ul className="space-y-2">
          {analysis.checks.map((check) => {
            const { icon: Icon, className } = CHECK_ICONS[check.status];
            return (
              <li key={check.name} className="flex gap-3 text-sm">
                <Icon className={`mt-0.5 size-5 shrink-0 ${className}`} aria-label={check.status} />
                <span>
                  <span className="font-semibold text-ink">{CHECK_TITLES[check.name] || check.name}: </span>
                  <span className="text-slate-600">{check.message}</span>
                </span>
              </li>
            );
          })}
        </ul>
      </Section>

      <Section title={`Marks distribution (total ${formatMarks(analysis.total_marks)})`}>
        <div className="grid gap-5 md:grid-cols-3">
          <Distribution
            title="By question"
            total={analysis.total_marks}
            rows={analysis.marks_by_group.map((g) => ({
              key: g.group,
              label: `Q${g.group} (attempt ${g.attempt} of ${g.of})`,
              marks: g.marks,
            }))}
          />
          <Distribution
            title="By unit"
            total={analysis.total_marks}
            rows={analysis.marks_by_unit.map((u) => ({ key: u.unit_number, label: `Unit ${u.unit_number}`, hint: u.unit_name, marks: u.marks }))}
          />
          <Distribution
            title="By course outcome"
            total={analysis.total_marks}
            rows={analysis.marks_by_co.map((c) => ({ key: c.co, label: c.co, marks: c.marks }))}
          />
        </div>
      </Section>

      <Section title="Syllabus relevance">
        <ul className="divide-y divide-slate-100 rounded-lg border border-slate-200">
          {analysis.question_relevance.map((item) => {
            const style = RELEVANCE[item.status];
            return (
              <li key={item.sub_question_id} className="flex flex-wrap items-center gap-x-3 gap-y-1 px-3 py-2 text-sm">
                <span className="w-12 font-semibold text-ink">{item.label}</span>
                <span className={`rounded px-2 py-0.5 text-xs font-semibold ${style.className}`}>{style.label}</span>
                <span className="text-xs text-slate-500">{Math.round(item.score * 100)}% of the wording matches the unit</span>
                <span className="flex flex-wrap gap-1">
                  {item.matched_terms.slice(0, 6).map((term) => (
                    <span key={term} className="rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-600">
                      {term}
                    </span>
                  ))}
                </span>
              </li>
            );
          })}
        </ul>
      </Section>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <section>
      <h3 className="mb-2 text-sm font-bold uppercase tracking-wide text-slate-500">{title}</h3>
      {children}
    </section>
  );
}

function Distribution({ title, rows, total }) {
  return (
    <div>
      <h4 className="mb-2 text-sm font-semibold text-ink">{title}</h4>
      <ul className="space-y-2">
        {rows.map((row) => (
          <li key={row.key} title={row.hint}>
            <div className="mb-0.5 flex justify-between text-xs text-slate-600">
              <span>{row.label}</span>
              <span className="font-semibold text-ink">{formatMarks(row.marks)}</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-slate-100">
              <div className="h-full rounded-full bg-brand" style={{ width: `${total ? Math.min(100, (row.marks / total) * 100) : 0}%` }} />
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
