const webFeatures = require('web-features');

// IDs/Keywords from the user's query
const queryIds = [
    'customizable-select', 'popover', 'anchor-positioning', 'customized-built-in-elements', 
    'shadow-dom', 'dialog', 'view-transitions', 'cross-document-view-transitions', 
    'file-system-access', 'input-date-time', 'invoker-commands', 'webusb',
    'scroll-driven-animations', 'container-style-queries', 'nesting', 'has', 
    'container-queries', 'scope', 'if', 'grid'
];

const features = webFeatures.features;
const results = {
    baseline: [],
    chrome_only: [], // or broadly "Chrome + maybe others but NOT baseline"
    other: []
};

queryIds.forEach(id => {
    // Attempt to find by ID (which is often the key in web-features)
    // If not found by exact key, try to find by name match
    let feature = features[id];
    
    if (!feature) {
        // Search by keys containing the ID string
        const matchingKey = Object.keys(features).find(k => k.includes(id));
        if (matchingKey) feature = features[matchingKey];
    }

    if (!feature) {
        // Search by name
        feature = Object.values(features).find(f => f.name.toLowerCase().includes(id.replace(/-/g, ' ')));
    }

    if (feature) {
        const status = feature.status;
        const support = status.support || {};
        const isBaseline = status.baseline === 'high' || status.baseline === 'low';
        
        // Check for "Usable in Chrome" (but not baseline)
        const chromeVer = support.chrome;
        const chromeSupported = chromeVer && parseFloat(chromeVer) <= 125; // Assuming ~current version

        const item = {
            id: id,
            name: feature.name,
            baseline: status.baseline,
            chrome: chromeVer,
            firefox: support.firefox,
            safari: support.safari,
            desc: feature.description
        };

        if (isBaseline) {
            results.baseline.push(item);
        } else if (chromeSupported) {
            results.chrome_only.push(item);
        } else {
            results.other.push(item);
        }
    } else {
        console.log(`Could not find feature for: ${id}`);
    }
});

console.log('=== Baseline / Widely Available ===');
results.baseline.forEach(f => console.log(`[${f.baseline.toUpperCase()}] ${f.name} (Chrome ${f.chrome}, FF ${f.firefox}, Safari ${f.safari})`));

console.log('\n=== Usable in Chrome (Limited Compat) ===');
results.chrome_only.forEach(f => console.log(`[NO BASELINE] ${f.name} (Chrome ${f.chrome}, FF ${f.firefox || 'No'}, Safari ${f.safari || 'No'})`));

console.log('\n=== Not Found / Other ===');
results.other.forEach(f => console.log(`[${f.id}] Found but categorized as other`));
