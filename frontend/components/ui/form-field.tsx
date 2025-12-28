import * as React from "react"
import { Input } from "./input"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "./tooltip"
import { HelpCircle } from "lucide-react"
import { cn } from "@/lib/utils"

interface FormFieldProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string
  helpText?: string
  error?: string
}

export const FormField = React.forwardRef<HTMLInputElement, FormFieldProps>(
  ({ label, helpText, error, className, ...props }, ref) => {
    return (
      <div className="grid gap-2">
        <div className="flex items-center gap-2">
          <label htmlFor={props.id} className="text-sm font-medium">
            {label}
          </label>
          {helpText && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <HelpCircle className="h-4 w-4 text-muted-foreground cursor-help" />
                </TooltipTrigger>
                <TooltipContent className="max-w-xs">
                  <p className="text-xs">{helpText}</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>
        <Input
          ref={ref}
          className={cn(error && "border-destructive", className)}
          {...props}
        />
        {error && (
          <p className="text-xs text-destructive">{error}</p>
        )}
      </div>
    )
  }
)
FormField.displayName = "FormField"
