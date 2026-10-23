import * as React from "react";
import { cn } from "@/lib/utils";

export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        "flex h-10 w-full min-w-0 rounded-md border border-input bg-background px-3 text-base tabular-nums placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring aria-[invalid=true]:border-danger aria-[invalid=true]:focus-visible:ring-danger sm:text-sm",
        className,
      )}
      {...props}
    />
  ),
);
Input.displayName = "Input";
