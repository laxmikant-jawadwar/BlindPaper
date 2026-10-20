import { ArrowRight, CheckCircle2, FileUp, Loader2 } from "lucide-react";
import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";
import Alert from "../ui/Alert";
import Button from "../ui/Button";
import { buttonClasses } from "../ui/buttonStyles";

const MAX_BYTES = 10 * 1024 * 1024;

/** Problems with the file itself, found before anything is uploaded. */
function fileProblem(file) {
  if (!/\.pdf$/i.test(file.name)) return "Only PDF files (.pdf) are accepted.";
  if (file.size === 0) return "That file is empty.";
  if (file.size > MAX_BYTES) return "That file is larger than the 10 MB limit.";
  return null;
}

/**
 * Workflow step 2: upload the syllabus PDF. The server extracts its text and tables, structures them
 * and stores the result; this component shows what was stored and where to go next.
 */
export default function SyllabusUploader({ onUploaded }) {
  const input = useRef(null);
  const [busy, setBusy] = useState(null); // the name of the file being processed
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState(null);
  const [stored, setStored] = useState(null);

  const upload = async (file) => {
    setError(null);
    setStored(null);
    const problem = fileProblem(file);
    if (problem) {
      setError(problem);
      return;
    }
    setBusy(file.name);
    try {
      const syllabus = await api.syllabus.process(file);
      setStored(syllabus);
      onUploaded?.(syllabus);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(null);
    }
  };

  const choose = (event) => {
    const file = event.target.files?.[0];
    event.target.value = ""; // so choosing the same file again still counts
    if (file) upload(file);
  };

  const drop = (event) => {
    event.preventDefault();
    setDragOver(false);
    const file = event.dataTransfer.files?.[0];
    if (file && !busy) upload(file);
  };

  if (stored) return <StoredSummary syllabus={stored} onAnother={() => setStored(null)} />;

  return (
    <div>
      {error && (
        <Alert tone="error" title="The syllabus could not be uploaded" className="mb-4">
          {error}
        </Alert>
      )}
      <div
        onDragOver={(event) => {
          event.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={drop}
        className={`rounded-xl border-2 border-dashed px-6 py-10 text-center transition-colors ${
          dragOver ? "border-brand bg-blue-50" : "border-slate-300 bg-slate-50/60"
        }`}
      >
        <input ref={input} type="file" accept=".pdf,application/pdf" onChange={choose} className="sr-only" aria-label="Syllabus PDF file" disabled={Boolean(busy)} />
        {busy ? (
          <div role="status" className="flex flex-col items-center gap-3">
            <Loader2 className="size-10 animate-spin text-brand" aria-hidden="true" />
            <p className="font-semibold text-ink">Reading and structuring {busy}…</p>
            <p className="max-w-md text-sm text-slate-500">
              We extract the text and the course-outcome table, find the units and their topics, and save everything to your account. This takes a few seconds.
            </p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <span className="grid size-14 place-items-center rounded-full bg-tint-blue-strong text-brand">
              <FileUp className="size-7" aria-hidden="true" />
            </span>
            <p className="text-lg font-semibold text-ink">Drag and drop your syllabus PDF here</p>
            <p className="text-sm text-slate-500">or choose a file from your computer (PDF, up to 10 MB)</p>
            <Button onClick={() => input.current?.click()} className="mt-1">
              Choose PDF
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}

function StoredSummary({ syllabus, onAnother }) {
  const noUnits = syllabus.course_content.length === 0;
  const rows = [
    ["Course", `${syllabus.subject_name}${syllabus.course_code ? ` (${syllabus.course_code})` : ""}`],
    ["Units found", syllabus.course_content.length],
    ["Course outcomes", syllabus.course_outcomes.length],
    ["Pages", syllabus.page_count],
    ["File", syllabus.filename],
  ];
  return (
    <div>
      {noUnits ? (
        <Alert tone="warning" title="No units were found in this PDF" className="mb-4">
          The text was saved, but a question paper cannot be configured without units. Upload a PDF whose course contents list units such as “Unit 1: …”.
        </Alert>
      ) : (
        <div className="mb-4 flex items-center gap-3 text-green-700">
          <CheckCircle2 className="size-6" aria-hidden="true" />
          <h3 className="text-lg font-bold">Syllabus saved</h3>
        </div>
      )}
      <dl className="divide-y divide-slate-100 rounded-lg border border-slate-200">
        {rows.map(([label, value]) => (
          <div key={label} className="flex justify-between gap-4 px-4 py-2.5 text-sm">
            <dt className="text-slate-500">{label}</dt>
            <dd className="text-right font-medium text-ink">{value}</dd>
          </div>
        ))}
      </dl>
      <div className="mt-5 flex flex-wrap gap-3">
        {!noUnits && (
          <Link to={`/faculty/generate/${syllabus.id}`} className={buttonClasses({ size: "lg" })}>
            Continue to configuration <ArrowRight className="size-5" aria-hidden="true" />
          </Link>
        )}
        <Button variant="secondary" size="lg" onClick={onAnother}>
          Upload a different PDF
        </Button>
      </div>
    </div>
  );
}
