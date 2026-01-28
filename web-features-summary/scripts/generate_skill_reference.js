const webFeatures = require('web-features');

// This script generates the references/baseline_2023_2026.md file
// Usage: node scripts/generate_skill_reference.js > references/baseline_2023_2026.md

const features = webFeatures.features;
const cutoffDate = '2023-01-01';

const newFeatures = Object.values(features).filter(feature => {
  if (!feature.status || !feature.status.baseline_low_date) return false;
  return feature.status.baseline_low_date >= cutoffDate;
}).sort((a, b) => {
  return b.status.baseline_low_date.localeCompare(a.status.baseline_low_date);
});

console.log(`# Newly Available Web Features (Since 2023) 

This reference lists web platform features that have reached Baseline status (available in all major browsers) recently. Use this to verify availability before recommending modern web APIs.

**Source:** [web-features](https://www.npmjs.com/package/web-features)
**Generated:** ${new Date().toISOString().split('T')[0]}

## Features List
`);

newFeatures.forEach(feature => {
  console.log(`### ${feature.name}`);
  console.log(`- **Baseline Status:** ${feature.status.baseline} (${feature.status.baseline_low_date})`);
  console.log(`- **Description:** ${feature.description_html ? feature.description_html.replace(/<[^>]*>/g, '') : feature.description}`);
  if (feature.spec && feature.spec.length > 0) {
    console.log(`- **Spec:** ${feature.spec[0]}`);
  }
  const support = feature.status.support;
  const supportStr = Object.entries(support)
    .filter(([browser]) => ['chrome', 'firefox', 'safari'].includes(browser))
    .map(([browser, version]) => `${browser} ${version}`)
    .join(', ');
  console.log(`- **Support:** ${supportStr}`);
  console.log('\n---');
});
