/** The big page title with its subtitle, and optional actions on the right. */
export default function PageHeading({ title, subtitle, actions, accent = false }) {
  return (
    <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
      <div className={accent ? "border-l-4 border-brand pl-3" : ""}>
        <h1 className="text-3xl font-bold tracking-tight text-ink sm:text-[34px]">{title}</h1>
        {subtitle && <p className="mt-1 text-lg text-slate-500">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-3">{actions}</div>}
    </div>
  );
}
