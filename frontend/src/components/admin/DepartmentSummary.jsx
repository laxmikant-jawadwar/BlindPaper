import { Building2 } from "lucide-react";
import { Link } from "react-router-dom";
import EmptyState from "../ui/EmptyState";
import { bodyRow, headRow, table, th } from "./tableStyles";

const pill = "inline-block min-w-[56px] rounded px-3 py-1 text-center text-sm font-medium";
const PILLS = {
  total: `${pill} bg-[#e9f2fe] text-blue-700`,
  pending: `${pill} bg-[#fef3de] text-amber-700`,
  approved: `${pill} bg-[#e6f7ea] text-green-700`,
  rejected: `${pill} bg-[#fde5e6] text-red-600`,
};

/** Papers per department: total, pending, approved and rejected. Follows the dashboard's department filter. */
export default function DepartmentSummary({ rows }) {
  if (rows.length === 0) {
    return <EmptyState icon={Building2} title="No departments to show" />;
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200">
      <table className={`${table} min-w-[440px]`}>
        <thead>
          <tr className={headRow}>
            <th className={`${th} px-2.5`}>Department</th>
            <th className={`${th} px-2.5 text-center`}>Total</th>
            <th className={`${th} px-2.5 text-center`}>Pending</th>
            <th className={`${th} px-2.5 text-center`}>Approved</th>
            <th className={`${th} px-2.5 text-center`}>Rejected</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.department} className={bodyRow}>
              <td className="px-2.5 py-1.5 text-[13px] text-ink">
                <Link to={`/admin/papers?department=${encodeURIComponent(row.department)}`} className="hover:text-brand hover:underline">
                  {row.department}
                </Link>
              </td>
              {["total", "pending", "approved", "rejected"].map((key) => (
                <td key={key} className="px-2.5 py-1.5 text-center">
                  <span className={PILLS[key]}>{row[key]}</span>
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
