import { BookOpen, FileCheck2, ShieldCheck, Sparkles } from "lucide-react";
import BrandLogo from "./BrandLogo";

const POINTS = [
  { icon: Sparkles, text: "Question papers written from your own syllabus by AI" },
  { icon: FileCheck2, text: "Checked for marks, structure and syllabus relevance" },
  { icon: ShieldCheck, text: "Reviewed and approved by the Exam Cell before use" },
];

/** The frame of the sign-in and registration pages: a dark brand panel beside the form. */
export default function AuthLayout({ title, subtitle, children, footer }) {
  return (
    <div className="grid min-h-screen bg-canvas lg:grid-cols-[minmax(380px,5fr)_7fr]">
      <aside className="hidden flex-col justify-between bg-sidebar p-10 text-white lg:flex">
        <BrandLogo />
        <div>
          <h2 className="text-4xl font-bold leading-tight">
            Syllabus-based question papers,
            <br />
            ready in minutes.
          </h2>
          <ul className="mt-8 space-y-4">
            {POINTS.map(({ icon: Icon, text }) => (
              <li key={text} className="flex items-center gap-3 text-slate-200">
                <span className="grid size-10 shrink-0 place-items-center rounded-lg bg-white/10">
                  <Icon className="size-5" aria-hidden="true" />
                </span>
                {text}
              </li>
            ))}
          </ul>
        </div>
        <p className="text-sm text-slate-400">© {new Date().getFullYear()} BlindPaper</p>
      </aside>

      <main className="flex items-center justify-center px-5 py-10">
        <div className="w-full max-w-md">
          <div className="mb-8 flex items-center gap-2 text-brand lg:hidden">
            <BookOpen className="size-7" aria-hidden="true" />
            <span className="text-xl font-bold text-ink">BlindPaper</span>
          </div>
          <h1 className="text-3xl font-bold text-ink">{title}</h1>
          <p className="mt-1 text-slate-500">{subtitle}</p>
          <div className="mt-7 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">{children}</div>
          {footer && <p className="mt-5 text-center text-sm text-slate-600">{footer}</p>}
        </div>
      </main>
    </div>
  );
}
