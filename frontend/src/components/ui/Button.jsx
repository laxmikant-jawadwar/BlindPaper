import { Loader2 } from "lucide-react";
import { buttonClasses } from "./buttonStyles";

/** A button with the BlindPaper look. `loading` shows a spinner and blocks further clicks. */
export default function Button({
  variant = "primary",
  size = "md",
  loading = false,
  disabled = false,
  className = "",
  type = "button",
  children,
  ...props
}) {
  return (
    <button
      type={type}
      disabled={disabled || loading}
      className={buttonClasses({ variant, size, className })}
      {...props}
    >
      {loading && <Loader2 className="size-4 animate-spin" aria-hidden="true" />}
      {children}
    </button>
  );
}
