# Quick Start - Performance Tuning Guide

## 🎯 Tuning Rápido por Cenário

### Cenário 1: Site muito lento no desktop
**Problema**: FPS baixo mesmo em desktop

**Solução** (animation.js, linha ~25):
```javascript
// Aumentar pixel ratio
renderer.setPixelRatio(isMobile ? 1 : 2);  // era 1.5

// Aumentar detalhes
const somaGeo = new THREE.IcosahedronGeometry(somaRadius, 16);  // era 12

// Aumentar partículas
const dustA = makeParticles(800, ...);  // era 600
```

---

### Cenário 2: Mobile travando/quente
**Problema**: Performance ruim em celulares

**Solução** (animation.js):
```javascript
// Reduzir mais ainda
const dustA = makeParticles(isMobile ? 100 : 600, ...);  // era 300
const dustB = makeParticles(isMobile ? 50 : 200, ...);   // era 100
const dustC = makeParticles(isMobile ? 10 : 60, ...);    // era 30

// Reduzir geometria
const geo = new THREE.TubeGeometry(curve, Math.floor(curve.getLength() * 1), ...);  // era 2

// Desativar completamente bloom
bloomPass.threshold = 999;  // Sempre desativa
```

---

### Cenário 3: Cores não estão corretas
**Problema**: Azul ainda aparecendo, texto colorido errado

**Verificar** (styles.css):
```css
:root {
  --cyan: #ffffff;        /* Deve ser branco */
  --teal: rgba(230, 240, 255, 0.95);  /* Soft blue */
  --border: rgba(255, 255, 255, 0.12);  /* Branco com transparência */
}

/* Verificar se h4 está preto */
.card-body h4 { 
  color: #000000;  /* Deve ser preto */
}
```

**Solução**: Limpar cache do navegador (Ctrl+Shift+Delete)

---

### Cenário 4: Textura nos títulos muito forte/fraca
**Problema**: Grão de papel craft invisível ou muito óbvio

**Ajuste** (styles.css, ~1250):
```css
/* MAIS FORTE - aumentar opacidade */
background-image: 
  repeating-linear-gradient(45deg, transparent, transparent 2px, rgba(0, 0, 0, 0.05) 2px, rgba(0, 0, 0, 0.05) 4px),
  /* ↑ era 0.02, agora 0.05 */
```

```css
/* MAIS FRACA - diminuir opacidade */
background-image: 
  repeating-linear-gradient(45deg, transparent, transparent 2px, rgba(0, 0, 0, 0.01) 2px, rgba(0, 0, 0, 0.01) 4px),
  /* ↑ era 0.02, agora 0.01 */
```

---

### Cenário 5: Glass morphism muito/pouco transparente
**Problema**: Painéis vidrosos demais opacos

**Ajuste** (styles.css):
```css
/* Mais transparente */
background: rgba(255, 255, 255, 0.03);  /* era 0.05-0.12 */

/* Menos transparente (mais opaco) */
background: rgba(255, 255, 255, 0.15);  /* era 0.05-0.12 */

/* Ajustar blur */
backdrop-filter: blur(24px) saturate(140%);  /* aumentar/diminuir 24px */
```

---

## 🔍 Debug Checklist

### Performance
```javascript
// No console do navegador
console.time('frame');
// ... seu código
console.timeEnd('frame');  // Mostra tempo em ms

// Ver FPS
let lastTime = performance.now();
let frameCount = 0;
function fpsCounter() {
  frameCount++;
  const currentTime = performance.now();
  if (currentTime - lastTime >= 1000) {
    console.log('FPS:', frameCount);
    frameCount = 0;
    lastTime = currentTime;
  }
  requestAnimationFrame(fpsCounter);
}
fpsCounter();
```

### Cores
```javascript
// Verificar se mobile foi detectado
console.log('isMobile:', isMobile);

// Verificar variáveis CSS
const styles = getComputedStyle(document.documentElement);
console.log('--cyan:', styles.getPropertyValue('--cyan'));
console.log('--border:', styles.getPropertyValue('--border'));
```

### Texturas
```javascript
// Inspecionar elemento
document.querySelector('h1').style.backgroundImage  // Deve mostrar gradients

// Temporariamente remover textura
document.querySelector('h1').style.backgroundImage = 'none';
```

---

## 📱 Teste em Diferentes Dispositivos

### Chrome DevTools Throttling
1. Abrir DevTools (F12)
2. Performance > Capture > Simulated throttling
3. Testar com: "Slow 4G" ou "Fast 3G"

### Teste Real em Mobile
```bash
# Iniciar servidor local
python3 -m http.server 8000 --directory portfolio-frontend

# Acessar do celular na mesma rede
# http://<seu-ip-local>:8000
```

---

## 🔧 Variáveis de Ambiente (Animation.js)

Adicione no topo para debugging:

```javascript
// VIPE Debug Mode
const VIPE_DEBUG = false;  // Mude para true
const VIPE_LOG_FRAMES = false;  // Log FPS a cada frame
const FORCE_DESKTOP = false;  // Forçar desktop mesmo em mobile
const FORCE_MOBILE = false;   // Forçar mobile mesmo em desktop

if (VIPE_DEBUG) {
  console.log('🔧 VIPE Debug Mode ENABLED');
  console.log('isMobile:', isMobile);
  console.log('devicePixelRatio:', window.devicePixelRatio);
  console.log('viewport:', window.innerWidth + 'x' + window.innerHeight);
}
```

---

## ⚡ Performance Targets

### Desktop
- FCP: < 2s
- LCP: < 2.5s
- TTI: < 3.5s
- FPS: 60 (estável)
- Memory: < 150MB

### Mobile (4G)
- FCP: < 3s
- LCP: < 3.5s
- TTI: < 5s
- FPS: 30-45 (aceitável)
- Memory: < 100MB

### Mobile (3G)
- FCP: < 4s
- LCP: < 5s
- TTI: < 7s
- FPS: 20-30 (básico)
- Memory: < 80MB

---

## 🚨 Problemas Comuns & Soluções

### "Site piscando/flickering"
✅ Solução: Cache buster na URL
```html
<!-- Adicionar timestamp -->
<link rel="stylesheet" href="./css/styles.css?v=20240714">
```

### "Cores azuis ainda aparecem"
✅ Solução: Limpar cache + hard refresh
- Windows/Linux: Ctrl+Shift+R
- Mac: Cmd+Shift+R

### "Mobile não carregando"
✅ Solução: Verificar console para erros
- DevTools > Console
- Procurar por erros em vermelho

### "Texturas muito pixeladas"
✅ Solução: Verificar zoom do navegador
- Zoom deve estar em 100%
- DevTools > Settings > zoom

### "Glass effect não funciona no Safari"
✅ Solução: Usar prefixos WebKit
```css
-webkit-backdrop-filter: blur(20px) saturate(140%);
backdrop-filter: blur(20px) saturate(140%);
```

---

## 📊 Monitorar em Produção

### Google Lighthouse (CI/CD)
```bash
npm install -g lighthouse
lighthouse https://seu-site.com --headless
```

### Web Vitals Real
```javascript
// Adicionar ao main.js
web-vitals.getCLS(console.log);
web-vitals.getFID(console.log);
web-vitals.getFCP(console.log);
web-vitals.getLCP(console.log);
web-vitals.getTTFB(console.log);
```

### Analytics Custom
```javascript
// Trackear eventos
if (window.gtag) {
  gtag('event', 'page_load', {
    'fcp': fcp,
    'lcp': lcp,
    'is_mobile': isMobile
  });
}
```

---

## 🎯 Benchmark Local

```bash
#!/bin/bash
# benchmark.sh

echo "🚀 Performance Benchmark"
echo "========================"

# 1. Bundle size
echo "📦 Bundle Size:"
ls -lh portfolio-frontend/css/styles.css
ls -lh portfolio-frontend/js/animation.js

# 2. Lighthouse local
echo "📊 Running Lighthouse..."
lighthouse http://localhost:8000 --headless --output=json > lighthouse.json

# 3. Parse results
echo "✅ Results saved to lighthouse.json"
```

---

**Dica**: Sempre testar mudanças em 3 cenários:
1. Desktop Chrome (baseline)
2. Mobile Chrome (throttled 4G)
3. Safari (compatibilidade)
