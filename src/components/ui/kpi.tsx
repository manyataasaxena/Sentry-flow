import * as React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface KpiProps extends React.HTMLAttributes<HTMLDivElement> {
  label: string;
  value: string;
  trend: string;
  icon: React.ElementType;
  color: string;
}

export const Kpi = React.forwardRef<HTMLDivElement, KpiProps>(
  function Kpi({ label, value, trend, icon: Icon, color, className, ...props }, ref) {
    return (
      <Card
        ref={ref}
        className={cn("hover:border-indigo-500/30 transition-colors", className)}
        {...props}
      >
        <CardContent className="pt-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-muted-foreground">{label}</p>
              <p className="text-2xl font-bold mt-1">{value}</p>
            </div>
            <div className={cn("p-2 rounded-lg bg-muted", color)}>
              <Icon className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4 flex items-center gap-2 text-sm">
            <span
              className={
                trend.startsWith("+") ? "text-emerald-400" : "text-rose-400"
              }
            >
              {trend}
            </span>
            <span className="text-muted-foreground">vs last week</span>
          </div>
        </CardContent>
      </Card>
    );
  }
);
