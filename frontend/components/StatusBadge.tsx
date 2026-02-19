type Variant = "healthy" | "warning" | "critical";

const styles: Record<Variant, string> = {
  healthy: "bg-emerald-50 text-emerald-700",
  warning: "bg-amber-50 text-amber-700",
  critical: "bg-red-50 text-red-600",
};

interface Props {
  variant: Variant;
  label: string;
}

export default function StatusBadge({ variant, label }: Props) {
  return (
    <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold ${styles[variant]}`}>
      {label}
    </span>
  );
}
