import { Search, Users } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";
import { bodyRow, headRow, table, td, tdMuted, th } from "../../components/admin/tableStyles";
import { useLoad } from "../../lib/useLoad";
import Alert from "../../components/ui/Alert";
import Button from "../../components/ui/Button";
import EmptyState from "../../components/ui/EmptyState";
import { inputClasses } from "../../components/ui/FormField";
import PageHeading from "../../components/ui/PageHeading";
import Spinner from "../../components/ui/Spinner";
import { initial } from "../../lib/format";

const count = "inline-block min-w-[40px] rounded px-2.5 py-1 text-center text-sm font-medium";
const COUNTS = [
  { key: "total", label: "Submitted", style: `${count} bg-[#e9f2fe] text-blue-700` },
  { key: "pending", label: "Pending", style: `${count} bg-[#fef3de] text-amber-700` },
  { key: "approved", label: "Approved", style: `${count} bg-[#e6f7ea] text-green-700` },
  { key: "rejected", label: "Rejected", style: `${count} bg-[#fde5e6] text-red-600` },
  { key: "drafts", label: "Drafts", style: `${count} bg-slate-100 text-slate-600` },
];

export default function AdminFaculty() {
  const faculty = useLoad(() => api.admin.faculty(), []);
  const [search, setSearch] = useState("");

  const needle = search.trim().toLowerCase();
  const rows = (faculty.data || []).filter((member) => !needle || member.name.toLowerCase().includes(needle));

  return (
    <div className="mx-auto max-w-[1400px]">
      <PageHeading title="Faculty" subtitle="Registered faculty members and how many papers each has prepared." />

      {faculty.error && (
        <Alert tone="error" title="The faculty list could not be loaded" className="mb-5">
          <p>{faculty.error.message}</p>
          <Button variant="secondary" size="sm" className="mt-2" onClick={faculty.reload}>
            Try again
          </Button>
        </Alert>
      )}

      <div className="mb-4 rounded-xl border border-slate-200 bg-white p-3">
        <div className="relative max-w-md">
          <label className="sr-only" htmlFor="faculty-search">
            Search faculty by name
          </label>
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" aria-hidden="true" />
          <input
            id="faculty-search"
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search faculty by name"
            className={`${inputClasses} pl-9`}
          />
        </div>
      </div>

      <section className="rounded-xl border border-slate-200 bg-white p-3 sm:p-4" aria-live="polite">
        {faculty.loading && !faculty.data ? (
          <div className="py-12 text-center">
            <Spinner label="Loading faculty..." />
          </div>
        ) : rows.length === 0 ? (
          <EmptyState icon={Users} title={needle ? "No faculty member matches that name" : "No faculty have registered yet"}>
            {!needle && "Faculty accounts appear here after they register."}
          </EmptyState>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-slate-200">
            <table className={`${table} min-w-[1000px]`}>
              <thead>
                <tr className={headRow}>
                  <th className={`${th} w-12`}>#</th>
                  <th className={th}>Name</th>
                  <th className={th}>Email</th>
                  <th className={th}>Department</th>
                  <th className={th}>Designation</th>
                  {COUNTS.map((item) => (
                    <th key={item.key} className={`${th} text-center`}>
                      {item.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((member, index) => (
                  <tr key={member.id} className={bodyRow}>
                    <td className={td}>{index + 1}</td>
                    <td className={td}>
                      <span className="flex items-center gap-3">
                        <span className="grid size-9 shrink-0 place-items-center rounded-full bg-tint-blue-strong text-sm font-semibold text-blue-700">
                          {initial(member.name)}
                        </span>
                        <span className="font-medium">{member.name}</span>
                      </span>
                    </td>
                    <td className={tdMuted}>{member.email}</td>
                    <td className={tdMuted}>
                      {member.department ? (
                        <Link to={`/admin/papers?department=${encodeURIComponent(member.department)}`} className="hover:text-brand hover:underline">
                          {member.department}
                        </Link>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className={tdMuted}>{member.designation || "—"}</td>
                    {COUNTS.map((item) => (
                      <td key={item.key} className="px-4 py-3 text-center">
                        <span className={item.style}>{member.papers[item.key]}</span>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {rows.length > 0 && (
          <p className="mt-3 text-sm text-slate-500">
            {rows.length} faculty member{rows.length === 1 ? "" : "s"}.
          </p>
        )}
      </section>
    </div>
  );
}
