class Prism {
  constructor(canvas, options = {}) {
    if (!canvas || !canvas.getContext) {
      return;
    }

    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.options = {
      height: 3.5,
      baseWidth: 5.5,
      animationType: 'rotate',
      glow: 1,
      offset: { x: 0, y: 0 },
      noise: 0.5,
      transparent: true,
      scale: 3.6,
      hueShift: 0,
      colorFrequency: 1,
      hoverStrength: 2,
      inertia: 0.05,
      bloom: 1,
      suspendWhenOffscreen: false,
      timeScale: 0.5,
      lightMode: false,
      ...options,
    };

    this.particles = [];
    this.startTime = performance.now();
    this.animationId = null;
    this.destroyed = false;
    this.bindResize();
    this.buildParticles();
    this.animate = this.animate.bind(this);
    this.animate(this.startTime);
  }

  bindResize() {
    this.resize = () => {
      const ratio = window.devicePixelRatio || 1;
      const rect = this.canvas.getBoundingClientRect();
      this.canvas.width = Math.max(1, Math.floor(rect.width * ratio));
      this.canvas.height = Math.max(1, Math.floor(rect.height * ratio));
      this.ctx.setTransform(1, 0, 0, 1, 0, 0);
      this.ctx.scale(ratio, ratio);
      this.buildParticles();
    };

    this.resize();
    window.addEventListener('resize', this.resize);
  }

  buildParticles() {
    const width = this.canvas.clientWidth || 1;
    const height = this.canvas.clientHeight || 1;
    const count = 110;
    this.particles = Array.from({ length: count }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.9,
      vy: (Math.random() - 0.5) * 0.9,
      r: Math.random() * 2.1 + 1.0,
      alpha: Math.random() * 0.8 + 0.18,
    }));
  }

  animate(now) {
    if (this.destroyed) return;

    const width = this.canvas.clientWidth || 1;
    const height = this.canvas.clientHeight || 1;
    const cx = width / 2;
    const cy = height / 2;
    const elapsed = (now - this.startTime) / 1000;
    const t = elapsed * this.options.timeScale;

    this.ctx.clearRect(0, 0, width, height);
    this.ctx.fillStyle = this.options.transparent ? 'rgba(0, 0, 0, 0)' : '#000000';
    this.ctx.fillRect(0, 0, width, height);

    this.particles.forEach((particle) => {
      const dx = cx - particle.x;
      const dy = cy - particle.y;
      const dist = Math.hypot(dx, dy) || 1;
      const pull = Math.max(0, 1 - dist / 430);

      particle.vx += (dx / dist) * (0.05 + pull * 0.1);
      particle.vy += (dy / dist) * (0.05 + pull * 0.1);
      particle.vx *= 0.96;
      particle.vy *= 0.96;

      particle.x += particle.vx + Math.sin(t + particle.x * 0.04) * 0.15;
      particle.y += particle.vy + Math.cos(t + particle.y * 0.04) * 0.15;

      if (particle.x < 0 || particle.x > width) particle.vx *= -0.8;
      if (particle.y < 0 || particle.y > height) particle.vy *= -0.8;

      const glow = 0.4 + (Math.sin(t * 2 + particle.x * 0.1) + 1) * 0.3;
      this.ctx.beginPath();
      this.ctx.fillStyle = `rgba(255,255,255,${particle.alpha * glow})`;
      this.ctx.arc(particle.x, particle.y, particle.r, 0, Math.PI * 2);
      this.ctx.fill();
    });

    this.drawPrism(cx, cy, width, height, t, elapsed);
    this.animationId = requestAnimationFrame(this.animate);
  }

  drawPrism(cx, cy, width, height, t, elapsed) {
    const baseSize = Math.min(width, height) * (0.14 + Math.min(1, Math.max(0, (t - 0.2) / 2.5)) * 0.18);
    const rotation = elapsed * (0.75 + Math.min(1, Math.max(0, t / 4)) * 1.2);

    this.ctx.save();
    this.ctx.translate(cx, cy);
    this.ctx.rotate(rotation);

    for (let i = 0; i < 3; i++) {
      this.ctx.beginPath();
      this.ctx.moveTo(0, -baseSize * 0.92);
      this.ctx.lineTo(baseSize * (0.72 - i * 0.1), baseSize * (0.42 + i * 0.18));
      this.ctx.lineTo(-baseSize * (0.72 - i * 0.1), baseSize * (0.42 + i * 0.18));
      this.ctx.closePath();
      this.ctx.strokeStyle = `rgba(255,255,255,${0.08 + i * 0.12})`;
      this.ctx.lineWidth = 1.2;
      this.ctx.stroke();
    }

    const gradient = this.ctx.createLinearGradient(-baseSize, -baseSize, baseSize, baseSize);
    gradient.addColorStop(0, 'rgba(255,255,255,0.95)');
    gradient.addColorStop(0.22, 'rgba(139,92,246,0.9)');
    gradient.addColorStop(0.68, 'rgba(255,255,255,0.78)');
    gradient.addColorStop(1, 'rgba(139,92,246,0.82)');

    this.ctx.beginPath();
    this.ctx.moveTo(0, -baseSize * 0.96);
    this.ctx.lineTo(baseSize * 0.82, baseSize * 0.52);
    this.ctx.lineTo(0, baseSize * 1.08);
    this.ctx.lineTo(-baseSize * 0.82, baseSize * 0.52);
    this.ctx.closePath();
    this.ctx.fillStyle = 'rgba(139,92,246,0.14)';
    this.ctx.fill();
    this.ctx.strokeStyle = gradient;
    this.ctx.lineWidth = 2.2;
    this.ctx.shadowBlur = 22;
    this.ctx.shadowColor = '#8b5cf6';
    this.ctx.stroke();
    this.ctx.shadowBlur = 0;

    const rays = 8;
    for (let i = 0; i < rays; i++) {
      const angle = (Math.PI * 2 * i) / rays + rotation * 0.8;
      const startR = baseSize * 0.72;
      const endR = baseSize * (1.18 + Math.sin(t * 2 + i) * 0.18);
      this.ctx.beginPath();
      this.ctx.moveTo(Math.cos(angle) * startR, Math.sin(angle) * startR);
      this.ctx.lineTo(Math.cos(angle) * endR, Math.sin(angle) * endR);
      this.ctx.strokeStyle = `rgba(255,255,255,${0.22 + (i / rays) * 0.35})`;
      this.ctx.lineWidth = 1.1;
      this.ctx.stroke();
    }

    this.ctx.restore();
  }

  destroy() {
    this.destroyed = true;
    if (this.animationId) cancelAnimationFrame(this.animationId);
    window.removeEventListener('resize', this.resize);
  }
}

window.Prism = Prism;
