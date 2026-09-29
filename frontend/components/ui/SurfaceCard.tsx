import * as React from "react"
import { cn } from "@/lib/cn"

export interface SurfaceCardProps extends React.HTMLAttributes<HTMLDivElement> {
  hoverable?: boolean
}

const SurfaceCard = React.forwardRef<HTMLDivElement, SurfaceCardProps>(
  ({ className, hoverable, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "bg-surface border border-border rounded-xl p-6",
          hoverable && "cursor-pointer transition-colors hover:border-[#444] active:bg-[#111]",
          className
        )}
        {...props}
      />
    )
  }
)
SurfaceCard.displayName = "SurfaceCard"

export { SurfaceCard }
