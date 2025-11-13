# Cognitude AI Design System

## Overview
This document outlines the design system for the Cognitude AI platform, providing guidelines and standards for consistent UI/UX across all components and pages.

## 1. Color Palette

### Primary Colors
The primary color palette includes multiple shades for various use cases:

#### Primary (Blue)
- `primary-50`: #eff6ff (Lightest shade)
- `primary-100`: #dbeafe
- `primary-200`: #bfdbfe
- `primary-300`: #93c5fd
- `primary-400`: #60a5fa
- `primary-500`: #3b82f6 (Default primary)
- `primary-600`: #2563eb (Darkened primary)
- `primary-70`: #1d4ed8 (Emphasis)
- `primary-800`: #1e40af (Deep primary)
- `primary-90`: #1e3a8a (Darkest primary)
- `primary-950`: #172554 (Maximum contrast)

#### Secondary (Purple)
- `secondary-50`: #f5f3ff (Lightest shade)
- `secondary-100`: #ede9fe
- `secondary-200`: #ddd6fe
- `secondary-300`: #c4b5fd
- `secondary-400`: #a78bfa
- `secondary-500`: #8b5cf6 (Default secondary)
- `secondary-600`: #7c3aed (Darkened secondary)
- `secondary-700`: #6d28d9 (Emphasis)
- `secondary-800`: #5b21b6 (Deep secondary)
- `secondary-900`: #4c1d95 (Darkest secondary)
- `secondary-950`: #2e1065 (Maximum contrast)

#### Status Colors
- **Success (Green)**: #22c55e (500) - Used for success states, positive feedback
- **Warning (Amber)**: #f59e0b (500) - Used for warnings, caution states
- **Danger (Red)**: #ef4444 (500) - Used for errors, destructive actions
- **Neutral (Gray)**: #6b7280 (500) - Used for neutral information

### Background Colors
- `bg-primary`: #ffffff (Light) / #0f172a (Dark) - Main background
- `bg-secondary`: #f9fafb (Light) / #1e293b (Dark) - Secondary background
- `bg-tertiary`: #f3f4f6 (Light) / #334155 (Dark) - Tertiary background

### Text Colors
- `text-primary`: #111827 (Light) / #f1f5f9 (Dark) - Primary text
- `text-secondary`: #6b7280 (Light) / #94a3b8 (Dark) - Secondary text
- `text-tertiary`: #9ca3af (Light) / #64748b (Dark) - Tertiary text

### Border Colors
- `border-primary`: #e5e7eb (Light) / #334155 (Dark) - Primary borders
- `border-secondary`: #d1d5db (Light) / #1e293b (Dark) - Secondary borders

## 2. Typography System

### Font Family
- **Primary Font**: Inter (Variable font with weights 300-800)
- **Fallback**: system-ui, sans-serif

### Typography Hierarchy

#### Headings
- **H1**: `.h1` - 4xl (2.25rem), font-bold, tracking-tight
- **H2**: `.h2` - 3xl (1.875rem), font-bold, tracking-tight
- **H3**: `.h3` - 2xl (1.5rem), font-bold, tracking-tight
- **H4**: `.h4` - xl (1.25rem), font-semibold, tracking-tight

#### Body Text
- **Body Large**: `.body-lg` - text-lg (1.125rem), text-neutral-700 (light) / text-neutral-300 (dark)
- **Body Medium**: `.body-md` - text-base (1rem), text-neutral-600 (light) / text-neutral-400 (dark)
- **Body Small**: `.body-sm` - text-sm (0.875rem), text-neutral-500 (light) / text-neutral-400 (dark)

#### Labels
- **Label**: `.label` - text-sm (0.875rem), font-medium, text-neutral-700 (light) / text-neutral-300 (dark), mb-2

### Usage Guidelines
- Use H1 for main page titles
- Use H2 for section headers
- Use H3 for subsection headers
- Use H4 for component titles
- Use body text styles consistently for content readability
- Labels should always be paired with form elements

## 3. Spacing System

### Spacing Scale
The design system uses a consistent spacing scale based on 4px increments:

- **Space 1**: 0.25rem (4px)
- **Space 2**: 0.5rem (8px)
- **Space 3**: 0.75rem (12px)
- **Space 4**: 1rem (16px)
- **Space 5**: 1.25rem (20px)
- **Space 6**: 1.5rem (24px)
- **Space 8**: 2rem (32px)
- **Space 10**: 2.5rem (40px) - 10 in config
- **Space 12**: 3rem (48px)
- **Space 16**: 4rem (64px)
- **Space 18**: 4.5rem (72px) - Custom spacing
- **Space 20**: 5rem (80px)
- **Space 24**: 6rem (96px)
- **Space 32**: 8rem (128px)
- **Space 40**: 10rem (160px)
- **Space 44**: 1rem (176px) - 110 in config
- **Space 48**: 12rem (192px) - 120 in config
- **Space 56**: 14rem (224px) - 140 in config
- **Space 64**: 16rem (256px) - 160 in config
- **Space 88**: 22rem (352px) - Custom spacing

### Layout Spacing
- **Page Padding**: 1rem (16px) on mobile, 1.5rem (24px) on desktop
- **Section Spacing**: 1.5rem (24px) between sections
- **Component Spacing**: 1rem (16px) between components
- **Internal Padding**: 1.5rem (24px) for cards and containers

### Spacing Utilities
- `.spacing-tight`: space-y-2 (8px)
- `.spacing-normal`: space-y-4 (16px)
- `.spacing-loose`: space-y-6 (24px)

## 4. Component Library

### Buttons
All buttons use the `.btn` base class with modifier classes for variations:

#### Base Button (`.btn`)
- Padding: px-4 py-2.5 (16px horizontal, 10px vertical)
- Rounded corners: rounded-lg
- Font: font-medium
- Transition: transition-all duration-200
- Focus: focus:outline-none focus:ring-2 focus:ring-offset-2
- Disabled: opacity-50 cursor-not-allowed
- Display: inline-flex items-center justify-center gap-2

#### Button Sizes
- **Small**: `.btn-sm` - px-3 py-1.5, text-sm
- **Large**: `.btn-lg` - px-6 py-3, text-lg
- **Default**: `.btn` - px-4 py-2.5, text-base

#### Button Variants
- **Primary**: `.btn-primary` - Gradient from primary-600 to secondary-600, white text
- **Secondary**: `.btn-secondary` - Gradient from neutral-600 to neutral-700, white text
- **Danger**: `.btn-danger` - Gradient from danger-600 to danger-700, white text
- **Success**: `.btn-success` - Gradient from success-600 to success-700, white text
- **Ghost**: `.btn-ghost` - Transparent background, hover with neutral-100
- **Outline**: `.btn-outline` - Transparent with border, neutral text

### Cards
- **Base Card**: `.card` - bg-white (dark:bg-neutral-800), rounded-xl, shadow-sm, border, p-6
- **Hover Card**: `.card-hover` - Adds hover effects: shadow-md, border change, slight elevation
- **Interactive Card**: `.card-interactive` - Hover effects + cursor-pointer + active scale

### Inputs
- **Base Input**: `.input` - Full width, px-4 py-3, bg-white (dark:bg-neutral-800), border, rounded-lg
- **Error Input**: `.input-error` - Red border for error states
- **Select**: `.select` - Same as input with appearance-none and cursor-pointer
- **Textarea**: `.textarea` - Same as input with min-h-[100px] and resize-y

### Badges
- **Base Badge**: `.badge` - Inline-flex, px-3 py-1, rounded-full, text-xs font-medium
- **Success Badge**: `.badge-success` - Green background with border
- **Error Badge**: `.badge-error` - Red background with border
- **Warning Badge**: `.badge-warning` - Amber background with border
- **Info Badge**: `.badge-info` - Blue background with border
- **Neutral Badge**: `.badge-neutral` - Gray background with border

### Alerts
- **Base Alert**: `.alert` - p-4, rounded-lg, border, flex items-start gap-3, animate-slide-down
- **Success Alert**: `.alert-success` - Green background and border
- **Error Alert**: `.alert-error` - Red background and border
- **Warning Alert**: `.alert-warning` - Amber background and border
- **Info Alert**: `.alert-info` - Blue background and border

### Tabs
- **Base Tab**: `.tab` - px-4 py-2, font-medium, hover effects, border-b, cursor-pointer
- **Active Tab**: `.tab-active` - Blue text and border, active state

### Other Components
- **Spinner**: `.spinner` - Inline-block, animate-spin, border with transparent top
- **Skeleton**: `.skeleton` - Animated loading placeholder with background
- **Divider**: `.divider` - Horizontal rule with appropriate spacing

## 5. Dark Mode Implementation

### Dark Mode Strategy
The system uses Tailwind's class-based dark mode strategy, where the `dark` class is added to the document element to activate dark mode styles.

### Color Mapping
- Background colors transition from light to dark variants
- Text colors invert for better contrast in dark mode
- Border colors adapt to the dark context
- All color variables have both light and dark mode definitions

### Automatic Theme Detection
- Checks for user's saved preference in localStorage
- Falls back to system preference (prefers-color-scheme)
- Persists user's choice in localStorage

### Theme Switching
- Implemented through ThemeContext and ThemeProvider
- Provides toggleTheme and setTheme functions
- Smooth transitions between themes

## 6. Accessibility Guidelines

### Color Contrast
All text and background combinations meet WCAG 2.1 AA standards:
- Normal text requires 4.5:1 contrast ratio
- Large text (18pt+ or 14pt+ bold) requires 3:1 ratio
- Tools provided for checking contrast ratios

### Keyboard Navigation
- All interactive elements are keyboard accessible
- Focus states are visible and clear
- Logical tab order is maintained

### Semantic HTML
- Proper heading hierarchy (H1 → H2 → H3 → H4)
- Use of appropriate ARIA labels where needed
- Semantic elements for better screen reader experience

### Component Accessibility
- All buttons have appropriate labels
- Form elements have associated labels
- Modals trap focus and have close functionality
- Proper role attributes for custom components

### Focus Management
- Visual focus indicators for keyboard users
- Focus management in modals and dropdowns
- Preserving focus when content changes

## 7. Usage Examples for Common UI Patterns

### Dashboard Layout
```jsx
<div className="min-h-screen bg-pattern flex flex-col">
  <header className="glass sticky top-0 z-50 border-b border-gray-200/50 shadow-sm dark:border-gray-700/50">
    {/* Header content */}
  </header>
 <main className="flex-1">{children}</main>
  <footer className="border-t border-gray-200 dark:border-gray-700 bg-white/50 dark:bg-gray-800/50 backdrop-blur-sm">
    {/* Footer content */}
  </footer>
</div>
```

### Card Component
```jsx
<div className="card">
  <h3 className="h3 mb-4">Card Title</h3>
  <p className="body-md">Card content goes here</p>
 <div className="mt-4 flex gap-3">
    <button className="btn btn-primary">Primary Action</button>
    <button className="btn btn-outline">Secondary Action</button>
 </div>
</div>
```

### Form Pattern
```jsx
<form className="space-y-4">
  <div>
    <label className="label">Field Label</label>
    <input type="text" className="input" placeholder="Enter value" />
  </div>
  <div>
    <label className="label">Select Option</label>
    <select className="select">
      <option>Option 1</option>
      <option>Option 2</option>
    </select>
  </div>
  <button type="submit" className="btn btn-primary w-full">Submit</button>
</form>
```

### Alert Pattern
```jsx
<div className="alert alert-info">
  <InfoIcon className="w-5 h-5" />
  <div>
    <h4 className="font-medium">Informational Alert</h4>
    <p className="text-sm mt-1">This is an informational message to the user</p>
  </div>
</div>
```

### Modal Pattern
```jsx
<Modal isOpen={isOpen} onClose={closeModal} title="Modal Title">
  <div className="space-y-4">
    <p>Modal content goes here</p>
    <div className="flex justify-end gap-3 pt-4">
      <button className="btn btn-outline" onClick={closeModal}>Cancel</button>
      <button className="btn btn-primary">Confirm</button>
    </div>
  </div>
</Modal>
```

### Button Variations
```jsx
<div className="flex flex-wrap gap-3">
  <button className="btn btn-primary">Primary</button>
 <button className="btn btn-secondary">Secondary</button>
  <button className="btn btn-success">Success</button>
  <button className="btn btn-danger">Danger</button>
  <button className="btn btn-ghost">Ghost</button>
 <button className="btn btn-outline">Outline</button>
</div>
```

### Responsive Design
- Mobile-first approach with responsive breakpoints
- Grid and flexbox utilities for adaptive layouts
- Proper spacing adjustments for different screen sizes
- Touch-friendly targets (minimum 44px touch targets)

### Animation Guidelines
- Subtle transitions for state changes (200ms duration)
- Meaningful animations that enhance user experience
- Reduced motion support via `prefers-reduced-motion`
- Performance-optimized CSS animations

This design system ensures consistent, accessible, and maintainable UI across the Cognitude AI platform.