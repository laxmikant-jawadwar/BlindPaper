import { BookOpen } from "lucide-react";

export default function BrandLogo() {
  return (
    <div className="flex items-center gap-3">
      <span className="grid size-11 place-items-center rounded-xl bg-sky-400/15 text-sky-400">
        <BookOpen className="size-8" strokeWidth={2.2} aria-hidden="true" />
      </span>
      <div className="leading-tight">
        <div className="text-2xl font-bold tracking-tight text-white">BlindPaper</div>
        <div className="text-[13px] text-slate-300">AI for Question Papers</div>
      </div>
    </div>
  );
}
