const webFeatures = require('web-features');

// This script helps identify high-impact features for the "Quick Reference" section in SKILL.md
// Usage: node scripts/analyze_high_impact.js

const features = webFeatures.features;

// Keywords to look for high-impact features
const keywords = [
    'Iterator', 'Set', 'Array', 'String', 'Object', 'Promise', // JS Built-ins
    ':not', ':has', ':is', ':where', 'nesting', 'container queries', 'layers', // CSS
    'toSorted', 'toReversed', 'toSpliced', 'with', 'groupBy', // Specific JS methods
    'dialog', 'popover', 'search', // HTML
    'compression', 'view transition' // APIs
];

const highImpactFeatures = Object.values(features).filter(feature => {
    // Check if it's relevant
    const text = (feature.name + ' ' + feature.description).toLowerCase();
    const isRelevant = keywords.some(k => text.includes(k.toLowerCase()));

    if (!isRelevant) return false;

    // Check date/status (approximate cutoff for "modern" in this context)
    if (feature.status.baseline === 'high') {
         if (feature.status.baseline_low_date && feature.status.baseline_low_date >= '2023-01-01') {
             return true;
         }
    } else if (feature.status.baseline === 'low') {
        return true;
    }
    return false;
}).sort((a, b) => {
    // Sort by date (newest first)
    const dateA = a.status.baseline_low_date || '9999-99-99';
    const dateB = b.status.baseline_low_date || '9999-99-99';
    return dateB.localeCompare(dateA);
});

console.log('Found features:', highImpactFeatures.length);
console.log('---');

highImpactFeatures.forEach(f => {
    console.log(`Name: ${f.name}`);
    console.log(`Baseline: ${f.status.baseline} (${f.status.baseline_low_date})`);
    console.log(`Description: ${f.description}`);
    if (f.usage) console.log('Usage data found:', f.usage);
    console.log('---');
});
