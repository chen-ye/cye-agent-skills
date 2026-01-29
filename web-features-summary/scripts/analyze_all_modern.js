const webFeatures = require('web-features');

// Usage: node scripts/analyze_all_modern.js

const features = webFeatures.features;
const cutoffDate = '2023-01-01';

// Group bucket definitions
const buckets = {
    'css': [],
    'html': [],
    'javascript': [],
    'api': [], // Web APIs (DOM, fetch, etc.)
    'other': []
};

// Helper to determine bucket
function getBucket(f) {
    if (f.group) {
        if (f.group.includes('css')) return 'css';
        if (f.group.includes('html')) return 'html';
        if (f.group.includes('js') || f.group.includes('javascript') || f.name.includes('Array') || f.name.includes('Promise')) return 'javascript';
    }
    // Fallback heuristics
    if (f.name.includes(':') || f.name.includes('@')) return 'css';
    if (f.name.startsWith('<')) return 'html';
    if (f.spec && f.spec[0] && f.spec[0].includes('css')) return 'css';
    return 'api';
}

Object.values(features).forEach(feature => {
    // Filter for modern features (Baseline since 2023 or Baseline Low)
    if (!feature.status) return;

    let isModern = false;
    if (feature.status.baseline === 'high') {
         if (feature.status.baseline_low_date && feature.status.baseline_low_date >= cutoffDate) {
             isModern = true;
         }
    } else if (feature.status.baseline === 'low') {
        isModern = true;
    }

    if (!isModern) return;

    const bucket = getBucket(feature);
    if (buckets[bucket]) {
        buckets[bucket].push(feature);
    } else {
        buckets['other'].push(feature);
    }
});

// Print results
Object.keys(buckets).forEach(key => {
    console.log(`\n========== ${key.toUpperCase()} (${buckets[key].length}) ==========`);
    // Sort by date newest first
    buckets[key].sort((a, b) => {
        const dateA = a.status.baseline_low_date || '9999-99-99';
        const dateB = b.status.baseline_low_date || '9999-99-99';
        return dateB.localeCompare(dateA);
    });

    buckets[key].forEach(f => {
        console.log(`[${f.status.baseline === 'high' ? 'HIGH' : 'LOW '}] ${f.status.baseline_low_date || 'New'} | ${f.name}`);
        // console.log(`      ${f.description}`); // Uncomment for detail
    });
});
