import { Save } from "lucide-react";
import { useState } from "react";
import { useAuth } from "../../auth/authContext";
import Alert from "../../components/ui/Alert";
import Button from "../../components/ui/Button";
import FormField from "../../components/ui/FormField";
import PageHeading from "../../components/ui/PageHeading";
import { DEPARTMENTS } from "../../lib/constants";
import { formatDate, initial } from "../../lib/format";

export default function Profile() {
  const { user, updateProfile } = useAuth();
  const [form, setForm] = useState({
    name: user.name,
    department: user.department || DEPARTMENTS[0],
    designation: user.designation || "",
    phone: user.phone || "",
  });
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState(null);
  const [busy, setBusy] = useState(false);

  const set = (field) => (event) => {
    setMessage(null);
    setForm((current) => ({ ...current, [field]: event.target.value }));
  };

  const changed =
    form.name.trim() !== user.name ||
    form.department !== user.department ||
    form.designation.trim() !== (user.designation || "") ||
    form.phone.trim() !== (user.phone || "");

  const submit = async (event) => {
    event.preventDefault();
    if (!form.name.trim()) {
      setErrors({ name: "Enter your name." });
      return;
    }
    setErrors({});
    setBusy(true);
    try {
      await updateProfile({
        name: form.name.trim(),
        department: form.department,
        designation: form.designation.trim() || null,
        phone: form.phone.trim() || null,
      });
      setMessage({ tone: "success", text: "Your profile was saved." });
    } catch (err) {
      setMessage({ tone: "error", text: err.message });
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <PageHeading title="Profile" subtitle="Your details are saved with every paper you submit." />

      <div className="grid max-w-5xl gap-6 lg:grid-cols-[280px_minmax(0,1fr)]">
        <section className="flex flex-col items-center rounded-xl border border-slate-100 bg-white p-6 text-center shadow-sm">
          <span className="grid size-24 place-items-center rounded-full bg-brand text-4xl font-semibold text-white">{initial(user.name)}</span>
          <h2 className="mt-4 text-xl font-bold text-ink">{user.name}</h2>
          <p className="text-sm text-slate-500">{user.designation || "Faculty"}</p>
          <p className="text-sm text-slate-500">{user.department} Department</p>
          <p className="mt-4 border-t border-slate-100 pt-4 text-xs text-slate-400">Member since {formatDate(user.created_at)}</p>
        </section>

        <form onSubmit={submit} className="rounded-xl border border-slate-100 bg-white p-6 shadow-sm" noValidate>
          <h2 className="mb-5 text-lg font-bold text-ink">Personal details</h2>
          <div className="space-y-4">
            {message && <Alert tone={message.tone}>{message.text}</Alert>}
            <FormField label="Full name" value={form.name} onChange={set("name")} error={errors.name} autoComplete="name" />
            <FormField label="Email address" value={user.email} disabled hint="Your email is your login and cannot be changed." />
            <div className="grid gap-4 sm:grid-cols-2">
              <FormField label="Department" options={DEPARTMENTS} value={form.department} onChange={set("department")} />
              <FormField label="Designation" placeholder="Assistant Professor" value={form.designation} onChange={set("designation")} />
            </div>
            <FormField label="Phone" type="tel" placeholder="Optional" value={form.phone} onChange={set("phone")} autoComplete="tel" />
          </div>
          <div className="mt-6 flex justify-end">
            <Button type="submit" size="lg" loading={busy} disabled={!changed}>
              <Save className="size-4" aria-hidden="true" /> Save changes
            </Button>
          </div>
        </form>
      </div>
    </>
  );
}
