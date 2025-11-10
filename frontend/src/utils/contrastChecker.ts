// Utility to calculate contrast ratio between two colors
// WCAG 2.1 contrast ratio formula: (L1 + 0.05) / (L2 + 0.05), where L1 is lighter and L2 is darker
export function calculateContrastRatio(color1: string, color2: string): number {
  const luminance1 = getRelativeLuminance(color1);
  const luminance2 = getRelativeLuminance(color2);
  
  const lighter = Math.max(luminance1, luminance2);
  const darker = Math.min(luminance1, luminance2);
  
  return (lighter + 0.05) / (darker + 0.05);
}

// Get relative luminance of a color (sRGB to luminance conversion)
function getRelativeLuminance(color: string): number {
  // Convert color string to RGB values
  const rgb = parseColor(color);
  
  // Convert RGB values to sRGB
  const r = srgbConvert(rgb.r);
  const g = srgbConvert(rgb.g);
  const b = srgbConvert(rgb.b);
  
  // Calculate relative luminance
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

// Convert RGB component to sRGB
function srgbConvert(color: number): number {
 const c = color / 255;
  return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
}

// Parse color string to RGB object
function parseColor(color: string): { r: number; g: number; b: number } {
  // Handle hex colors
  if (color.startsWith('#')) {
    const hex = color.slice(1);
    if (hex.length === 3) {
      const r = parseInt(hex[0] + hex[0], 16);
      const g = parseInt(hex[1] + hex[1], 16);
      const b = parseInt(hex[2] + hex[2], 16);
      return { r, g, b };
    } else if (hex.length === 6) {
      const r = parseInt(hex.slice(0, 2), 16);
      const g = parseInt(hex.slice(2, 4), 16);
      const b = parseInt(hex.slice(4, 6), 16);
      return { r, g, b };
    }
  }
  
  // Handle RGB/RGBA functions
  if (color.startsWith('rgb') || color.startsWith('hsl')) {
    const values = color.match(/\d+/g);
    if (values && values.length >= 3) {
      return {
        r: parseInt(values[0]),
        g: parseInt(values[1]),
        b: parseInt(values[2])
      };
    }
  }
  
  // Handle CSS variable names (for our application)
  if (color.startsWith('var(--')) {
    // For this check, we'll return a representative value based on the variable
    // In a real application, we'd resolve the actual CSS variable value
    return getRGBForCSSVariable(color);
  }
  
  // Default fallback
  return { r: 0, g: 0, b: 0 };
}

// Map CSS variables to RGB values for our application
function getRGBForCSSVariable(variable: string): { r: number; g: number; b: number } {
  // This is a simplified mapping for our application's CSS variables
 // In a real implementation, we would resolve actual computed values
  switch(variable) {
    case 'var(--text-primary)':
      return { r: 17, g: 24, b: 39 }; // Light mode: rgb(17, 24, 39)
    case 'var(--text-secondary)':
      return { r: 107, g: 114, b: 128 }; // Light mode: rgb(107, 114, 128)
    case 'var(--text-tertiary)':
      return { r: 156, g: 163, b: 175 }; // Light mode: rgb(156, 163, 175)
    case 'var(--bg-primary)':
      return { r: 255, g: 255, b: 255 }; // Light mode: rgb(255, 255, 255)
    case 'var(--bg-secondary)':
      return { r: 249, g: 250, b: 251 }; // Light mode: rgb(249, 250, 251)
    case 'var(--bg-tertiary)':
      return { r: 243, g: 244, b: 246 }; // Light mode: rgb(243, 244, 246)
    case 'var(--primary-500)':
      return { r: 59, g: 130, b: 246 }; // rgb(59, 130, 246)
    case 'var(--primary-600)':
      return { r: 37, g: 99, b: 235 }; // rgb(37, 99, 235)
    case 'var(--primary-700)':
      return { r: 29, g: 78, b: 216 }; // rgb(29, 78, 216)
    case 'var(--secondary-500)':
      return { r: 139, g: 92, b: 246 }; // rgb(139, 92, 246)
    case 'var(--success-500)':
      return { r: 34, g: 197, b: 94 }; // rgb(34, 197, 94)
    case 'var(--warning-500)':
      return { r: 245, g: 158, b: 11 }; // rgb(245, 158, 11)
    case 'var(--danger-500)':
      return { r: 239, g: 68, b: 68 }; // rgb(239, 68, 68)
    case 'var(--neutral-500)':
      return { r: 115, g: 115, b: 115 }; // rgb(115, 115, 15)
    case 'var(--text-primary-dark)':
      return { r: 241, g: 245, b: 249 }; // Dark mode: rgb(241, 245, 249)
    case 'var(--text-secondary-dark)':
      return { r: 148, g: 163, b: 184 }; // Dark mode: rgb(148, 163, 184)
    case 'var(--bg-primary-dark)':
      return { r: 15, g: 23, b: 42 }; // Dark mode: rgb(15, 23, 42)
    case 'var(--bg-secondary-dark)':
      return { r: 30, g: 41, b: 59 }; // Dark mode: rgb(30, 41, 59)
    default:
      return { r: 0, g: 0, b: 0 };
  }
}

// WCAG AA compliance check
export function isWCAGAACompliant(contrastRatio: number, isLargeText: boolean = false): boolean {
  if (isLargeText) {
    // Large text (at least 18pt or 14pt bold) needs 3:1 ratio
    return contrastRatio >= 3.0;
  } else {
    // Normal text needs 4.5:1 ratio
    return contrastRatio >= 4.5;
  }
}

// WCAG AAA compliance check
export function isWCAGAAACompliant(contrastRatio: number, isLargeText: boolean = false): boolean {
  if (isLargeText) {
    // Large text needs 4.5:1 ratio for AAA
    return contrastRatio >= 4.5;
  } else {
    // Normal text needs 7:1 ratio for AAA
    return contrastRatio >= 7.0;
  }
}