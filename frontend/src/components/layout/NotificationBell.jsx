import { Bell, CheckCircle2, XCircle } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";
import { formatDate } from "../../lib/format";

const SEEN_KEY = "blindpaper.notifications.seen";

function readSeen() {
  try {
    return localStorage.getItem(SEEN_KEY) || "";
  } catch {
    return "";
  }
}

/** The faculty's bell: the admin's latest decisions on their papers, with a dot for ones not yet seen. */
export default function NotificationBell() {
  const [notes, setNotes] = useState([]);
  const [open, setOpen] = useState(false);
  const [seen, setSeen] = useState(readSeen);
  const box = useRef(null);

  useEffect(() => {
    let cancelled = false;
    api.papers
      .notifications()
      .then((list) => !cancelled && setNotes(list))
      .catch(() => {
        /* the bell is a convenience; a failure should not disturb the page */
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!open) return;
    const close = (event) => !box.current?.contains(event.target) && setOpen(false);
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [open]);

  const latest = notes[0]?.reviewed_at || "";
  const unread = Boolean(latest) && latest > seen;

  const toggle = () => {
    setOpen((wasOpen) => !wasOpen);
    if (latest) {
      try {
        localStorage.setItem(SEEN_KEY, latest);
      } catch {
        /* the dot will simply show again next time */
      }
      setSeen(latest);
    }
  };

  return (
    <div className="relative" ref={box}>
      <button
        type="button"
        onClick={toggle}
        aria-label={unread ? "Notifications (new decisions)" : "Notifications"}
        aria-expanded={open}
        className="relative grid size-11 place-items-center rounded-full text-slate-700 hover:bg-slate-100"
      >
        <Bell className="size-6" aria-hidden="true" />
        {unread && <span className="absolute right-2.5 top-2.5 size-2.5 rounded-full bg-red-500 ring-2 ring-white" />}
      </button>

      {open && (
        <div className="absolute right-0 z-30 mt-2 w-80 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xl">
          <div className="border-b border-slate-100 px-4 py-3 text-sm font-semibold text-ink">Decisions on your papers</div>
          {notes.length === 0 ? (
            <p className="px-4 py-6 text-center text-sm text-slate-500">No decisions yet.</p>
          ) : (
            <ul className="max-h-80 divide-y divide-slate-100 overflow-y-auto">
              {notes.map((note) => (
                <li key={`${note.paper_id}-${note.reviewed_at}`}>
                  <Link
                    to={`/faculty/papers/${note.paper_id}`}
                    onClick={() => setOpen(false)}
                    className="flex gap-3 px-4 py-3 hover:bg-slate-50"
                  >
                    {note.status === "Approved" ? (
                      <CheckCircle2 className="mt-0.5 size-5 shrink-0 text-green-600" aria-hidden="true" />
                    ) : (
                      <XCircle className="mt-0.5 size-5 shrink-0 text-red-500" aria-hidden="true" />
                    )}
                    <span className="min-w-0 text-sm">
                      <span className="block font-medium text-ink">
                        {note.course_name} was {note.status.toLowerCase()}
                      </span>
                      {note.reason && <span className="block truncate text-slate-500">{note.reason}</span>}
                      <span className="block text-xs text-slate-400">{formatDate(note.reviewed_at)}</span>
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
