import { SEMESTERS, YEARS } from "../../lib/constants";
import { NumberedCard, SelectField, TextField } from "./fields";

const asOptions = (values) => values.map((value) => ({ value, label: value }));

/** 1 · Course Details: prefilled from the stored syllabus, editable for this paper only. */
export default function CourseDetailsCard({ values, errors, onChange }) {
  return (
    <NumberedCard number={1} title="Course Details">
      <p className="sr-only">Fetched from the uploaded syllabus. Changes here apply to this paper only and never change the stored syllabus.</p>
      <div className="grid gap-x-4 gap-y-3 sm:grid-cols-2">
        <TextField label="Course Name" value={values.courseName} onChange={(e) => onChange("courseName", e.target.value)} error={errors.courseName} />
        <TextField label="Course Code" value={values.courseCode} onChange={(e) => onChange("courseCode", e.target.value)} error={errors.courseCode} />
        <SelectField label="Year" options={asOptions(YEARS)} value={values.year} onChange={(e) => onChange("year", e.target.value)} error={errors.year} />
        <SelectField
          label="Semester"
          options={asOptions(SEMESTERS)}
          value={values.semester}
          onChange={(e) => onChange("semester", e.target.value)}
          error={errors.semester}
        />
      </div>
    </NumberedCard>
  );
}
