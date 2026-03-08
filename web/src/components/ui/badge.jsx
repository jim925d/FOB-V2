import * as React from "react"
import { cva } from "class-variance-authority";

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider transition-colors",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary text-primary-foreground",
        secondary: "border-transparent bg-secondary text-secondary-foreground",
        outline: "text-foreground",
        destructive: "border-transparent bg-destructive text-destructive-foreground",
        certification: "border-fob-info/30 bg-fob-info/15 text-fob-info",
        education: "border-fob-purple/30 bg-fob-purple/15 text-fob-purple",
        skillbridge: "border-fob-copper/30 bg-fob-copper/15 text-fob-copper",
        entry_role: "border-fob-orange/30 bg-fob-orange/15 text-fob-orange",
        mid_role: "border-fob-warn/30 bg-fob-warn/15 text-fob-warn",
        target_role: "border-fob-accent/30 bg-fob-accent/15 text-fob-accent",
        stretch_role: "border-fob-accent/30 bg-fob-accent/10 text-fob-accent/80",
        origin: "border-fob-accent/30 bg-fob-accent/15 text-fob-accent",
      },
    },
    defaultVariants: { variant: "default" },
  }
)

function Badge({
  className,
  variant,
  ...props
}) {
  return (<div className={cn(badgeVariants({ variant }), className)} {...props} />);
}

// eslint-disable-next-line react-refresh/only-export-components -- badgeVariants used by consumers
export { Badge, badgeVariants }
