export function SectionLabel({ children, color = "var(--color-accent)" }) {
  return (
    <div className="flex items-center gap-2 mb-3.5">
      <div
        className="w-1 h-[18px] rounded-sm flex-shrink-0"
        style={{ background: color }}
      />
      <span
        className="text-[11px] font-semibold tracking-wider uppercase"
        style={{ color: "var(--color-text-dim)" }}
      >
        {children}
      </span>
    </div>
  );
}
