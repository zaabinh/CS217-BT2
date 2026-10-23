import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva("inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium [&_svg]:size-3", {
  variants: {
    tone: {
      neutral: "border-border bg-muted text-muted-foreground",
      info: "border-primary/20 bg-primary/10 text-primary",
      success: "border-success/25 bg-success/10 text-success",
      warning: "border-warning/30 bg-warning/10 text-warning",
      danger: "border-danger/25 bg-danger/10 text-danger",
    },
  },
  defaultVariants: { tone: "neutral" },
});

export function Badge({ className, tone, ...props }: React.HTMLAttributes<HTMLSpanElement> & VariantProps<typeof badgeVariants>) {
  return <span className={cn(badgeVariants({ tone }), className)} {...props} />;
}
