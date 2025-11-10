import { calculateContrastRatio, isWCAGAACompliant } from './contrastChecker';

interface ContrastCheck {
  element: string;
  foreground: string;
  background: string;
  contrastRatio: number;
  isCompliant: boolean;
 isLargeText: boolean;
  requiredRatio: number;
}

interface AccessibilityAuditResult {
  compliant: ContrastCheck[];
  nonCompliant: ContrastCheck[];
  summary: {
    totalChecks: number;
    compliantCount: number;
    nonCompliantCount: number;
    complianceRate: number;
  };
}

// Define the color values for our application
const COLOR_VALUES = {
 // Light mode
 'text-primary': { r: 17, g: 24, b: 39 },      // rgb(17, 24, 39) - var(--text-primary)
  'text-secondary': { r: 107, g: 114, b: 128 }, // rgb(107, 114, 128) - var(--text-secondary)
  'text-tertiary': { r: 156, g: 163, b: 175 },  // rgb(156, 163, 175) - var(--text-tertiary)
  'bg-primary': { r: 255, g: 255, b: 255 },     // rgb(255, 255, 255) - var(--bg-primary)
  'bg-secondary': { r: 249, g: 250, b: 251 },   // rgb(249, 250, 251) - var(--bg-secondary)
  'bg-tertiary': { r: 243, g: 244, b: 246 },    // rgb(243, 244, 246) - var(--bg-tertiary)
  'primary-500': { r: 59, g: 130, b: 246 },     // rgb(59, 130, 246) - var(--color-primary-500)
  'primary-600': { r: 37, g: 99, b: 235 },      // rgb(37, 99, 235) - var(--color-primary-600)
  'primary-700': { r: 29, g: 78, b: 216 },      // rgb(29, 78, 216) - var(--color-primary-700)
  'secondary-500': { r: 139, g: 92, b: 246 },   // rgb(139, 92, 246) - var(--color-secondary-500)
  'success-500': { r: 34, g: 197, b: 94 },      // rgb(34, 197, 94) - var(--color-success-500)
  'warning-500': { r: 245, g: 158, b: 11 },     // rgb(245, 158, 11) - var(--color-warning-500)
  'danger-500': { r: 239, g: 68, b: 68 },       // rgb(239, 68) - var(--color-danger-500)
  'neutral-500': { r: 115, g: 15, b: 115 },    // rgb(115, 115, 15) - var(--color-neutral-500)
  
  // Dark mode
  'text-primary-dark': { r: 241, g: 245, b: 249 },   // rgb(241, 245, 249) - var(--text-primary) in dark mode
  'text-secondary-dark': { r: 148, g: 163, b: 184 }, // rgb(148, 163, 184) - var(--text-secondary) in dark mode
  'bg-primary-dark': { r: 15, g: 23, b: 42 },         // rgb(15, 23, 42) - var(--bg-primary) in dark mode
  'bg-secondary-dark': { r: 30, g: 41, b: 59 },       // rgb(30, 41, 59) - var(--bg-secondary) in dark mode
};

// Convert RGB object to CSS rgb() string
function rgbToString(rgb: { r: number; g: number; b: number }): string {
  return `rgb(${rgb.r}, ${rgb.g}, ${rgb.b})`;
}

// Get RGB values for a color name
function getColorRGB(colorName: string): { r: number; g: number; b: number } {
  return COLOR_VALUES[colorName as keyof typeof COLOR_VALUES] || { r: 0, g: 0, b: 0 };
}

export function runAccessibilityAudit(): AccessibilityAuditResult {
  const checks: ContrastCheck[] = [];
  
  // Define the color combinations to check
  const colorCombinations = [
    // Light mode combinations
    { element: 'Primary text on light background', fg: 'text-primary', bg: 'bg-primary', largeText: false },
    { element: 'Secondary text on light background', fg: 'text-secondary', bg: 'bg-primary', largeText: false },
    { element: 'Tertiary text on light background', fg: 'text-tertiary', bg: 'bg-primary', largeText: false },
    { element: 'Primary text on secondary background', fg: 'text-primary', bg: 'bg-secondary', largeText: false },
    { element: 'Secondary text on secondary background', fg: 'text-secondary', bg: 'bg-secondary', largeText: false },
    { element: 'Tertiary text on secondary background', fg: 'text-tertiary', bg: 'bg-secondary', largeText: false },
    
    // Dark mode combinations
    { element: 'Primary text on dark background', fg: 'text-primary-dark', bg: 'bg-primary-dark', largeText: false },
    { element: 'Secondary text on dark background', fg: 'text-secondary-dark', bg: 'bg-primary-dark', largeText: false },
    { element: 'Primary text on dark secondary background', fg: 'text-primary-dark', bg: 'bg-secondary-dark', largeText: false },
    { element: 'Secondary text on dark secondary background', fg: 'text-secondary-dark', bg: 'bg-secondary-dark', largeText: false },
    
    // Button combinations
    { element: 'White text on primary button', fg: 'white', bg: 'primary-600', largeText: false },
    { element: 'White text on secondary button', fg: 'white', bg: 'secondary-500', largeText: false },
    { element: 'White text on success button', fg: 'white', bg: 'success-500', largeText: false },
    { element: 'White text on warning button', fg: 'white', bg: 'warning-500', largeText: false },
    { element: 'White text on danger button', fg: 'white', bg: 'danger-500', largeText: false },
    { element: 'Primary text on ghost button', fg: 'text-primary', bg: 'transparent', largeText: false },
    { element: 'Dark text on ghost button hover', fg: 'text-primary', bg: 'bg-secondary', largeText: false },
    
    // Form elements
    { element: 'Input text on white background', fg: 'text-primary', bg: 'bg-primary', largeText: false },
    { element: 'Placeholder text on white background', fg: 'text-tertiary', bg: 'bg-primary', largeText: false },
    
    // Badge combinations
    { element: 'Success badge text', fg: 'success-500', bg: 'success-50', largeText: false },
    { element: 'Warning badge text', fg: 'warning-500', bg: 'warning-50', largeText: false },
    { element: 'Danger badge text', fg: 'danger-500', bg: 'danger-50', largeText: false },
    { element: 'Info badge text', fg: 'primary-500', bg: 'primary-50', largeText: false },
    { element: 'Neutral badge text', fg: 'neutral-500', bg: 'bg-tertiary', largeText: false },
    
    // Link combinations
    { element: 'Primary link text', fg: 'primary-600', bg: 'bg-primary', largeText: false },
    { element: 'Primary link hover text', fg: 'primary-700', bg: 'bg-primary', largeText: false },
    
    // Card components
    { element: 'Card title text', fg: 'text-primary', bg: 'bg-primary', largeText: false },
    { element: 'Card body text', fg: 'text-secondary', bg: 'bg-primary', largeText: false },
  ];
  
  // Process each color combination
 for (const combo of colorCombinations) {
   let fgRGB, bgRGB;
   
   if (combo.fg === 'white') {
     fgRGB = { r: 255, g: 255, b: 255 };
     bgRGB = getColorRGB(combo.bg);
   } else if (combo.fg === 'transparent') {
     // For transparent backgrounds, assume white as the base
     fgRGB = getColorRGB(combo.fg);
     bgRGB = { r: 255, g: 255, b: 255 };
   } else {
     fgRGB = getColorRGB(combo.fg);
     bgRGB = getColorRGB(combo.bg);
   }
   
   // Ensure we have valid RGB values
   if (!fgRGB || !bgRGB) {
     console.warn(`Could not resolve colors for: ${combo.element}`);
     continue;
   }
   
   const fgColor = rgbToString(fgRGB);
   const bgColor = rgbToString(bgRGB);
    
    const contrastRatio = calculateContrastRatio(fgColor, bgColor);
    const requiredRatio = combo.largeText ? 3.0 : 4.5;
    const isCompliant = isWCAGAACompliant(contrastRatio, combo.largeText);
    
    checks.push({
      element: combo.element,
      foreground: fgColor,
      background: bgColor,
      contrastRatio: parseFloat(contrastRatio.toFixed(2)),
      isCompliant,
      isLargeText: combo.largeText,
      requiredRatio
    });
  }
  
  // Separate compliant and non-compliant items
  const compliant = checks.filter(check => check.isCompliant);
  const nonCompliant = checks.filter(check => !check.isCompliant);
  
  // Create summary
  const summary = {
    totalChecks: checks.length,
    compliantCount: compliant.length,
    nonCompliantCount: nonCompliant.length,
    complianceRate: parseFloat(((compliant.length / checks.length) * 100).toFixed(2))
  };
  
  return {
    compliant,
    nonCompliant,
    summary
  };
}

// Function to get a detailed accessibility report
export function getAccessibilityReport(): string {
  const audit = runAccessibilityAudit();
  
  let report = `# Accessibility Audit Report\n\n`;
  report += `## Summary\n`;
  report += `- Total Checks: ${audit.summary.totalChecks}\n`;
  report += `- Compliant: ${audit.summary.compliantCount}\n`;
  report += `- Non-Compliant: ${audit.summary.nonCompliantCount}\n`;
  report += `- Compliance Rate: ${audit.summary.complianceRate}%\n\n`;
  
  if (audit.nonCompliant.length > 0) {
    report += `## Non-Compliant Items (Require Attention)\n`;
    report += `These color combinations do not meet WCAG AA standards:\n\n`;
    
    for (const item of audit.nonCompliant) {
      report += `- **${item.element}**: ${item.contrastRatio}:1 contrast (requires ${item.requiredRatio}:1)\n`;
      report += `  - Foreground: ${item.foreground}\n`;
      report += `  - Background: ${item.background}\n`;
      report += `  - WCAG AA Compliant: ${item.isCompliant ? 'Yes' : 'No'}\n\n`;
    }
  }
  
  if (audit.compliant.length > 0) {
    report += `## Compliant Items\n`;
    report += `These color combinations meet WCAG AA standards:\n\n`;
    
    for (const item of audit.compliant) {
      report += `- **${item.element}**: ${item.contrastRatio}:1 contrast\n`;
    }
 }
  
  report += `\n## Recommendations\n`;
  if (audit.nonCompliant.length > 0) {
    report += `- Address all non-compliant items by adjusting foreground or background colors to achieve minimum contrast ratios\n`;
    report += `- For normal text, ensure contrast ratio is at least 4.5:1\n`;
    report += `- For large text (18pt+ or 14pt+ bold), ensure contrast ratio is at least 3:1\n`;
  } else {
    report += `- All tested color combinations meet WCAG AA standards\n`;
    report += `- Consider testing additional components not covered in this audit\n`;
  }
  
  return report;
}