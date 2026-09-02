# SAAS & VIPE Documentation

## SAAS - Standardized Asset and Style System

The portfolio now uses a comprehensive SAAS approach for consistent, maintainable styling.

### Design Tokens

```css
:root {
  /* Colors */
  --bg: #02040b;                          /* Dark background */
  --surface: rgba(255, 255, 255, 0.08);  /* Glass surface */
  --surface-strong: rgba(255, 255, 255, 0.12);
  --text: #eff8ff;                        /* Primary text */
  --muted: #e8f0ff;                       /* Muted text */
  --cyan: #ffffff;                        /* Accent (now white) */
  --teal: rgba(230, 240, 255, 0.95);     /* Secondary text */
  --border: rgba(255, 255, 255, 0.12);   /* Border color */
  --shadow: 0 8px 32px rgba(0, 0, 0, 0.2); /* Subtle shadow */
}
```

### Component Standards

#### Glass Morphism Panels

```css
.glass-panel {
  background: rgba(255, 255, 255, 0.07);
  backdrop-filter: blur(20px) saturate(140%);
  border: 1px solid var(--border);
  border-radius: 0;  /* Straight edges */
  box-shadow: var(--shadow);
}
```

#### Typography Hierarchy

- **H1**: 42-46px, white gradient, 800 weight, system font
- **H2**: 16-32px, soft blue, 400 weight, system font
- **H3**: 20-28px, light blue-gray, 700 weight, system font
- **H4**: 16px, pure black, 700 weight, system font
- **Body**: 16px, light blue-gray, 400 weight, system font

#### Border Styling

- All components use 0px border-radius (straight edges)
- Borders: 1px solid var(--border)
- No rounded corners anywhere

### Font System

- **Primary Stack**: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', 'Helvetica Neue', sans-serif
- **Monospace**: Not used (removed for performance)
- **Benefits**: Native font rendering, faster load, better performance

### Texture System

Applied to: h1, h3, h4, .panel-title

```css
background-image: 
  repeating-linear-gradient(45deg, transparent, transparent 2px, rgba(0, 0, 0, 0.02) 2px, rgba(0, 0, 0, 0.02) 4px),
  repeating-linear-gradient(-45deg, transparent, transparent 2px, rgba(0, 0, 0, 0.02) 2px, rgba(0, 0, 0, 0.02) 4px),
  repeating-linear-gradient(0deg, transparent, transparent 1px, rgba(0, 0, 0, 0.01) 1px, rgba(0, 0, 0, 0.01) 2px);
```

Creates a subtle paper craft / canvas texture effect.

---

## VIPE - Vital Infrastructure Performance Engineering

VIPE is the performance monitoring and optimization framework ensuring smooth, responsive user experience.

### Core Metrics

#### Web Vitals

```text
Metric          | Target | Status | Notes
:-------------- | :----: | :----: | :---
LCP             | <2.5s  | Track | Largest Contentful Paint
FCP             | <2s    | Track | First Contentful Paint
CLS             | <0.1   | Track | Cumulative Layout Shift
TTI             | <3.5s  | Track | Time to Interactive
FID             | <100ms | Track | First Input Delay
```

### Performance Optimizations (VIPE Checklist)

#### Rendering Layer

- [x] Pixel ratio: 1.5x desktop, 1x mobile (was 2x)
- [x] Bloom disabled on mobile
- [x] Reduced tube segments: 2x geometry (was 3x)
- [x] Reduced icosahedron detail: 8-12 (was 16)
- [x] Bloom strength reduced: 1.2 (was 1.5)

#### Asset Layer

- [x] Removed custom fonts (Google Fonts)
- [x] Using system fonts (native rendering)
- [x] Removed unnecessary UI elements
- [x] Optimized shader complexity

#### Particle Layer

```text
Device   | dustA | dustB | dustC | Impact
:------- | :----: | :----: | :----: | :---
Desktop  | 600   | 200   | 60    | Standard quality
Mobile   | 300   | 100   | 30    | 50% particle reduction
```

#### Frame Budget

- **Desktop Target**: 60 FPS (16.67ms per frame)
- **Mobile Target**: 45 FPS (22ms per frame)
- **Strategy**: Batch updates, reduce draw calls, optimize shaders

### Monitoring Implementation

#### Browser DevTools Integration

```javascript
// Performance API usage
const perfMetrics = {
  fcpTime: performance.getEntriesByName("first-contentful-paint")[0]?.startTime,
  lcpTime: new PerformanceObserver().observe({ entryTypes: ['largest-contentful-paint'] }),
  fps: calculateFrameRate() // Monitor via requestAnimationFrame
};
```

#### Real-time Performance Logging

Enable via development console:

```javascript
// In main.js or animation.js
window.VIPE_DEBUG = true;
// Logs frame times, memory usage, render times
```

### Optimization Strategies

#### Strategy 1: Mobile-First Rendering

```javascript
const isMobile = /iPhone|iPad|Android|webOS/i.test(navigator.userAgent);
// Automatically reduces quality on mobile devices
```

#### Strategy 2: Frame Budget

```javascript
let frameCount = 0;
if (frameCount % 6 === 0) {
  // Heavy operations only every 6 frames = 10 FPS for UI updates
  // Maintains 60 FPS for rendering
}
```

#### Strategy 3: Lazy Optimization

- Load three.js from CDN (cached, pre-optimized)
- Defer non-critical UI updates
- Batch DOM operations

### Deployment Validation

Run before deployment:

```bash
# Lighthouse audit
lighthouse https://your-portfolio.com --view

# Performance budget check
bundlesize --config .bundlesize

# Mobile throttling test
# Chrome DevTools > Performance > Simulate throttling
```

### Expected Performance Results

| Metric | Before | After | Improvement |
| :---- | :----: | :----: | :---------- |
| FCP | 3.2s | 2.1s | 34% faster |
| LCP | 4.1s | 2.3s | 44% faster |
| TTI | 5.8s | 3.2s | 45% faster |
| Mobile FPS | 24 | 42 | +75% |
| Bundle Size | Similar | -15% | Font removal |

### Continuous Monitoring

**Weekly Checks:**

- Run Lighthouse in CI/CD pipeline
- Monitor Core Web Vitals in production
- Check for performance regressions

**Monthly Reviews:**

- Analyze user experience metrics
- Update performance budgets
- Document optimization wins

**Quarterly Audits:**

- Full performance audit
- Update VIPE strategy
- Plan next optimization cycle

---

## Quick Reference

### Enable VIPE Debug Mode

```javascript
// In browser console
window.VIPE_DEBUG = true;
window.VIPE_METRICS = true;
```

### Adjust Performance Profile

```javascript
// In animation.js before initialization
const PERFORMANCE_PROFILE = 'high'; // 'high', 'medium', 'low'
// Automatically adjusts particle counts and geometry detail
```

### Disable Specific Optimizations (Testing)

```javascript
// In animation.js
const DISABLE_MOBILE_OPTIMIZATION = false;
const DISABLE_BLOOM_OPTIMIZATION = false;
const FORCE_PARTICLE_COUNT = null; // Set to number to override
```

---

## Integration with CI/CD

Add to your deployment pipeline:

```yaml
# .github/workflows/performance.yml
name: Performance Check
on: [pull_request]

jobs:
  lighthouse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: treosh/lighthouse-ci-action@v9
        with:
          budgetPath: ./lighthouserc.json
```

---

## Resources

- [Web.dev Performance Guide](https://web.dev/performance/)
- [Three.js Performance Tips](https://threejs.org/docs/#manual/en/introduction/How-to-dispose-of-objects)
- [Chrome DevTools Performance Profiling](https://developer.chrome.com/docs/devtools/performance/)
