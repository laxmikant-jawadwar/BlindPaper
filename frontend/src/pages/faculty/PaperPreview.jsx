import { ArrowLeft, Check, Download, RefreshCw, Save, Send, Trash2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { api, saveBlob } from "../../api/client";
import AnalysisPanel from "../../components/paper/AnalysisPanel";
import PaperDocument from "../../components/paper/PaperDocument";
import Alert from "../../components/ui/Alert";
import Button from "../../components/ui/Button";
import ConfirmDialog from "../../components/ui/ConfirmDialog";
import PageHeading from "../../components/ui/PageHeading";
import Spinner from "../../components/ui/Spinner";
import StatusBadge from "../../components/ui/StatusBadge";
import { EXAM_TYPES } from "../../lib/constants";
import { formatDate, formatDateTime, subLabel } from "../../lib/format";
import { useLoad } from "../../lib/useLoad";

const STEPS = ["Configure", "Generate", "Preview"];

function Stepper() {
  return (
    <ol className="flex items-center gap-2 text-sm" aria-label="Progress">
      {STEPS.map((step, index) => {
        const current = index === STEPS.length - 1;
        return (
          <li key={step} className="flex items-center gap-2" aria-current={current ? "step" : undefined}>
            <span
              className={`grid size-7 place-items-center rounded-full text-xs font-bold ${current ? "bg-brand text-white" : "bg-green-600 text-white"}`}
            >
              {current ? index + 1 : <Check className="size-4" aria-hidden="true" />}
            </span>
            <span className={current ? "font-semibold text-ink" : "text-slate-500"}>{step}</span>
            {!current && <span className="mx-1 h-px w-6 bg-slate-300" aria-hidden="true" />}
          </li>
        );
      })}
    </ol>
  );
}

const sameValue = (a, b) => JSON.stringify(a) === JSON.stringify(b);

export default function PaperPreview() {
  const { paperId } = useParams();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const justGenerated = params.get("new") === "1";

  const { data: loaded, loading, error } = useLoad(() => api.papers.get(paperId), paperId);
  const [saved, setSaved] = useState(null); // the newest copy from the server after a save or regenerate
  const [edits, setEdits] = useState({}); // unsaved corrections: sub_question_id -> changed fields
  const [dialog, setDialog] = useState(null); // "regenerate" | "submit" | "delete"
  const [busy, setBusy] = useState(false);
  const [dialogError, setDialogError] = useState(null);
  const [notice, setNotice] = useState(null);
  const [rewriting, setRewriting] = useState(null); // the sub-question being written again right now
  const [askRewrite, setAskRewrite] = useState(null); // a sub-question waiting for "replace my edits?" confirmation
  const noticeBox = useRef(null);

  // an error should be seen even when the faculty is far down the page; a success is visible in the question itself
  useEffect(() => {
    if (notice?.tone === "error") noticeBox.current?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [notice]);

  const base = saved?.id === paperId ? saved : loaded;
  if (error) {
    return (
      <>
        <BackLink />
        <Alert tone="error" title="Could not open this paper">
          {error.message}
        </Alert>
      </>
    );
  }
  if (!base) {
    return (
      <>
        <BackLink />
        {loading && <Spinner label="Opening the paper..." />}
      </>
    );
  }

  const editable = base.status === "Draft" || base.status === "Rejected";
  const questions = base.questions.map((q) => ({ ...q, ...edits[q.sub_question_id] }));
  const paper = { ...base, questions };
  const dirty = Object.keys(edits).length > 0;
  const failing = base.analysis.checks.filter((c) => c.status === "fail");
  const blocked = !dirty && failing.length > 0;

  const edit = (id, patch) => {
    const original = base.questions.find((q) => q.sub_question_id === id);
    setEdits((current) => {
      const merged = { ...current[id], ...patch };
      const unchanged = Object.keys(merged).every((key) => sameValue(merged[key], original[key]));
      const next = { ...current };
      if (unchanged) delete next[id];
      else next[id] = merged;
      return next;
    });
  };

  const editPayload = () =>
    Object.entries(edits).map(([id, patch]) => {
      const merged = { ...base.questions.find((q) => q.sub_question_id === id), ...patch };
      return { sub_question_id: id, question_text: merged.question_text, options: merged.options, answer: merged.answer };
    });

  const accept = (updated, text) => {
    setSaved(updated);
    setEdits({});
    setNotice({ tone: "success", text });
  };

  const closeDialog = () => {
    setDialog(null);
    setDialogError(null);
  };

  const run = async (action) => {
    setBusy(true);
    setDialogError(null);
    setNotice(null);
    try {
      await action();
    } catch (err) {
      if (dialog) setDialogError(err.message);
      else setNotice({ tone: "error", text: err.message });
    } finally {
      setBusy(false);
    }
  };

  const save = () =>
    run(async () => accept(await api.papers.update(base.id, editPayload()), "Your changes were saved and the paper was checked again."));

  const regenerate = () =>
    run(async () => {
      accept(await api.papers.regenerate(base.id), "The questions were written again.");
      closeDialog();
    });

  const submit = () =>
    run(async () => {
      if (dirty) await api.papers.update(base.id, editPayload());
      const submitted = await api.papers.submit(base.id);
      accept(submitted, "Submitted. The Exam Cell will review it.");
      closeDialog();
    });

  const remove = () =>
    run(async () => {
      await api.papers.remove(base.id);
      navigate("/faculty/papers", { replace: true });
    });

  const download = () => run(async () => saveBlob(await api.papers.pdf(base.id)));

  /** "Q1b)" for a sub-question id, as the faculty sees it */
  const labelOf = (subQuestionId) => {
    for (const [g, group] of base.groups.entries()) {
      const s = group.sub_questions.findIndex((sub) => sub.id === subQuestionId);
      if (s >= 0) return `Q${g + 1}${subLabel(s)}`;
    }
    return "The question";
  };

  // Write one question again. Only that question changes; the faculty's other unsaved corrections stay.
  const rewrite = async (subQuestionId) => {
    setAskRewrite(null);
    setRewriting(subQuestionId);
    setNotice(null);
    try {
      const updated = await api.papers.regenerateQuestion(base.id, subQuestionId);
      setSaved(updated);
      setEdits((current) => {
        const next = { ...current };
        delete next[subQuestionId]; // the replaced version's hand edits are gone with it
        return next;
      });
      setNotice({ tone: "success", text: `${labelOf(subQuestionId)} was written again. Your other questions were not touched.` });
    } catch (err) {
      setNotice({ tone: "error", text: err.message });
    } finally {
      setRewriting(null);
    }
  };

  const requestRewrite = (subQuestionId) => (edits[subQuestionId] ? setAskRewrite(subQuestionId) : rewrite(subQuestionId));

  return (
    <>
      <BackLink />
      <PageHeading
        title={base.course_name}
        subtitle={`${base.course_code} · ${EXAM_TYPES[base.exam_type].description} · ${base.year}, ${base.semester}`}
        actions={<StatusBadge status={base.status} className="text-base" />}
      />

      {justGenerated && base.status === "Draft" && (
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-100 bg-white px-5 py-3">
          <Stepper />
          <span className="text-sm text-slate-500">Your paper is ready. It stays a draft until you submit it.</span>
        </div>
      )}

      <div className="mb-5 space-y-3" ref={noticeBox}>
        {notice && <Alert tone={notice.tone}>{notice.text}</Alert>}
        {base.status === "Draft" && (
          <Alert tone="info">Read the questions and correct anything you need. When you are happy, submit the paper for admin approval.</Alert>
        )}
        {base.status === "Rejected" && (
          <Alert tone="error" title="The admin sent this paper back">
            <p>{base.rejection_reason}</p>
            <p className="mt-1 text-red-700/80">Make the corrections below (or regenerate the questions) and submit it again.</p>
          </Alert>
        )}
        {base.status === "Pending Approval" && (
          <Alert tone="warning">
            Submitted on {formatDate(base.submitted_at)}. It is waiting for the Exam Cell to decide, so it cannot be edited meanwhile.
          </Alert>
        )}
        {base.status === "Approved" && (
          <Alert tone="success">Approved on {formatDate(base.reviewed_at)}. You can download the final question paper.</Alert>
        )}
      </div>

      <div className="mb-5 flex flex-wrap items-center gap-3 rounded-xl border border-slate-100 bg-white p-4 shadow-sm">
        {editable && (
          <>
            <Button variant="secondary" onClick={save} disabled={!dirty || dialog !== null || rewriting !== null} loading={busy && !dialog && dirty}>
              <Save className="size-4" aria-hidden="true" /> Save changes
            </Button>
            <Button variant="secondary" onClick={() => setDialog("regenerate")} disabled={rewriting !== null}>
              <RefreshCw className="size-4" aria-hidden="true" /> Regenerate all
            </Button>
            <Button
              onClick={() => setDialog("submit")}
              disabled={blocked || rewriting !== null}
              title={blocked ? "Fix the failing checks first" : undefined}
            >
              <Send className="size-4" aria-hidden="true" /> {dirty ? "Save and submit for approval" : "Submit for approval"}
            </Button>
            <Button variant="ghost" className="ml-auto text-red-600 hover:bg-red-50" disabled={rewriting !== null} onClick={() => setDialog("delete")}>
              <Trash2 className="size-4" aria-hidden="true" /> Delete
            </Button>
          </>
        )}
        {base.status === "Approved" && (
          <Button onClick={download} loading={busy}>
            <Download className="size-4" aria-hidden="true" /> Download PDF
          </Button>
        )}
        {dirty && <span className="text-sm text-amber-600">You have unsaved changes.</span>}
        {blocked && <span className="text-sm text-red-600">Cannot submit yet: {failing.map((c) => c.message).join(" ")}</span>}
        {!editable && base.status !== "Approved" && <span className="text-sm text-slate-500">This paper is read-only.</span>}
      </div>

      <div className="grid items-start gap-6 xl:grid-cols-[minmax(0,1fr)_380px]">
        <PaperDocument
          paper={paper}
          editable={editable}
          showAnswers
          onChange={edit}
          onRegenerate={requestRewrite}
          regeneratingId={rewriting}
          disabled={busy}
        />

        <aside className="space-y-5 xl:sticky xl:top-24">
          <section className="rounded-xl border border-slate-100 bg-white p-5 shadow-sm">
            <h2 className="mb-3 text-lg font-bold text-ink">Paper summary</h2>
            <dl className="space-y-2 text-sm">
              <Row label="Total marks" value={base.total_marks} />
              <Row label="Difficulty" value={base.difficulty} />
              <Row label="Question types" value={base.question_types.join(", ")} />
              <Row label="Units" value={base.selected_units.map((n) => `Unit ${n}`).join(", ")} />
              <Row label="Generated" value={formatDateTime(base.generation?.generated_at)} />
              <Row label="Written by" value={base.generation?.model || "—"} />
            </dl>
          </section>

          <section className="rounded-xl border border-slate-100 bg-white p-5 shadow-sm">
            <h2 className="mb-3 text-lg font-bold text-ink">Checks</h2>
            {dirty && <p className="mb-3 text-xs text-amber-600">These checks are for the saved paper. Save your changes to refresh them.</p>}
            <AnalysisPanel analysis={base.analysis} />
          </section>
        </aside>
      </div>

      <ConfirmDialog
        open={askRewrite !== null}
        title={`Replace your changes to ${askRewrite ? labelOf(askRewrite) : "this question"}?`}
        confirmLabel="Write a new question"
        onConfirm={() => rewrite(askRewrite)}
        onCancel={() => setAskRewrite(null)}
      >
        <p>
          You have changed this question by hand. A new question will replace it, and your changes to it will be lost. Your other
          questions and corrections stay as they are.
        </p>
      </ConfirmDialog>

      <ConfirmDialog
        open={dialog === "regenerate"}
        title="Write the questions again?"
        confirmLabel="Regenerate"
        busy={busy}
        error={dialogError}
        onConfirm={regenerate}
        onCancel={closeDialog}
      >
        <p>
          The AI will write a fresh set of questions for the same configuration.
          {dirty ? " Your unsaved corrections will be lost." : " The current questions will be replaced."}
        </p>
      </ConfirmDialog>

      <ConfirmDialog
        open={dialog === "submit"}
        title="Submit for approval?"
        confirmLabel={dirty ? "Save and submit" : "Submit"}
        busy={busy}
        error={dialogError}
        onConfirm={submit}
        onCancel={closeDialog}
      >
        <p>
          The paper goes to the Exam Cell for review and its status becomes <strong>Pending Approval</strong>. You will not be able to edit it
          until it is decided.
        </p>
        {base.analysis.status === "warnings" && (
          <Alert tone="warning">The checks have warnings. You can still submit, but the reviewer will see them.</Alert>
        )}
      </ConfirmDialog>

      <ConfirmDialog
        open={dialog === "delete"}
        title="Delete this paper?"
        confirmLabel="Delete paper"
        tone="danger"
        busy={busy}
        error={dialogError}
        onConfirm={remove}
        onCancel={closeDialog}
      >
        <p>
          <strong className="text-ink">{base.course_name}</strong> will be deleted for good. This cannot be undone.
        </p>
      </ConfirmDialog>
    </>
  );
}

function BackLink() {
  return (
    <Link to="/faculty/papers" className="mb-4 inline-flex items-center gap-1.5 text-sm font-semibold text-brand hover:underline">
      <ArrowLeft className="size-4" aria-hidden="true" /> My Papers
    </Link>
  );
}

function Row({ label, value }) {
  return (
    <div className="flex justify-between gap-4">
      <dt className="text-slate-500">{label}</dt>
      <dd className="text-right font-medium text-ink">{value}</dd>
    </div>
  );
}
