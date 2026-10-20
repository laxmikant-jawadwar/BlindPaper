import { useState } from "react";
import SyllabusLibrary from "../../components/configure/SyllabusLibrary";
import SyllabusUploader from "../../components/configure/SyllabusUploader";
import PageHeading from "../../components/ui/PageHeading";

/** /faculty/generate — workflow step 2: upload the syllabus PDF, or reuse one you uploaded before. */
export default function GeneratePaper() {
  const [uploads, setUploads] = useState(0); // bumps so the list below refreshes after an upload

  return (
    <div className="mx-auto max-w-5xl">
      <PageHeading title="Generate Paper" subtitle="Upload your syllabus PDF, then configure the question paper." />

      <section className="mb-6 rounded-xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
        <div className="mb-4 flex items-center gap-3">
          <span className="grid size-9 place-items-center rounded-full bg-[#cfe5fd] text-[17px] font-bold text-brand">1</span>
          <div>
            <h2 className="text-lg font-bold text-ink">Upload syllabus</h2>
            <p className="text-sm text-slate-500">Next: configure the paper, generate it, then preview and submit it.</p>
          </div>
        </div>
        <SyllabusUploader onUploaded={() => setUploads((n) => n + 1)} />
      </section>

      <SyllabusLibrary refreshKey={uploads} />
    </div>
  );
}
