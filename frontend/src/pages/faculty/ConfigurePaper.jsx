import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../../api/client";
import ConfigureForm from "../../components/configure/ConfigureForm";
import Alert from "../../components/ui/Alert";
import { buttonClasses } from "../../components/ui/buttonStyles";
import Spinner from "../../components/ui/Spinner";

/** /faculty/generate/:syllabusId — loads the stored syllabus, then shows the Configure form. */
export default function ConfigurePaper() {
  const { syllabusId } = useParams();
  const [loaded, setLoaded] = useState(null); // { id, syllabus } or { id, error }

  useEffect(() => {
    let cancelled = false;
    api.syllabus
      .get(syllabusId)
      .then((syllabus) => !cancelled && setLoaded({ id: syllabusId, syllabus }))
      .catch((error) => !cancelled && setLoaded({ id: syllabusId, error }));
    return () => {
      cancelled = true;
    };
  }, [syllabusId]);

  const current = loaded?.id === syllabusId ? loaded : null;

  if (!current) {
    return (
      <div className="grid place-items-center py-24">
        <Spinner label="Loading your syllabus..." />
      </div>
    );
  }

  if (current.error) {
    const missing = current.error.status === 404;
    return (
      <div className="mx-auto max-w-xl py-12">
        <Alert tone={missing ? "warning" : "error"} title={missing ? "We couldn't find that syllabus" : "Could not load the syllabus"}>
          {missing ? "It may have been deleted, or it belongs to another account. Upload it again or pick one of your syllabi." : current.error.message}
        </Alert>
        <Link to="/faculty/generate" className={buttonClasses({ className: "mt-5" })}>
          Back to Generate Paper
        </Link>
      </div>
    );
  }

  if (current.syllabus.course_content.length === 0) {
    return (
      <div className="mx-auto max-w-xl py-12">
        <Alert tone="warning" title="This syllabus has no units">
          No unit headings were found in {current.syllabus.filename}, so a paper cannot be configured from it. Upload a PDF whose course contents list
          units such as “Unit 1: …”.
        </Alert>
        <Link to="/faculty/generate" className={buttonClasses({ className: "mt-5" })}>
          Back to Generate Paper
        </Link>
      </div>
    );
  }

  return <ConfigureForm key={current.id} syllabus={current.syllabus} />;
}
