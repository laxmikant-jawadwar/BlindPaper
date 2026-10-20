import { ArrowRight, Building2, Users } from "lucide-react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";
import { useLoad } from "../../lib/useLoad";
import Alert from "../../components/ui/Alert";
import Button from "../../components/ui/Button";
import PageHeading from "../../components/ui/PageHeading";
import Spinner from "../../components/ui/Spinner";

const FIGURES = [
  { key: "total", label: "Total", style: "bg-[#e9f2fe] text-blue-700" },
  { key: "pending", label: "Pending", style: "bg-[#fef3de] text-amber-700" },
  { key: "approved", label: "Approved", style: "bg-[#e6f7ea] text-green-700" },
  { key: "rejected", label: "Rejected", style: "bg-[#fde5e6] text-red-600" },
];

export default function AdminDepartments() {
  const departments = useLoad(() => api.admin.departments(), []);

  return (
    <div className="mx-auto max-w-[1400px]">
      <PageHeading title="Departments" subtitle="Faculty and papers in each department. Choose one to see its papers." />

      {departments.error && (
        <Alert tone="error" title="The departments could not be loaded" className="mb-5">
          <p>{departments.error.message}</p>
          <Button variant="secondary" size="sm" className="mt-2" onClick={departments.reload}>
            Try again
          </Button>
        </Alert>
      )}

      {departments.loading && !departments.data ? (
        <div className="py-12 text-center">
          <Spinner label="Loading departments..." />
        </div>
      ) : (
        <ul className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {(departments.data || []).map((department) => (
            <li key={department.department}>
              <Link
                to={`/admin/papers?department=${encodeURIComponent(department.department)}`}
                className="group block rounded-xl border border-slate-200 bg-white p-5 shadow-[0_1px_2px_rgba(15,27,51,0.04)] transition-shadow hover:border-blue-200 hover:shadow-md"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <span className="grid size-11 place-items-center rounded-full bg-tint-blue-strong text-blue-600">
                      <Building2 className="size-5" aria-hidden="true" />
                    </span>
                    <div>
                      <h2 className="text-lg font-semibold text-ink">{department.department}</h2>
                      <p className="flex items-center gap-1.5 text-sm text-slate-500">
                        <Users className="size-4" aria-hidden="true" />
                        {department.faculty_count} faculty member{department.faculty_count === 1 ? "" : "s"}
                      </p>
                    </div>
                  </div>
                  <ArrowRight className="mt-1 size-5 text-slate-300 transition-colors group-hover:text-brand" aria-hidden="true" />
                </div>

                <dl className="mt-5 grid grid-cols-4 gap-2 text-center">
                  {FIGURES.map((figure) => (
                    <div key={figure.key} className={`rounded-lg px-1 py-2.5 ${figure.style}`}>
                      <dd className="text-xl font-bold">{department[figure.key]}</dd>
                      <dt className="text-xs font-medium">{figure.label}</dt>
                    </div>
                  ))}
                </dl>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
