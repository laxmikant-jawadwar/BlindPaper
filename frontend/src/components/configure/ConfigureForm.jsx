import { ArrowRight, Loader2, Zap } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../../api/client";
import { DEFAULT_CO_CODES, totalMarks, validateConfiguration } from "../../lib/paperRules";
import { QUESTION_TYPES } from "../../lib/constants";
import Alert from "../ui/Alert";
import Button from "../ui/Button";
import Modal from "../ui/Modal";
import { DifficultyCard, ExamTypeCard } from "./ChoiceCards";
import CourseDetailsCard from "./CourseDetailsCard";
import QuestionTypesCard from "./QuestionTypesCard";
import StepIndicator from "./StepIndicator";
import TemplateEditor from "./TemplateEditor";
import UnitSelectionCard from "./UnitSelectionCard";
import { defaultTemplate, defaultUnitsFor, reassignUnit, unitsUsedBy } from "./template";

function buildInitialForm(syllabus, coCodes) {
  const unitNumbers = syllabus.course_content.map((unit) => unit.unit_number);
  return {
    courseName: syllabus.subject_name,
    courseCode: syllabus.course_code || "",
    year: "Third Year",
    semester: "Semester 5",
    examType: "MSE",
    difficulty: "Balanced",
    questionTypes: QUESTION_TYPES.map((type) => type.value),
    selectedUnits: defaultUnitsFor("MSE", unitNumbers),
    unitsTouched: false, // once the faculty picks units by hand, switching exam type no longer changes them
    // the two templates are kept apart, so editing one never changes the other
    templates: {
      MSE: defaultTemplate("MSE", coCodes, unitNumbers),
      ESE: defaultTemplate("ESE", coCodes, unitNumbers),
    },
  };
}

/** The request the backend expects: only the ACTIVE exam type's template is sent. */
function buildConfig(form, syllabusId) {
  return {
    syllabus_id: syllabusId,
    course_name: form.courseName.trim(),
    course_code: form.courseCode.trim(),
    year: form.year,
    semester: form.semester,
    exam_type: form.examType,
    difficulty: form.difficulty,
    question_types: QUESTION_TYPES.map((type) => type.value).filter((value) => form.questionTypes.includes(value)),
    selected_units: [...form.selectedUnits].sort((a, b) => a - b),
    groups: form.templates[form.examType].map((group) => ({
      id: group.id,
      instruction: group.instruction.trim(),
      sub_questions: group.subQuestions.map((sub) => ({
        id: sub.id,
        description: sub.description.trim(),
        co: sub.co,
        marks: Number(sub.marks),
        unit_number: sub.unitNumber,
      })),
    })),
  };
}

const FAILURE_TITLES = {
  404: "The syllabus is no longer available",
  422: "The configuration needs changes",
  429: "The AI service is busy",
  502: "The paper could not be generated",
  503: "The paper could not be generated",
};

/** The Configure Question Paper form for one stored syllabus (workflow step 3), and the Generate action (step 4). */
export default function ConfigureForm({ syllabus }) {
  const navigate = useNavigate();
  const units = syllabus.course_content;
  const allUnitNumbers = useMemo(() => units.map((unit) => unit.unit_number), [units]);
  const coCodes = useMemo(
    () => (syllabus.course_outcomes.length ? syllabus.course_outcomes.map((outcome) => outcome.code) : DEFAULT_CO_CODES),
    [syllabus],
  );

  const [initial] = useState(() => buildInitialForm(syllabus, coCodes));
  const [initialJson] = useState(() => JSON.stringify(initial));
  const [form, setForm] = useState(initial);
  const [showErrors, setShowErrors] = useState(false);
  const [attempts, setAttempts] = useState(0);
  const [generating, setGenerating] = useState(false);
  const [failure, setFailure] = useState(null);
  const [confirmCancel, setConfirmCancel] = useState(false);
  const messageBox = useRef(null);

  const activeGroups = form.templates[form.examType];
  const validation = useMemo(
    () => validateConfiguration({ ...form, groups: activeGroups, coCodes }),
    [form, activeGroups, coCodes],
  );
  const total = useMemo(() => totalMarks(activeGroups), [activeGroups]);
  const dirty = JSON.stringify(form) !== initialJson;
  const shownErrors = showErrors ? validation : { fields: {}, groups: {}, messages: [], valid: true };
  const selectedUnits = useMemo(() => [...form.selectedUnits].sort((a, b) => a - b), [form.selectedUnits]);
  const questionCount = activeGroups.reduce((sum, group) => sum + group.subQuestions.length, 0);

  useEffect(() => {
    if (attempts || failure) messageBox.current?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [attempts, failure]);

  const setField = (field, value) => setForm((current) => ({ ...current, [field]: value }));
  const setGroups = (change) =>
    setForm((current) => ({
      ...current,
      templates: { ...current.templates, [current.examType]: change(current.templates[current.examType]) },
    }));

  const toggleType = (type) =>
    setForm((current) => ({
      ...current,
      questionTypes: current.questionTypes.includes(type)
        ? current.questionTypes.filter((t) => t !== type)
        : [...current.questionTypes, type],
    }));

  // MSE starts with the first half of the units and ESE with all of them, until the faculty chooses units by hand
  const changeExamType = (examType) =>
    setForm((current) => {
      if (current.unitsTouched) return { ...current, examType };
      const wanted = new Set([...defaultUnitsFor(examType, allUnitNumbers), ...unitsUsedBy(current.templates[examType])]);
      return { ...current, examType, selectedUnits: allUnitNumbers.filter((n) => wanted.has(n)) };
    });

  const toggleUnit = (unitNumber) =>
    setForm((current) => {
      if (!current.selectedUnits.includes(unitNumber)) {
        return { ...current, unitsTouched: true, selectedUnits: [...current.selectedUnits, unitNumber] };
      }
      const remaining = current.selectedUnits.filter((n) => n !== unitNumber);
      if (!remaining.length) return { ...current, unitsTouched: true, selectedUnits: remaining };
      // sub-questions that used the deselected unit move to a unit that is still selected
      const first = [...remaining].sort((a, b) => a - b)[0];
      return {
        ...current,
        unitsTouched: true,
        selectedUnits: remaining,
        templates: {
          MSE: reassignUnit(current.templates.MSE, unitNumber, first),
          ESE: reassignUnit(current.templates.ESE, unitNumber, first),
        },
      };
    });

  const generate = async () => {
    setShowErrors(true);
    setFailure(null);
    if (!validation.valid) {
      setAttempts((count) => count + 1);
      return;
    }
    setGenerating(true);
    try {
      const paper = await api.papers.generate(buildConfig(form, syllabus.id));
      navigate(`/faculty/papers/${paper.id}?new=1`);
    } catch (err) {
      setFailure(err);
      setGenerating(false);
    }
  };

  const cancel = () => (dirty ? setConfirmCancel(true) : navigate("/faculty/generate"));

  return (
    <div className="lg:-mx-4 lg:-mt-2">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-4">
        <div className="border-l-4 border-brand pl-3">
          <h1 className="text-[29.5px] font-bold leading-[1.15] tracking-tight text-ink">Configure Question Paper</h1>
          <p className="text-[17.5px] leading-[1.4] text-slate-500">Set examination details, select template and define question distribution.</p>
        </div>
        <StepIndicator current={generating ? 2 : 1} />
      </div>

      <div className="relative">
        <div inert={generating} aria-busy={generating} className={generating ? "opacity-40 transition-opacity" : "transition-opacity"}>
          <div className="grid items-start gap-3.5 lg:grid-cols-[528fr_690fr]">
            <div className="min-w-0 space-y-3">
              <CourseDetailsCard values={form} errors={shownErrors.fields} onChange={setField} />
              <ExamTypeCard value={form.examType} onChange={changeExamType} />
              <DifficultyCard value={form.difficulty} onChange={(value) => setField("difficulty", value)} />
              <QuestionTypesCard selected={form.questionTypes} onToggle={toggleType} error={shownErrors.fields.questionTypes} />
              <UnitSelectionCard units={units} selected={form.selectedUnits} onToggle={toggleUnit} error={shownErrors.fields.units} />
            </div>

            <TemplateEditor
              examType={form.examType}
              onExamTypeChange={changeExamType}
              groups={activeGroups}
              onGroupsChange={setGroups}
              coCodes={coCodes}
              unitNumbers={selectedUnits}
              errors={shownErrors.groups}
              total={total}
            />
          </div>

          <div ref={messageBox} className="mt-4 space-y-3">
            {showErrors && !validation.valid && (
              <Alert tone="warning" title="Please fix the following before generating:">
                <ul className="mt-1 list-disc space-y-0.5 pl-5">
                  {validation.messages.slice(0, 8).map((message) => (
                    <li key={message}>{message}</li>
                  ))}
                  {validation.messages.length > 8 && <li>…and {validation.messages.length - 8} more.</li>}
                </ul>
              </Alert>
            )}
            {failure && (
              <Alert tone="error" title={FAILURE_TITLES[failure.status] || "Something went wrong"}>
                <p>{failure.message}</p>
                {failure.problems.length > 0 && (
                  <ul className="mt-1 list-disc space-y-0.5 pl-5">
                    {failure.problems.map((problem) => (
                      <li key={problem}>{problem}</li>
                    ))}
                  </ul>
                )}
              </Alert>
            )}
          </div>

          <div className="mt-4 flex flex-wrap items-center justify-end gap-3">
            <Button variant="secondary" size="lg" onClick={cancel} className="min-w-[96px]">
              Cancel
            </Button>
            <Button size="lg" onClick={generate}>
              <Zap className="size-5" aria-hidden="true" /> Generate Question Paper <ArrowRight className="size-5" aria-hidden="true" />
            </Button>
          </div>
        </div>

        {generating && (
          <div className="absolute inset-0 z-10" role="status" aria-live="polite">
            <div className="sticky top-32 mx-auto mt-24 w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-2xl">
              <Loader2 className="mx-auto size-10 animate-spin text-brand" aria-hidden="true" />
              <h2 className="mt-4 text-xl font-bold text-ink">Generating your question paper…</h2>
              <p className="mt-2 text-sm text-slate-500">
                Writing {questionCount} question{questionCount === 1 ? "" : "s"} from {selectedUnits.length} unit{selectedUnits.length === 1 ? "" : "s"} of{" "}
                {form.courseName.trim() || "your syllabus"}, then checking them against your template. This usually takes 5 to 15 seconds.
              </p>
            </div>
          </div>
        )}
      </div>

      <Modal
        open={confirmCancel}
        onClose={() => setConfirmCancel(false)}
        title="Discard this configuration?"
        size="md"
        footer={
          <>
            <Button variant="secondary" onClick={() => setConfirmCancel(false)}>
              Keep editing
            </Button>
            <Button variant="danger" onClick={() => navigate("/faculty/generate")}>
              Discard
            </Button>
          </>
        }
      >
        <p className="text-sm text-slate-600">You have changed the configuration. If you leave now, those changes are lost.</p>
      </Modal>
    </div>
  );
}
