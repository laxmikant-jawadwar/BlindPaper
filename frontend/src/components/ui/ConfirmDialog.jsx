import Alert from "./Alert";
import Button from "./Button";
import Modal from "./Modal";

/** "Are you sure?" for actions that cannot be undone. `error` shows a failure from the last attempt. */
export default function ConfirmDialog({
  open,
  title,
  children,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  tone = "primary",
  busy = false,
  error = null,
  onConfirm,
  onCancel,
}) {
  return (
    <Modal
      open={open}
      onClose={busy ? undefined : onCancel}
      size="md"
      title={title}
      footer={
        <>
          <Button variant="secondary" onClick={onCancel} disabled={busy}>
            {cancelLabel}
          </Button>
          <Button variant={tone} onClick={onConfirm} loading={busy}>
            {confirmLabel}
          </Button>
        </>
      }
    >
      <div className="space-y-4 text-slate-600">
        {children}
        {error && <Alert tone="error">{error}</Alert>}
      </div>
    </Modal>
  );
}
