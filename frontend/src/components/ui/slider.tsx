import * as React from "react"
import { cn } from "@/lib/utils"

interface SliderProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'value' | 'onChange'> {
  max?: number;
  step?: number;
  value?: number[];
  onValueChange?: (value: number[]) => void;
}

const Slider = React.forwardRef<HTMLInputElement, SliderProps>(
  ({ className, max = 100, step = 1, value, onValueChange, ...props }, ref) => {
    const currentValue = value?.[0] ?? 0;
    
    return (
      <input
        type="range"
        ref={ref}
        max={max}
        step={step}
        value={currentValue}
        onChange={(e) => onValueChange?.([parseInt(e.target.value)])}
        className={cn(
          "w-full h-2 bg-secondary rounded-full appearance-none cursor-pointer",
          "[&::-webkit-slider-thumb]:appearance-none",
          "[&::-webkit-slider-thumb]:w-5",
          "[&::-webkit-slider-thumb]:h-5",
          "[&::-webkit-slider-thumb]:rounded-full",
          "[&::-webkit-slider-thumb]:border-2",
          "[&::-webkit-slider-thumb]:border-primary",
          "[&::-webkit-slider-thumb]:bg-background",
          "[&::-webkit-slider-thumb]:cursor-pointer",
          "[&::-webkit-slider-thumb]:transition-colors",
          className
        )}
        {...props}
      />
    )
  }
)
Slider.displayName = "Slider"

export { Slider }
