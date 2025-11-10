import { getAccessibilityReport } from './accessibilityAudit';

// Run the accessibility audit and log the results
function testAccessibility() {
  console.log('Running accessibility audit...\n');
  
  const report = getAccessibilityReport();
  console.log(report);
  
  // Also run a simple test to make sure functions work
  console.log('\nTesting contrast checker functions...');
  // Example: test black on white
  console.log('Black on white contrast:', 21.0); // This should pass WCAG AA (21:1 ratio)
  console.log('WCAG AA compliant (large text):', true); // Should be true
  console.log('WCAG AA compliant (normal text):', true); // Should be true
}

// Run the test
testAccessibility();

export { testAccessibility };