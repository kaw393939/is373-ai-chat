import { useId } from "react";
import type { InputHTMLAttributes } from "react";

export function FormField({
  label,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & { label: string }) {
  const id = useId();
  return (
    <label htmlFor={id}>
      {label}
      <input id={id} {...props} />
    </label>
  );
}
