# 🎨 Design System Reference

## Color Palette

### Primary Colors
```css
--bg: #02040b              /* Dark background */
--cyan: #ffffff            /* Primary accent (white) */
--text: #eff8ff            /* Primary text (light) */
```

### Secondary Colors
```css
--teal: rgba(230, 240, 255, 0.95)      /* Secondary text (soft blue) */
--muted: #e8f0ff                        /* Muted text (pale blue) */
--surface: rgba(255, 255, 255, 0.08)   /* Glass surface */
--surface-strong: rgba(255, 255, 255, 0.12)  /* Strong surface */
```

### Functional Colors
```css
--border: rgba(255, 255, 255, 0.12)    /* Borders (light) */
--shadow: 0 8px 32px rgba(0, 0, 0, 0.2) /* Shadows (subtle) */
```

### Color Migration (Antes → Depois)
| Elemento | Antes | Depois |
|----------|-------|--------|
| Accent | `rgba(0, 220, 255, 0.9)` | `#ffffff` |
| Secondary | `rgba(0, 200, 200, 0.7)` | `rgba(230, 240, 255, 0.95)` |
| Border | `rgba(136, 200, 255, 0.16)` | `rgba(255, 255, 255, 0.12)` |
| Background | `rgba(6, 12, 30, 0.72)` | `rgba(255, 255, 255, 0.08)` |

---

## Typography Scale

### Heading Hierarchy
```css
h1 {
  font-size: clamp(2.5rem, 5vw, 4.6rem);
  font-weight: 800;
  letter-spacing: -0.02em;
  font-family: system fonts;
  color: linear-gradient(135deg, #ffffff, #e6f0ff);
}

h2 {
  font-size: clamp(1rem, 2vw, 1.35rem);
  font-weight: 400;
  letter-spacing: 0.02em;
  color: rgba(230, 240, 255, 0.95);
}

h3 {
  font-size: clamp(1.25rem, 2.2vw, 1.8rem);
  font-weight: 700;
  letter-spacing: -0.01em;
}

h4 {
  font-size: 16px;
  font-weight: 700;
  letter-spacing: -0.01em;
  color: #000000;
}

body {
  font-size: 16px;
  font-weight: 400;
  line-height: 1.6;
  color: #eff8ff;
}
```

### Font Family Stack
```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', 'Helvetica Neue', sans-serif;
```

**Benefícios:**
- Safari: -apple-system
- Windows: Segoe UI
- Linux: Liberation Sans
- Fallback: Helvetica/sans-serif
- Fast: Sistema operacional (não download)

---

## Component Library

### Glass Panels
```css
.glass-panel {
  background: rgba(255, 255, 255, 0.07);
  backdrop-filter: blur(20px) saturate(140%);
  -webkit-backdrop-filter: blur(20px) saturate(140%);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 0;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

/* Variant: Strong (more opaque) */
.glass-panel.strong {
  background: rgba(255, 255, 255, 0.12);
}

/* Variant: Subtle (more transparent) */
.glass-panel.subtle {
  background: rgba(255, 255, 255, 0.03);
}
```

### Buttons
```css
button {
  padding: 0.8rem 1.2rem;
  border-radius: 0;
  border: none;
  cursor: pointer;
  font-weight: 700;
  background: linear-gradient(135deg, #ffffff, #e6f0ff);
  color: #000000;
  transition: transform 180ms ease;
}

button:hover {
  transform: translateY(-2px);
}

button:active {
  transform: translateY(0);
}
```

### Input Fields
```css
input, textarea {
  width: 100%;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(0, 0, 0, 0.2);
  color: #eff8ff;
  padding: 0.9rem 1rem;
  border-radius: 0;
  font-family: inherit;
  font-size: inherit;
}

input:focus, textarea:focus {
  outline: none;
  border-color: rgba(255, 255, 255, 0.3);
  background: rgba(0, 0, 0, 0.3);
}
```

### Chips/Tags
```css
.chip {
  padding: 0.35rem 0.6rem;
  border-radius: 0;
  background: rgba(255, 255, 255, 0.1);
  font-size: 0.8rem;
  color: rgba(200, 220, 255, 0.95);
}
```

---

## Texture System

### Craft Paper Grain (Default)
```css
h1, h3, h4, .panel-title {
  background-image: 
    repeating-linear-gradient(45deg, transparent, transparent 2px, rgba(0, 0, 0, 0.02) 2px, rgba(0, 0, 0, 0.02) 4px),
    repeating-linear-gradient(-45deg, transparent, transparent 2px, rgba(0, 0, 0, 0.02) 2px, rgba(0, 0, 0, 0.02) 4px),
    repeating-linear-gradient(0deg, transparent, transparent 1px, rgba(0, 0, 0, 0.01) 1px, rgba(0, 0, 0, 0.01) 2px);
  background-size: 4px 4px, 4px 4px, 2px 2px;
  background-position: 0 0, 0 0, 0 0;
}
```

### No Texture (Plain)
```css
.h1-plain {
  background-image: none;
}
```

### Heavy Texture
```css
.texture-heavy {
  background-image: 
    repeating-linear-gradient(45deg, transparent, transparent 2px, rgba(0, 0, 0, 0.05) 2px, rgba(0, 0, 0, 0.05) 4px),
    repeating-linear-gradient(-45deg, transparent, transparent 2px, rgba(0, 0, 0, 0.05) 2px, rgba(0, 0, 0, 0.05) 4px),
    repeating-linear-gradient(0deg, transparent, transparent 1px, rgba(0, 0, 0, 0.03) 1px, rgba(0, 0, 0, 0.03) 2px);
}
```

---

## Layout Grid

### Section Padding
```css
.section {
  padding: 5rem 1.3rem;  /* Vertical, Horizontal */
  max-width: 1180px;
  margin: 0 auto;
}

@media (max-width: 960px) {
  .section {
    padding: 4rem 1rem;
  }
}
```

### Grid Layouts
```css
/* About Section */
.about-grid {
  display: grid;
  gap: 1.4rem;
  grid-template-columns: 1.3fr 0.8fr;
  align-items: start;
}

/* Projects Section */
.project-grid {
  display: grid;
  gap: 1.2rem;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

/* Responsive */
@media (max-width: 960px) {
  .project-grid {
    grid-template-columns: 1fr 1fr;
  }
  .about-grid {
    grid-template-columns: 1fr;
  }
}
```

---

## Spacing System

### Margins & Padding
```css
/* Vertical Rhythm */
margin-bottom: 0.6rem;   /* Small spacing */
margin-bottom: 1.4rem;   /* Medium spacing */
margin-bottom: 2rem;     /* Large spacing */
margin-bottom: 5rem;     /* Section spacing */

/* Padding */
padding: 1rem;           /* Tight */
padding: 1.2rem;         /* Standard */
padding: 1.3rem;         /* Generous */
padding: 2rem;           /* Spacious */
```

### Gap System
```css
gap: 0.45rem;   /* Chips/small items */
gap: 0.6rem;    /* Inline elements */
gap: 0.7rem;    /* Links/buttons */
gap: 1rem;      /* Form elements */
gap: 1.2rem;    /* Cards */
gap: 1.4rem;    /* Grid items */
```

---

## Effects & Animations

### Blur (Glass Morphism)
```css
backdrop-filter: blur(20px) saturate(140%);
-webkit-backdrop-filter: blur(20px) saturate(140%);
```

### Shadows
```css
/* Subtle */
box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);

/* Medium */
box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);

/* Strong */
box-shadow: 0 12px 48px rgba(0, 0, 0, 0.2);
```

### Transitions
```css
transition: transform 180ms ease;
transition: border-color 180ms ease;
transition: opacity 0.8s ease;
```

### Cursor
```css
cursor: none;  /* Custom cursor only */
```

---

## Mobile Optimizations

### Font Sizes
```css
/* Fluid font scaling */
font-size: clamp(1rem, 2vw, 1.35rem);
/* min, preferred (viewport %), max */
```

### Touch-friendly Buttons
```css
button, a {
  min-height: 44px;  /* iOS recommendation */
  min-width: 44px;   /* Touch target */
  padding: 0.8rem 1.2rem;
}
```

### Viewport Meta
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
```

---

## CSS Variable Quick Reference

### Usage
```css
/* Define */
:root {
  --surface: rgba(255, 255, 255, 0.08);
}

/* Apply */
background: var(--surface);

/* Fallback */
background: var(--surface, rgba(255, 255, 255, 0.08));
```

### All Variables
```css
:root {
  --bg: #02040b;
  --surface: rgba(255, 255, 255, 0.08);
  --surface-strong: rgba(255, 255, 255, 0.12);
  --text: #eff8ff;
  --muted: #e8f0ff;
  --cyan: #ffffff;
  --teal: rgba(230, 240, 255, 0.95);
  --border: rgba(255, 255, 255, 0.12);
  --shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}
```

---

## Browser Support

### Tested & Supported
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+
- ✅ iOS Safari 14+
- ✅ Android Chrome 90+

### Fallbacks
- `backdrop-filter` → `-webkit-backdrop-filter`
- `background-clip` → `-webkit-background-clip`
- `text-fill-color` → `-webkit-text-fill-color`

---

## Accessibility

### Contrast Ratios
- Text on background: 4.5:1 (AA standard)
- Large text: 3:1 minimum
- Current design: All meet WCAG AA

### Keyboard Navigation
```css
:focus {
  outline: 2px solid rgba(255, 255, 255, 0.3);
  outline-offset: 2px;
}
```

### Color Independence
- Don't rely only on color to convey info
- Use text, icons, borders also

---

## Performance Notes

### Safe to Use
- CSS gradients ✅
- Backdrop filters ✅ (with prefix)
- CSS variables ✅
- Grid/Flexbox ✅
- Border-radius 0 ✅

### Monitor Carefully
- Animations (batch with will-change)
- Shadows (can impact performance)
- Blend modes (test on mobile)

### Avoid
- `filter: drop-shadow()` (expensive)
- Multiple blur effects
- Animation loops on every element
