class IntroSequence {
    constructor() {
        this.canvas = document.getElementById('introCanvas');
        this.init();
    }

    init() {
        if (!this.canvas) return;
        this.prism = new Prism(this.canvas, {
            height: 3.5,
            baseWidth: 5.5,
            animationType: 'rotate',
            timeScale: 0.7,
            scale: 3.5,
            glow: 1.25,
            noise: 0.35,
            hueShift: 0,
            colorFrequency: 1.2,
            bloom: 1.1,
            transparent: true,
            suspendWhenOffscreen: false,
            lightMode: false,
        });

        // Automatically transition after intro, but allow user to click Enter.
        const enter = document.getElementById('enterButton');
        const finishIntro = () => {
            document.body.classList.add('ready');
            const overlay = document.getElementById('introOverlay');
            if (overlay) overlay.style.pointerEvents = 'none';
        };

        if (enter) {
            enter.addEventListener('click', finishIntro);
            enter.addEventListener('keydown', (e) => { if (e.key === 'Enter') finishIntro(); });
        }

        window.setTimeout(() => {
            finishIntro();
        }, 4200);
    }
}

class CortexDashboard {
    constructor() {
        this.stateIndex = 0;
        this.states = ['idle', 'thinking', 'analyzing', 'executing', 'waiting', 'blocked', 'complete'];
        this.canvas = null;
        this.ctx = null;
        this.particles = [];
        this.animationId = null;
        this.init();
    }

    init() {
        this.canvas = document.getElementById('prismCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.bindEvents();
        this.setState('thinking');
        this.buildParticles();
        this.resizeCanvas();
        this.animate();
        this.cycleStates();
    }

    bindEvents() {
        const input = document.getElementById('userInput');
        const button = document.getElementById('sendButton');

        button.addEventListener('click', () => {
            const value = input.value.trim();
            if (!value) return;
            this.executeCommand(value);
            input.value = '';
        });

        input.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') {
                const value = input.value.trim();
                if (!value) return;
                this.executeCommand(value);
                input.value = '';
            }
        });

        document.querySelectorAll('.command-chip').forEach((chip) => {
            chip.addEventListener('click', () => {
                const value = chip.textContent.toLowerCase();
                this.executeCommand(value);
            });
        });

        window.addEventListener('resize', () => this.resizeCanvas());
    }

    cycleStates() {
        setInterval(() => {
            this.stateIndex = (this.stateIndex + 1) % this.states.length;
            this.setState(this.states[this.stateIndex]);
        }, 5200);
    }

    executeCommand(command) {
        const lower = command.toLowerCase();
        const stateMap = {
            'security': 'analyzing',
            'memory': 'thinking',
            'tools': 'executing',
            'governance': 'waiting',
            'analyze': 'analyzing',
            'scan': 'analyzing',
            'evolve': 'executing',
            'approve': 'waiting',
            'blocked': 'blocked'
        };

        const selectedState = Object.entries(stateMap).find(([key]) => lower.includes(key));
        this.setState(selectedState ? selectedState[1] : 'thinking');
    }

    setState(state) {
        document.body.classList.remove('state-idle', 'state-thinking', 'state-analyzing', 'state-executing', 'state-waiting', 'state-blocked', 'state-complete');
        document.body.classList.add(`state-${state}`);
        const statePill = document.getElementById('statePill');
        const labelMap = {
            idle: 'IDLE',
            thinking: 'THINKING',
            analyzing: 'ANALYZING',
            executing: 'EXECUTING',
            waiting: 'WAITING',
            blocked: 'BLOCKED',
            complete: 'COMPLETE'
        };
        if (statePill) statePill.textContent = labelMap[state] || 'THINKING';
    }

    resizeCanvas() {
        const rect = this.canvas.getBoundingClientRect();
        const ratio = window.devicePixelRatio || 1;
        this.canvas.width = rect.width * ratio;
        this.canvas.height = rect.height * ratio;
        this.ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
        this.buildParticles();
    }

    buildParticles() {
        const width = this.canvas.clientWidth || 600;
        const height = this.canvas.clientHeight || 500;
        const count = Math.min(140, Math.max(80, Math.floor(width / 9)));
        this.particles = Array.from({ length: count }, () => ({
            x: Math.random() * width,
            y: Math.random() * height,
            vx: (Math.random() - 0.5) * 0.9,
            vy: (Math.random() - 0.5) * 0.9,
            r: Math.random() * 2.3 + 1.4,
            alpha: Math.random() * 0.8 + 0.2
        }));
    }

    animate() {
        const width = this.canvas.clientWidth;
        const height = this.canvas.clientHeight;
        const cx = width / 2;
        const cy = height / 2;

        const currentState = document.body.className.match(/state-(\w+)/)?.[1] || 'thinking';
        const energy = currentState === 'thinking' ? 1.15 : currentState === 'analyzing' ? 1.6 : currentState === 'executing' ? 1.9 : currentState === 'waiting' ? 0.75 : currentState === 'blocked' ? 0.45 : 0.9;

        this.ctx.clearRect(0, 0, width, height);

        this.particles.forEach((particle, index) => {
            const dx = cx - particle.x;
            const dy = cy - particle.y;
            const angle = Math.atan2(dy, dx);
            const dist = Math.hypot(dx, dy) || 1;
            const targetVx = (Math.cos(angle) * 0.9) / Math.max(1, dist / 90) + (Math.random() - 0.5) * 0.28;
            const targetVy = (Math.sin(angle) * 0.9) / Math.max(1, dist / 90) + (Math.random() - 0.5) * 0.28;

            particle.vx += (targetVx - particle.vx) * 0.03 * energy;
            particle.vy += (targetVy - particle.vy) * 0.03 * energy;
            particle.x += particle.vx * 1.8;
            particle.y += particle.vy * 1.8;

            if (particle.x < 0 || particle.x > width) particle.vx *= -1;
            if (particle.y < 0 || particle.y > height) particle.vy *= -1;

            this.ctx.beginPath();
            this.ctx.fillStyle = `rgba(196, 208, 255, ${particle.alpha})`;
            this.ctx.arc(particle.x, particle.y, particle.r, 0, Math.PI * 2);
            this.ctx.fill();

            for (let j = index + 1; j < this.particles.length; j++) {
                const other = this.particles[j];
                const dx2 = particle.x - other.x;
                const dy2 = particle.y - other.y;
                const d = Math.hypot(dx2, dy2);
                if (d < 80) {
                    this.ctx.beginPath();
                    this.ctx.strokeStyle = `rgba(139, 92, 246, ${0.08 + (1 - d / 80) * 0.42})`;
                    this.ctx.lineWidth = 1;
                    this.ctx.moveTo(particle.x, particle.y);
                    this.ctx.lineTo(other.x, other.y);
                    this.ctx.stroke();
                }
            }
        });

        this.drawPrism(cx, cy, currentState);
        this.animationId = requestAnimationFrame(() => this.animate());
    }

    drawPrism(cx, cy, state) {
        const time = performance.now() * 0.001;
        const hue = state === 'blocked' ? '#ff5d73' : state === 'waiting' ? '#f5b942' : '#8b5cf6';
        const glow = state === 'blocked' ? 0.9 : state === 'waiting' ? 0.7 : 1.2;
        const baseSize = Math.min(this.canvas.clientWidth, this.canvas.clientHeight) * 0.22;

        this.ctx.save();
        this.ctx.translate(cx, cy);
        this.ctx.rotate(time * (state === 'executing' ? 0.9 : 0.45));

        for (let i = 0; i < 3; i++) {
            this.ctx.beginPath();
            this.ctx.moveTo(0, -baseSize * 0.92);
            this.ctx.lineTo(baseSize * (0.72 - i * 0.12), baseSize * (0.42 + i * 0.18));
            this.ctx.lineTo(-baseSize * (0.72 - i * 0.12), baseSize * (0.42 + i * 0.18));
            this.ctx.closePath();
            this.ctx.strokeStyle = `rgba(255,255,255,${0.15 + i * 0.1})`;
            this.ctx.lineWidth = 1.2;
            this.ctx.stroke();
        }

        const gradient = this.ctx.createLinearGradient(-baseSize, -baseSize, baseSize, baseSize);
        gradient.addColorStop(0, 'rgba(255, 255, 255, 0.95)');
        gradient.addColorStop(0.25, hue);
        gradient.addColorStop(0.6, '#ddd4ff');
        gradient.addColorStop(1, 'rgba(139, 92, 246, 0.7)');

        this.ctx.beginPath();
        this.ctx.moveTo(0, -baseSize * 0.96);
        this.ctx.lineTo(baseSize * 0.85, baseSize * 0.5);
        this.ctx.lineTo(0, baseSize * 1.08);
        this.ctx.lineTo(-baseSize * 0.85, baseSize * 0.5);
        this.ctx.closePath();
        this.ctx.fillStyle = `rgba(139, 92, 246, ${0.1 + glow * 0.1})`;
        this.ctx.fill();
        this.ctx.strokeStyle = gradient;
        this.ctx.lineWidth = 2.5;
        this.ctx.shadowBlur = 24 * glow;
        this.ctx.shadowColor = hue;
        this.ctx.stroke();
        this.ctx.shadowBlur = 0;

        const rayCount = state === 'executing' ? 12 : state === 'thinking' ? 7 : 5;
        for (let i = 0; i < rayCount; i++) {
            const angle = (Math.PI * 2 * i) / rayCount + time * 0.5;
            const startR = baseSize * 0.8;
            const endR = baseSize * (1.38 + Math.sin(time * 2 + i) * 0.18);
            this.ctx.beginPath();
            this.ctx.moveTo(Math.cos(angle) * startR, Math.sin(angle) * startR);
            this.ctx.lineTo(Math.cos(angle) * endR, Math.sin(angle) * endR);
            this.ctx.strokeStyle = `rgba(255,255,255,${0.22 + i / rayCount * 0.4})`;
            this.ctx.lineWidth = 1.2;
            this.ctx.stroke();
        }

        this.ctx.restore();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new IntroSequence();
    new CortexDashboard();
});
