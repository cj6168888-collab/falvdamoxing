import * as React from 'react';
import * as DropdownMenuPrimitive from '@radix-ui/react-dropdown-menu';
import { cn } from '@/lib/utils';
export const Menu = DropdownMenuPrimitive.Root;
export const MenuTrigger = DropdownMenuPrimitive.Trigger;
export const MenuContent = React.forwardRef<React.ElementRef<typeof DropdownMenuPrimitive.Content>, React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Content>>(({ className, ...props }, ref) => (<DropdownMenuPrimitive.Portal><DropdownMenuPrimitive.Content ref={ref} className={cn('z-50 min-w-[8rem] overflow-hidden rounded-md border bg-popover p-1 shadow-md', className)} {...props} /></DropdownMenuPrimitive.Portal>));
export const MenuItem = React.forwardRef<React.ElementRef<typeof DropdownMenuPrimitive.Item>, React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Item>>(({ className, ...props }, ref) => (<DropdownMenuPrimitive.Item ref={ref} className={cn('relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none focus:bg-accent', className)} {...props} />));
