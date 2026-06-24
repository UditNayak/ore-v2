interface Props {
  label: string;
  children: React.ReactNode;
}

/** A small labeled section used to align content across the V1/V2 columns. */
export default function Section({ label, children }: Props) {
  return (
    <div>
      <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">
        {label}
      </h4>
      <div className="text-sm text-slate-800">{children}</div>
    </div>
  );
}
