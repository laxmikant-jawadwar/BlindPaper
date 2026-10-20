/** What a table or list shows when there is nothing in it yet. */
export default function EmptyState({ icon: Icon, title, children }) {
  return (
    <div className="flex flex-col items-center px-6 py-12 text-center">
      {Icon && (
        <span className="mb-3 grid size-14 place-items-center rounded-full bg-slate-100 text-slate-400">
          <Icon className="size-7" aria-hidden="true" />
        </span>
      )}
      <h3 className="text-base font-semibold text-slate-800">{title}</h3>
      {children && <p className="mt-1 max-w-md text-sm text-slate-500">{children}</p>}
    </div>
  );
}
