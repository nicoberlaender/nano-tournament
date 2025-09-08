"use client"

import * as React from "react"
import * as OTPFieldPrimitive from "@radix-ui/react-one-time-password-field"

import { cn } from "@/lib/utils"

const OneTimePasswordField = React.forwardRef<
  React.ElementRef<typeof OTPFieldPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof OTPFieldPrimitive.Root>
>(({ className, ...props }, ref) => (
  <OTPFieldPrimitive.Root
    ref={ref}
    className={cn(
      "flex items-center gap-2 has-[:disabled]:opacity-50",
      className
    )}
    {...props}
  />
))
OneTimePasswordField.displayName = "OneTimePasswordField"

const OneTimePasswordFieldInput = React.forwardRef<
  React.ElementRef<typeof OTPFieldPrimitive.Input>,
  React.ComponentPropsWithoutRef<typeof OTPFieldPrimitive.Input>
>(({ className, ...props }, ref) => (
  <OTPFieldPrimitive.Input
    ref={ref}
    className={cn(
      "relative flex h-20 w-16 items-center justify-center border-4 border-black text-3xl font-black transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 rounded-xl text-center",
      className
    )}
    style={{ backgroundColor: '#FBF3B9' }}
    {...props}
  />
))
OneTimePasswordFieldInput.displayName = "OneTimePasswordFieldInput"

export {
  OneTimePasswordField,
  OneTimePasswordFieldInput,
}