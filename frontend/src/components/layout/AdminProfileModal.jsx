import Modal from "../ui/Modal";
import Button from "../ui/Button";
import { formatDate, initial } from "../../lib/format";

/** The administrator's details (there is nothing for an admin to edit, so this is read-only). */
export default function AdminProfileModal({ open, onClose, user }) {
  const rows = [
    ["Name", user.name],
    ["Email", user.email],
    ["Role", "Administrator"],
    ["Designation", user.designation || "Exam Cell Authority"],
    ["Account created", formatDate(user.created_at)],
  ];
  return (
    <Modal open={open} onClose={onClose} title="My Profile" size="md" footer={<Button variant="secondary" onClick={onClose}>Close</Button>}>
      <div className="mb-5 flex items-center gap-4">
        <span className="grid size-16 place-items-center rounded-full bg-brand text-2xl font-semibold text-white">{initial(user.name)}</span>
        <div>
          <div className="text-lg font-semibold text-ink">{user.name}</div>
          <div className="text-sm text-slate-500">Exam Cell Authority</div>
        </div>
      </div>
      <dl className="divide-y divide-slate-100 rounded-xl border border-slate-200">
        {rows.map(([label, value]) => (
          <div key={label} className="flex justify-between gap-4 px-4 py-3 text-sm">
            <dt className="text-slate-500">{label}</dt>
            <dd className="text-right font-medium text-ink">{value}</dd>
          </div>
        ))}
      </dl>
    </Modal>
  );
}
