/**
 * Reusable hero section. Props: eyebrow, title (string, supports HTML via dangerouslySetInnerHTML),
 * subtitle, compact (boolean), children
 */
export default function PageHero({
  eyebrow,
  title,
  subtitle,
  compact = false,
  children,
}) {
  return (
    <section
      className="border-b"
      style={{
        background: "linear-gradient(to bottom, var(--color-bg-secondary), var(--color-bg-primary))",
        borderColor: "var(--color-border)",
      }}
    >
      <div
        className={`max-w-[1200px] mx-auto px-7 ${compact ? "py-8" : "py-12"}`}
      >
        {eyebrow && (
          <div className="flex items-center gap-2 mb-3">
            <div
              className="w-[22px] h-0.5 rounded-full flex-shrink-0"
              style={{ background: "var(--color-accent)" }}
            />
            <span className="text-xs uppercase tracking-widest" style={{ color: "var(--color-accent)" }}>
              {eyebrow}
            </span>
          </div>
        )}
        {title && (
          <h1
            className={`font-serif max-w-3xl ${compact ? "text-2xl" : "text-4xl"} [&_em]:not-italic [&_em]:text-fob-accent`}
            style={{ color: "var(--color-text-primary)" }}
            dangerouslySetInnerHTML={typeof title === "string" ? { __html: title } : undefined}
          >
            {typeof title !== "string" ? title : null}
          </h1>
        )}
        {subtitle && (
          <p className="text-sm text-[--color-text-muted] max-w-xl mt-2">
            {subtitle}
          </p>
        )}
        {children && <div className="mt-4">{children}</div>}
      </div>
    </section>
  );
}
