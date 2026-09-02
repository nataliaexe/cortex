# Portfolio Maintenance Guide

## Performance Optimizations Implemented

### Rendering Optimizations

- **Reduced Pixel Ratio**: Desktop targets 1.5x, mobile targets 1x (was 2x)
- **Simplified Geometry**: Reduced tube segments and icosahedron detail levels
- **Bloom Disabled on Mobile**: Post-processing bloom effect is disabled for mobile devices
- **Optimized Particles**: Reduced particle counts:
  - Desktop: dustA 600 → 1200 (config optimized)
  - Mobile: dustA 300, dustB 100, dustC 30
- **Frame Update Optimization**: UI updates are now batched, reducing DOM reflows

### Browser Detection

Mobile devices are automatically detected and optimized:

```javascript
const isMobile = /iPhone|iPad|Android|webOS/i.test(navigator.userAgent);
```

---

## Design System Updates

### Color Palette (SAAS - Standardized Asset and Style System)

- **Primary**: White (#ffffff) - Celestial white
- **Secondary**: Soft Blue (#e6f0ff)
- **Text**: Light Blue-Gray (#eff8ff)
- **Surface**: Semi-transparent white with glass morphism
- **Previous Colors**: Azure/cyan replaced with white celestial

### Typography

- **Font Stack**: System fonts (-apple-system, BlinkMacSystemFont, Segoe UI, Inter)
- **Removed**: Share Tech Mono, Syncopate fonts (heavier loading)
- **Benefits**: Faster load times, better performance

### Components

- **Border Radius**: Changed to 0 (straight edges, clean lines)
- **Glass Morphism**: Enhanced with improved blur and transparency
- **Shadows**: Softened for modern, minimal aesthetic

### Texture System

- Paper craft texture applied to titles (h1, h3, h4)
- Cross-hatch patterns at 45-degree angles for subtle grain effect
- Non-intrusive overlay using CSS gradients

---

## Monitoring & Maintenance (VIPE - Vital Infrastructure Performance Engineering)

### Key Metrics to Monitor

1. **First Contentful Paint (FCP)**: < 2s target
2. **Largest Contentful Paint (LCP)**: < 2.5s target
3. **Cumulative Layout Shift (CLS)**: < 0.1 target
4. **Time to Interactive (TTI)**: < 3.5s target

### Performance Checkpoints

- Test on mobile devices (throttled 4G)
- Check bloom effect is disabled on mobile
- Verify particle count matches device type
- Monitor frame rate (target 60 FPS on desktop, 30-45 FPS on mobile)

### Maintenance Tasks

**Weekly**:

- Check performance metrics in browser DevTools
- Monitor network waterfall for asset loading

**Monthly**:

- Run Lighthouse audit
- Check for browser compatibility issues
- Review Three.js version updates

**Quarterly**:

- Performance regression testing
- Update design documentation
- Evaluate new optimization techniques

### Browser DevTools Checklist

```text
Performance Tab:
- Frame rate should stay consistent
- No long tasks (>50ms)
- Memory usage should stabilize

Network Tab:
- Total bundle size
- Asset loading waterfall
- Cache effectiveness
```

---

## Configuration Options

### Adjusting Particle Counts

Edit `js/animation.js` line ~340:

```javascript
// Lower counts = better performance
// Higher counts = more visual complexity
const dustA = makeParticles(isMobile ? 300 : 600, ...);
const dustB = makeParticles(isMobile ? 100 : 200, ...);
const dustC = makeParticles(isMobile ? 30 : 60, ...);
```

### Adjusting Bloom Intensity

Edit `js/animation.js` line ~44:

```javascript
bloomPass.strength = isMobile ? 0 : 1.2;    // 0 = disabled
bloomPass.radius = 0.6;                     // Lower = sharper
```

### Geometry Detail Level

Edit `js/animation.js` line ~180:

```javascript
// Tube segments: lower = simpler geometry
const geo = new THREE.TubeGeometry(curve, Math.floor(curve.getLength() * 2), ...);
                                           // Multiply factor controls complexity
```

---

## Deployment Checklist

Before deploying to production:

- [ ] Run `npm run build` (or equivalent)
- [ ] Test on mobile devices (iOS Safari, Chrome Android)
- [ ] Verify performance metrics
- [ ] Check that "Neural Synapse" panel is hidden
- [ ] Verify white/celestial color scheme applied
- [ ] Test glass morphism effects across browsers
- [ ] Validate texture rendering on titles

---

## File Structure

```text
portfolio-frontend/
├── index.html          # Main document (updated fonts)
├── css/
│   └── styles.css      # All design system, SAAS colors, VIPE metrics
├── js/
│   ├── animation.js    # Three.js rendering (optimized)
│   └── main.js         # Form handling
└── assets/             # Images and static content
```

---

## Troubleshooting

**Performance Issues on Desktop**:

- Increase pixel ratio in animation.js
- Check for browser extensions interfering
- Verify hardware acceleration is enabled

**Mobile Too Slow**:

- Reduce particle counts further
- Disable bloom completely
- Reduce geometry detail

**Colors Look Different**:

- Clear browser cache
- Check display color profile
- Verify CSS variables are loaded

**Text Texture Too Strong/Weak**:

- Edit texture opacity in CSS (lines with `rgba(0, 0, 0, 0.02)`)
- Adjust the gradient repeat values

---

## Resources

- [Three.js Documentation](https://threejs.org/docs/)
- [Web Performance](https://web.dev/performance/)
- [CSS Performance](https://developer.mozilla.org/en-US/docs/Web/Performance)
