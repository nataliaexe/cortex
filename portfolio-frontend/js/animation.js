import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';

const container = document.getElementById('hero-canvas');
if (!container) throw new Error('Hero canvas container not found');

const isMobile = /iPhone|iPad|Android|webOS/i.test(navigator.userAgent);

const cursorEl = document.getElementById('cursor');
document.addEventListener('mousemove', (event) => {
  cursorEl.style.left = event.clientX + 'px';
  cursorEl.style.top = event.clientY + 'px';
});

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x00000a);
scene.fog = new THREE.FogExp2(0x00000f, 0.022);

const camera = new THREE.PerspectiveCamera(52, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(0, 8, 45);

const renderer = new THREE.WebGLRenderer({ antialias: false, powerPreference: 'high-performance' });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(isMobile ? 1 : Math.min(window.devicePixelRatio, 1.5));
container.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.04;
controls.autoRotate = true;
controls.autoRotateSpeed = 0.7;
controls.enablePan = false;
controls.maxDistance = 80;

const renderScene = new RenderPass(scene, camera);
const bloomPass = new UnrealBloomPass(new THREE.Vector2(window.innerWidth, window.innerHeight), 1.2, 0.3, 0.7);
bloomPass.threshold = isMobile ? 999 : 1.0;
bloomPass.strength = isMobile ? 0 : 1.2;
bloomPass.radius = 0.6;

const composer = new EffectComposer(renderer);
composer.addPass(renderScene);
if (!isMobile) composer.addPass(bloomPass);

const vertexShader = `
  attribute float aIsInput;
  varying vec2 vUv;
  varying vec3 vWorldPos;
  varying vec3 vNormal;
  varying float vIsInput;
  varying float vDist;

  void main() {
    vUv = uv;
    vIsInput = aIsInput;
    vec4 worldPos = modelMatrix * vec4(position, 1.0);
    vWorldPos = worldPos.xyz;
    vDist = length(worldPos.xyz);
    vNormal = normalize(normalMatrix * normal);
    gl_Position = projectionMatrix * viewMatrix * worldPos;
  }
`;

const fragmentShader = `
  uniform float uTime;
  uniform float uPulseProgress;
  uniform float uActivation;
  uniform vec3 uCameraPos;

  varying vec2 vUv;
  varying vec3 vWorldPos;
  varying vec3 vNormal;
  varying float vIsInput;
  varying float vDist;

  float hash(vec3 p) {
    p = fract(p * 0.3183099 + .1);
    p *= 17.0;
    return fract(p.x * p.y * p.z * (p.x + p.y + p.z));
  }
  float noise(vec3 x) {
    vec3 i = floor(x);
    vec3 f = fract(x);
    f = f * f * (3.0 - 2.0 * f);
    return mix(
      mix(mix(hash(i + vec3(0,0,0)), hash(i + vec3(1,0,0)), f.x),
          mix(hash(i + vec3(0,1,0)), hash(i + vec3(1,1,0)), f.x), f.y),
      mix(mix(hash(i + vec3(0,0,1)), hash(i + vec3(1,0,1)), f.x),
          mix(hash(i + vec3(0,1,1)), hash(i + vec3(1,1,1)), f.x), f.y), f.z);
  }
  vec3 palette(float t, vec3 a, vec3 b, vec3 c, vec3 d) {
    return a + b * cos(6.28318 * (c * t + d));
  }

  void main() {
    vec3 viewDir = normalize(uCameraPos - vWorldPos);
    float fresnel = pow(1.0 - max(dot(vNormal, viewDir), 0.0), 3.0);
    float n1 = noise(vWorldPos * 0.5 + uTime * 0.2);
    float n2 = noise(vWorldPos * 2.0 - uTime * 0.5);

    vec3 baseColor = vec3(0.01, 0.018, 0.03) + (vec3(0.08, 0.22, 0.28) * fresnel * n1);
    baseColor *= (0.5 + 0.5 * n2);

    vec3 pulseColor = vec3(0.0);
    if (vIsInput > 0.5 && uPulseProgress > -5.0) {
      float pDist = abs(vDist - uPulseProgress);
      float core = exp(-pDist * pDist * 3.0);
      float trail = smoothstep(6.0, 0.0, vDist - uPulseProgress) * smoothstep(-2.0, 0.0, uPulseProgress - vDist);
      float pi = max(core * 3.0, trail * 1.5);
      pulseColor = vec3(3.5, 1.0, 0.1) * pi * (0.8 + 0.2 * n2);
    }

    vec3 actColor = vec3(0.0);
    if (uActivation > 0.0) {
      float distFromWave = vDist - uActivation;
      float waveFront = exp(-pow(distFromWave, 2.0) * 0.2) * step(0.0, -distFromWave);
      float residual = smoothstep(uActivation, uActivation - 25.0, vDist);
      float actIntensity = waveFront * 4.0 + residual * 1.5;
      actIntensity *= (0.6 + 0.4 * noise(vWorldPos * 1.5 - uTime * 2.0));

      vec3 dir = normalize(vWorldPos);
      float angle = atan(dir.z, dir.x);
      vec3 rainbow = palette(
        angle * 0.15 + vDist * 0.05 - uTime * 0.5,
        vec3(0.5,0.5,0.5), vec3(0.5,0.5,0.5),
        vec3(1.0,1.0,1.0), vec3(0.00,0.33,0.67)
      );
      actColor = rainbow * actIntensity * 1.5;
      if (vDist < 4.0) {
        float somaFlash = exp(-pow(uActivation * 0.2, 2.0)) * 2.5;
        actColor += vec3(1.0, 0.9, 0.8) * somaFlash;
      }
    }

    gl_FragColor = vec4(baseColor + pulseColor + actColor, 1.0);
  }
`;

const material = new THREE.ShaderMaterial({
  vertexShader,
  fragmentShader,
  uniforms: {
    uTime: { value: 0 },
    uPulseProgress: { value: -10.0 },
    uActivation: { value: 0 },
    uCameraPos: { value: new THREE.Vector3() }
  },
  transparent: false,
  depthWrite: true,
  side: THREE.FrontSide
});

const structureGroup = new THREE.Group();
scene.add(structureGroup);

function createWanderingPath(start, dir, length, segments, jitterScale, endPoint) {
  const pts = [start.clone()];
  let curr = start.clone();
  let cDir = dir.clone().normalize();
  for (let i = 0; i < segments; i++) {
    cDir.x += (Math.random() - 0.5) * jitterScale;
    cDir.y += (Math.random() - 0.5) * jitterScale;
    cDir.z += (Math.random() - 0.5) * jitterScale;
    cDir.normalize();
    curr = curr.clone().add(cDir.clone().multiplyScalar(length / segments));
    pts.push(curr);
  }
  if (endPoint) {
    const approach = endPoint.clone().add(new THREE.Vector3(-1.5, 0, 0));
    pts[pts.length - 1] = approach;
    pts.push(endPoint.clone());
  }
  return new THREE.CatmullRomCurve3(pts);
}

function taperGeometry(geo, baseRadius, isInput) {
  const pos = geo.attributes.position;
  const norm = geo.attributes.normal;
  const uv = geo.attributes.uv;
  for (let i = 0; i < pos.count; i++) {
    const u = uv.getX(i);
    const t = isInput ? 1.0 : (1.0 - u);
    const taper = Math.pow(t, 0.6);
    const shrink = baseRadius * (1.0 - taper);
    pos.setXYZ(i,
      pos.getX(i) - norm.getX(i) * shrink,
      pos.getY(i) - norm.getY(i) * shrink,
      pos.getZ(i) - norm.getZ(i) * shrink
    );
  }
  geo.computeVertexNormals();
}

function addBranch(curve, radius, isInput) {
  const geo = new THREE.TubeGeometry(curve, Math.floor(curve.getLength() * 2), radius, isMobile ? 6 : 10, false);
  taperGeometry(geo, radius, isInput);
  const arr = new Float32Array(geo.attributes.position.count).fill(isInput ? 1.0 : 0.0);
  geo.setAttribute('aIsInput', new THREE.BufferAttribute(arr, 1));
  structureGroup.add(new THREE.Mesh(geo, material));
  return { curve };
}

const somaRadius = 3.3;
const somaGeo = new THREE.IcosahedronGeometry(somaRadius, isMobile ? 8 : 12);
const pos = somaGeo.attributes.position;
for (let i = 0; i < pos.count; i++) {
  const v = new THREE.Vector3().fromBufferAttribute(pos, i);
  let n = Math.sin(v.x * 2) * Math.cos(v.y * 2) * Math.sin(v.z * 2) * 0.5 + Math.sin(v.x * 5 + v.y * 3) * 0.2;
  v.add(v.clone().normalize().multiplyScalar(n));
  pos.setXYZ(i, v.x, v.y, v.z);
}
somaGeo.computeVertexNormals();
const somaIsInput = new Float32Array(pos.count).fill(0.0);
somaGeo.setAttribute('aIsInput', new THREE.BufferAttribute(somaIsInput, 1));
structureGroup.add(new THREE.Mesh(somaGeo, material));

const inputCurve = createWanderingPath(
  new THREE.Vector3(-45, 0, 0), new THREE.Vector3(1, 0, 0), 46, 30, 0.05,
  new THREE.Vector3(-somaRadius * 0.1, 0, 0)
);
addBranch(inputCurve, 0.6, true);

for (let i = 0; i < 18; i++) {
  const phi = Math.random() * Math.PI * 2;
  const theta = Math.acos(Math.random() * 2 - 1);
  let startPhi = phi;
  if (Math.cos(startPhi) * Math.sin(theta) < -0.3) {
    startPhi = startPhi > Math.PI ? startPhi - Math.PI : startPhi + Math.PI;
  }

  const startDir = new THREE.Vector3(
    Math.cos(startPhi) * Math.sin(theta),
    Math.sin(startPhi) * Math.sin(theta),
    Math.cos(theta)
  );
  const start = startDir.clone().multiplyScalar(somaRadius * 0.8);
  const length = 20 + Math.random() * 30;
  const mainRadius = 0.4 + Math.random() * 0.3;
  const { curve: mainCurve } = addBranch(
    createWanderingPath(start, startDir, length, 25, 0.4),
    mainRadius, false
  );

  const numSec = Math.floor(Math.random() * 4) + 2;
  for (let j = 0; j < numSec; j++) {
    const t = 0.2 + Math.random() * 0.6;
    const bStart = mainCurve.getPoint(t);
    const tangent = mainCurve.getTangent(t);
    const rv = new THREE.Vector3(Math.random() - 0.5, Math.random() - 0.5, Math.random() - 0.5).normalize();
    const bDir = tangent.clone().cross(rv).normalize().add(tangent.multiplyScalar(0.5)).normalize();
    addBranch(
      createWanderingPath(bStart, bDir, (1 - t) * length * (0.4 + Math.random() * 0.4), 15, 0.6),
      mainRadius * (1 - t) * 0.8, false
    );
  }
}

function makeParticles(count, spread, colorHex, size, opacity) {
  const geo = new THREE.BufferGeometry();
  const posArray = new Float32Array(count * 3);
  for (let i = 0; i < count * 3; i++) posArray[i] = (Math.random() - 0.5) * spread;
  geo.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
  const mat = new THREE.PointsMaterial({
    color: colorHex,
    size,
    transparent: true,
    opacity,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    sizeAttenuation: true
  });
  return new THREE.Points(geo, mat);
}

const dustA = makeParticles(isMobile ? 300 : 600, 120, 0x224466, 0.08, 0.2);
const dustB = makeParticles(isMobile ? 100 : 200, 90, 0x003355, 0.16, 0.15);
const dustC = makeParticles(isMobile ? 30 : 60, 60, 0x00aacc, 0.30, 0.1);
scene.add(dustA, dustB, dustC);

const elMv = document.getElementById('tele-mv');
const elProp = document.getElementById('tele-prop');
const elSignal = document.getElementById('bar-signal');
const elAxon = document.getElementById('bar-axon');
const elStatus = document.getElementById('status-msg');
const elDot = document.getElementById('status-dot');
const elPanel = document.getElementById('ui-panel');
if (elPanel) elPanel.style.display = 'none';
const elCoords = document.getElementById('coords');
if (elCoords) elCoords.style.display = 'none';

let state = 0;
let pulseProg = -10.0;
let actProg = 0.0;
const INPUT_LENGTH = 45.0;

let mvBase = -70.0;
let mvTarget = -70.0;

window.addEventListener('click', () => {
  if (state !== 0) return;
  state = 1;
  pulseProg = INPUT_LENGTH;
  actProg = 0.0;
  material.uniforms.uActivation.value = 0.0;
  if (elPanel) elPanel.style.opacity = '0';
  document.body.classList.add('active');
  setTimeout(() => document.body.classList.remove('active'), 300);
  mvTarget = 40.0;
});

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
  composer.setSize(window.innerWidth, window.innerHeight);
});

const clock = new THREE.Clock();
let frameCount = 0;

function animate() {
  requestAnimationFrame(animate);
  const delta = clock.getDelta();
  frameCount += 1;

  controls.update();

  dustA.rotation.y += delta * 0.008;
  dustA.rotation.x += delta * 0.003;
  dustB.rotation.y -= delta * 0.005;
  dustB.rotation.z += delta * 0.002;
  dustC.rotation.y += delta * 0.015;

  material.uniforms.uTime.value += delta;
  material.uniforms.uCameraPos.value.copy(camera.position);

  mvBase += (Math.random() - 0.5) * 0.4;
  mvBase = Math.max(-80, Math.min(-55, mvBase));
  mvTarget += (mvBase - mvTarget) * 0.05;

  if (state === 1) {
    pulseProg -= delta * 35.0;
    material.uniforms.uPulseProgress.value = pulseProg;
    mvTarget = 40.0 * (1.0 - pulseProg / INPUT_LENGTH);

    if (pulseProg <= 2.0) {
      state = 2;
      pulseProg = -10.0;
      material.uniforms.uPulseProgress.value = -10.0;
      actProg = 0.0;
      camera.position.y += 0.5;
    }
  } else if (state === 2) {
    actProg += delta * 20.0;
    material.uniforms.uActivation.value = actProg;

    if (actProg > 75.0) {
      state = 0;
      material.uniforms.uActivation.value = 0.0;
      mvTarget = -70.0;
      if (elStatus) {
        elStatus.textContent = '▸ RETRIGGER AVAILABLE';
        elStatus.className = 'status-line ready';
      }
      if (elDot) {
        elDot.style.background = '#00ffc8';
        elDot.style.boxShadow = '0 0 6px #00ffc8';
      }
      if (elPanel) elPanel.style.opacity = '1';
    }
  }

  if (frameCount % 6 === 0) {
    const mv = state === 0 ? mvBase : mvTarget;
    if (elMv) {
      elMv.textContent = (mv >= 0 ? '+' : '') + mv.toFixed(1) + ' mV';
      elMv.className = 'tele-val' + (mv > 0 ? ' alert' : '');
    }

    if (state === 0) {
      if (elProp) {
        elProp.textContent = 'STANDBY';
        elProp.className = 'tele-val';
      }
      if (elStatus) {
        elStatus.textContent = '▸ AWAITING STIMULUS';
        elStatus.className = 'status-line idle';
      }
      if (elSignal) elSignal.style.width = (6 + Math.random() * 4) + '%';
      if (elDot) {
        elDot.style.background = '#00ffc8';
        elDot.style.boxShadow = '0 0 6px #00ffc8';
      }
    } else if (state === 1) {
      const pct = Math.max(0, Math.min(100, (1 - pulseProg / INPUT_LENGTH) * 100));
      if (elProp) {
        elProp.textContent = 'PROPAGATING';
        elProp.className = 'tele-val alert';
      }
      if (elStatus) {
        elStatus.textContent = '▸ SIGNAL INCOMING';
        elStatus.className = 'status-line firing';
      }
      if (elSignal) {
        elSignal.style.width = pct + '%';
        elSignal.style.background = 'linear-gradient(90deg, rgba(255,80,0,0.6), rgba(255,200,0,0.9))';
      }
      if (elDot) {
        elDot.style.background = '#ff6000';
        elDot.style.boxShadow = '0 0 8px #ff4000';
      }
    } else if (state === 2) {
      const pct = Math.min(100, actProg / 75 * 100);
      if (elProp) {
        elProp.textContent = 'FIRING';
        elProp.className = 'tele-val active';
      }
      if (elStatus) {
        elStatus.textContent = '▸ ACTION POTENTIAL';
        elStatus.className = 'status-line firing';
      }
      if (elSignal) {
        elSignal.style.width = (100 - pct * 0.7) + '%';
        elSignal.style.background = 'linear-gradient(90deg, rgba(0,255,120,0.6), rgba(0,200,255,0.9))';
      }
      if (elAxon) elAxon.style.width = Math.max(0, 100 - pct) + '%';
      if (elDot) {
        elDot.style.background = '#ff00aa';
        elDot.style.boxShadow = '0 0 10px #ff00aa';
      }
    }
  }

  if (frameCount % 10 === 0) {
    if (elCoords) {
      const coordX = document.getElementById('coord-x');
      const coordY = document.getElementById('coord-y');
      const coordZ = document.getElementById('coord-z');
      if (coordX) coordX.textContent = 'X: ' + camera.position.x.toFixed(3);
      if (coordY) coordY.textContent = 'Y: ' + camera.position.y.toFixed(3);
      if (coordZ) coordZ.textContent = 'Z: ' + camera.position.z.toFixed(3);
    }
  }

  composer.render();
}

animate();