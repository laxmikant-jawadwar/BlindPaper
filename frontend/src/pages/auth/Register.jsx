import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { homeFor, useAuth } from "../../auth/authContext";
import AuthLayout from "../../components/layout/AuthLayout";
import Alert from "../../components/ui/Alert";
import Button from "../../components/ui/Button";
import FormField from "../../components/ui/FormField";
import { DEPARTMENTS } from "../../lib/constants";

const EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

function validate(form) {
  const errors = {};
  if (!form.name.trim()) errors.name = "Enter your name.";
  if (!EMAIL.test(form.email.trim())) errors.email = "Enter a valid email address.";
  if (form.password.length < 6) errors.password = "Use at least 6 characters.";
  if (form.confirm !== form.password) errors.confirm = "The passwords do not match.";
  return errors;
}

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: "",
    email: "",
    department: DEPARTMENTS[0],
    designation: "",
    password: "",
    confirm: "",
  });
  const [errors, setErrors] = useState({});
  const [serverError, setServerError] = useState(null);
  const [busy, setBusy] = useState(false);

  const set = (field) => (event) => setForm((current) => ({ ...current, [field]: event.target.value }));

  const submit = async (event) => {
    event.preventDefault();
    const found = validate(form);
    setErrors(found);
    if (Object.keys(found).length) return;

    setServerError(null);
    setBusy(true);
    try {
      const user = await register({
        name: form.name,
        email: form.email,
        password: form.password,
        department: form.department,
        designation: form.designation.trim() || null,
      });
      navigate(homeFor(user), { replace: true });
    } catch (err) {
      setServerError(err.message);
      setBusy(false);
    }
  };

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Join BlindPaper and generate question papers from your syllabus."
      footer={
        <>
          Already have an account?{" "}
          <Link to="/login" className="font-semibold text-brand hover:underline">
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={submit} className="space-y-4" noValidate>
        {serverError && <Alert tone="error">{serverError}</Alert>}
        <FormField label="Full name" placeholder="Prof. Priya Sharma" autoComplete="name" value={form.name} onChange={set("name")} error={errors.name} />
        <FormField
          label="Email address"
          type="email"
          placeholder="you@college.edu"
          autoComplete="email"
          value={form.email}
          onChange={set("email")}
          error={errors.email}
        />
        <div className="grid gap-4 sm:grid-cols-2">
          <FormField label="Department" options={DEPARTMENTS} value={form.department} onChange={set("department")} />
          <FormField label="Designation (optional)" placeholder="Assistant Professor" value={form.designation} onChange={set("designation")} />
        </div>
        <FormField
          label="Password"
          type="password"
          autoComplete="new-password"
          placeholder="At least 6 characters"
          value={form.password}
          onChange={set("password")}
          error={errors.password}
        />
        <FormField
          label="Confirm password"
          type="password"
          autoComplete="new-password"
          value={form.confirm}
          onChange={set("confirm")}
          error={errors.confirm}
        />
        <Button type="submit" size="lg" loading={busy} className="w-full">
          Create account
        </Button>
      </form>
    </AuthLayout>
  );
}
