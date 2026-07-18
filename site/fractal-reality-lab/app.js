'use strict';

const $ = (selector) => document.querySelector(selector);
const clamp = (value, min = 0, max = 1) => Math.min(max, Math.max(min, value));
const pct = (value) => `${Math.round(value * 100)}%`;
const labelize = (value) => value.replaceAll('_', ' ').replace(/\b\w/g, (m) => m.toUpperCase());

const analogues = {
  neuron_branching: { label: 'Neuron branching', layer: 'structural_analogy', mechanism: 'Recursive branching and transport constraints, not Mandelbrot iteration.', features: [.72,.18,.24,.70,.30,.62,.51,.73,.48], draw: 'neuron' },
  lightning: { label: 'Lightning channel', layer: 'structural_analogy', mechanism: 'Dielectric breakdown and branching instability.', features: [.14,.81,.09,.82,.20,.79,.91,.68,.78], draw: 'lightning' },
  river_delta: { label: 'River delta', layer: 'structural_analogy', mechanism: 'Erosion, sediment transport, and flow optimization.', features: [.68,.26,.18,.66,.33,.58,.47,.61,.42], draw: 'river' },
  tree: { label: 'Tree branching', layer: 'structural_analogy', mechanism: 'Growth, resource transport, and mechanical loading.', features: [.83,.10,.36,.59,.45,.44,.35,.67,.34], draw: 'tree' },
  optical_caustic: { label: 'Coffee-cup optical caustic', layer: 'demonstrated_connection', mechanism: 'Ray-envelope geometry produces a caustic; resemblance to the Mandelbrot cardioid is limited.', features: [.92,.05,.76,.31,.76,.19,.21,.88,.24], draw: 'caustic' },
  cardioid_microphone: { label: 'Cardioid microphone response', layer: 'demonstrated_connection', mechanism: 'Polar response r(θ)=1+cosθ: the same named curve family, used by a different system.', features: [.98,.02,.92,.22,.91,.08,.08,.93,.12], draw: 'cardioid' },
  rose_window: { label: 'Gothic rose window', layer: 'structural_analogy', mechanism: 'Designed radial symmetry and repeated motifs.', features: [.99,.01,.96,.42,.85,.11,.05,.95,.08], draw: 'rose' },
  antenna_interference: { label: 'Wave interference lens', layer: 'demonstrated_connection', mechanism: 'Superposition and phase interference; lotus resemblance is interpretive.', features: [.88,.08,.89,.38,.82,.16,.19,.84,.21], draw: 'waves' },
  mandelbulb: { label: 'Mandelbulb', layer: 'demonstrated_connection', mechanism: 'A 3D fractal inspired by Mandelbrot-style iteration, not one unique canonical extension.', features: [.62,.30,.55,.80,.39,.64,.73,.78,.68], draw: 'bulb' },
  eiffel_tower: { label: 'Eiffel Tower', layer: 'philosophical_interpretation', mechanism: 'Tapered lattice engineering; “3D Mandelbrot tower” is metaphor, not an established derivation.', features: [.96,.04,.70,.49,.63,.29,.18,.74,.18], draw: 'tower' }
};
const featureNames = ['boundedness','escape_speed','periodicity','orbit_entropy','spectral_concentration','spectral_flatness','instability','angular_turning','lyapunov_proxy'];

const state = {
  c: { re: -0.743643887, im: 0.131825904 },
  maxIter: 180,
  view: { re: -0.5, im: 0, span: 3.2 },
  orbit: [], escaped: false, escapeIteration: 180, features: {},
  analogue: 'neuron_branching', prediction: .75,
  renderToken: 0, brainPhase: 0, dragging: false, dragStart: null, viewStart: null,
  audio: null
};

const canvases = {
  hero: $('#heroCanvas'), mandelbrot: $('#mandelbrotCanvas'), julia: $('#juliaCanvas'), orbit: $('#orbitCanvas'),
  brain: $('#brainCanvas'), bulb: $('#bulbCanvas'), share: $('#shareCanvas')
};

function fitCanvas(canvas, maxScale = 1.5) {
  const rect = canvas.getBoundingClientRect();
  const dpr = Math.min(window.devicePixelRatio || 1, maxScale);
  const width = Math.max(2, Math.floor(rect.width * dpr));
  const height = Math.max(2, Math.floor(rect.height * dpr));
  if (canvas.width !== width || canvas.height !== height) { canvas.width = width; canvas.height = height; }
  return { width, height, dpr };
}

function orbitFor(re, im, maxIter, startRe = 0, startIm = 0) {
  let zr = startRe, zi = startIm;
  const orbit = [[zr, zi]];
  for (let i = 1; i <= maxIter; i++) {
    const zr2 = zr * zr - zi * zi + re;
    zi = 2 * zr * zi + im; zr = zr2;
    orbit.push([zr, zi]);
    if (zr * zr + zi * zi > 4) return { orbit, escaped: true, escapeIteration: i };
  }
  return { orbit, escaped: false, escapeIteration: maxIter };
}

function normalizedEntropy(values, bins = 16) {
  if (values.length < 2) return 0;
  const finite = values.filter(Number.isFinite); if (!finite.length) return 0;
  const min = Math.min(...finite), max = Math.max(...finite); if (max - min < 1e-12) return 0;
  const counts = Array(bins).fill(0);
  for (const value of finite) counts[Math.min(bins - 1, Math.floor((value - min) / (max - min) * bins))]++;
  let h = 0; for (const count of counts) if (count) { const p = count / finite.length; h -= p * Math.log(p); }
  return h / Math.log(bins);
}

function spectralStats(signal) {
  const n = Math.min(signal.length, 96); if (n < 4) return [0, 0];
  const sampled = Array.from({ length: n }, (_, i) => signal[Math.floor(i * signal.length / n)]);
  const mean = sampled.reduce((a,b) => a+b,0) / n;
  const power = [];
  for (let k = 1; k <= Math.floor(n / 2); k++) {
    let re = 0, im = 0;
    for (let j = 0; j < n; j++) { const a = -2 * Math.PI * k * j / n; const v = sampled[j] - mean; re += v * Math.cos(a); im += v * Math.sin(a); }
    power.push(re*re + im*im + 1e-15);
  }
  const sum = power.reduce((a,b)=>a+b,0); const dominant = Math.max(...power) / sum;
  const geometric = Math.exp(power.reduce((a,b)=>a+Math.log(b),0)/power.length);
  const arithmetic = sum / power.length;
  return [dominant, clamp(geometric / arithmetic)];
}

function extractFeatures(result) {
  const mags = result.orbit.map(([re,im]) => Math.hypot(re,im));
  const deltas = result.orbit.slice(1).map(([re,im],i) => Math.hypot(re-result.orbit[i][0], im-result.orbit[i][1]));
  const angles = result.orbit.map(([re,im])=>Math.atan2(im,re));
  let periodicity = 0; const tail = result.orbit.slice(Math.floor(result.orbit.length/2));
  for (let lag=1; lag<=Math.min(24,Math.floor(tail.length/2)); lag++) {
    let distance=0,count=0; for(let i=lag;i<tail.length;i++){distance+=Math.hypot(tail[i][0]-tail[i-lag][0],tail[i][1]-tail[i-lag][1]);count++;}
    periodicity=Math.max(periodicity,Math.exp(-4*(distance/Math.max(1,count))));
  }
  const sorted = [...deltas].filter(Number.isFinite).sort((a,b)=>a-b);
  const q = (p) => sorted[Math.min(sorted.length-1,Math.floor(p*(sorted.length-1)))] || 0;
  const instability = sorted.length ? q(.9)/(q(.5)+q(.9)+1e-12) : 0;
  let angular=0; for(let i=1;i<angles.length;i++){let d=Math.abs(angles[i]-angles[i-1]);d=Math.min(d,2*Math.PI-d);angular+=d;}
  angular = angles.length>1 ? clamp(angular/(angles.length-1)/Math.PI) : 0;
  let l=0; for(const m of mags.slice(1)) l+=Math.log(Math.max(2*m,1e-12)); l/=Math.max(1,mags.length-1);
  const [dominant,flatness]=spectralStats(mags);
  return {
    boundedness: result.escaped ? 0 : 1,
    escape_speed: result.escaped ? 1-clamp(result.escapeIteration/state.maxIter) : 0,
    periodicity: clamp(periodicity), orbit_entropy: clamp(normalizedEntropy(mags.map(v=>Math.log1p(v)))),
    spectral_concentration: clamp(dominant), spectral_flatness: clamp(flatness), instability: clamp(instability),
    angular_turning: angular, lyapunov_proxy: clamp(1/(1+Math.exp(-l)))
  };
}

function palette(t, inside = false) {
  if (inside) return [2,4,9];
  const a = .5 + .5*Math.cos(6.283*(t + 0.00));
  const b = .5 + .5*Math.cos(6.283*(t + 0.21));
  const c = .5 + .5*Math.cos(6.283*(t + 0.47));
  return [Math.floor(20+220*a),Math.floor(15+180*b),Math.floor(32+220*c)];
}

async function renderEscape(canvas, mode, options = {}) {
  const { width, height } = fitCanvas(canvas, mode === 'hero' ? 1 : 1.15);
  const ctx = canvas.getContext('2d', { alpha: false });
  const image = ctx.createImageData(width, height); const data = image.data;
  const token = ++state.renderToken;
  const span = options.span ?? (mode === 'julia' ? 3.5 : state.view.span);
  const centerRe = options.re ?? (mode === 'julia' ? 0 : state.view.re);
  const centerIm = options.im ?? (mode === 'julia' ? 0 : state.view.im);
  const aspect = width / height; const spanY = span / aspect;
  const maxIter = options.maxIter ?? state.maxIter;
  const juliaC = options.c ?? state.c;
  const chunk = 20;
  for (let y0=0;y0<height;y0+=chunk) {
    if (token !== state.renderToken && mode !== 'hero') return;
    for(let y=y0;y<Math.min(height,y0+chunk);y++) for(let x=0;x<width;x++) {
      const px = centerRe + (x/width-.5)*span;
      const py = centerIm + (y/height-.5)*spanY;
      let zr = mode === 'julia' ? px : 0, zi = mode === 'julia' ? py : 0;
      const cr = mode === 'julia' ? juliaC.re : px, ci = mode === 'julia' ? juliaC.im : py;
      let i=0,zr2=0,zi2=0;
      for(;i<maxIter && zr2+zi2<=4;i++){zi=2*zr*zi+ci;zr=zr2-zi2+cr;zr2=zr*zr;zi2=zi*zi;}
      let t=0; if(i<maxIter){const smooth=i+1-Math.log2(Math.log2(Math.max(2,Math.sqrt(zr2+zi2))));t=.04*smooth + .07*Math.log2(1+1/span);}
      const [r,g,b]=palette(t,i===maxIter); const p=(y*width+x)*4;data[p]=r;data[p+1]=g;data[p+2]=b;data[p+3]=255;
    }
    if (mode !== 'hero') { ctx.putImageData(image,0,0); await new Promise(requestAnimationFrame); }
  }
  ctx.putImageData(image,0,0);
  if(mode==='mandelbrot') drawSelection(ctx,width,height,span,spanY,centerRe,centerIm);
}

function drawSelection(ctx,w,h,span,spanY,re,im){
  const x=(state.c.re-re)/span*w+w/2,y=(state.c.im-im)/spanY*h+h/2;
  ctx.save();ctx.strokeStyle='#f6f8ff';ctx.lineWidth=1.5;ctx.beginPath();ctx.arc(x,y,8,0,Math.PI*2);ctx.stroke();ctx.strokeStyle='#5febff';ctx.beginPath();ctx.arc(x,y,14,0,Math.PI*2);ctx.stroke();ctx.restore();
}

function drawOrbit() {
  const canvas=canvases.orbit,{width:w,height:h}=fitCanvas(canvas);const ctx=canvas.getContext('2d');ctx.fillStyle='#020306';ctx.fillRect(0,0,w,h);
  const finite=state.orbit.filter(([re,im])=>Number.isFinite(re)&&Number.isFinite(im)&&Math.hypot(re,im)<20);
  const max=Math.max(2,...finite.map(([re,im])=>Math.max(Math.abs(re),Math.abs(im))));const scale=.42*Math.min(w,h)/max;const ox=w/2,oy=h/2;
  ctx.strokeStyle='rgba(151,164,186,.25)';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(0,oy);ctx.lineTo(w,oy);ctx.moveTo(ox,0);ctx.lineTo(ox,h);ctx.stroke();
  const gradient=ctx.createLinearGradient(0,0,w,h);gradient.addColorStop(0,'#9874ff');gradient.addColorStop(.55,'#5febff');gradient.addColorStop(1,'#b9ff6a');ctx.strokeStyle=gradient;ctx.lineWidth=2;ctx.beginPath();
  finite.forEach(([re,im],i)=>{const x=ox+re*scale,y=oy-im*scale;i?ctx.lineTo(x,y):ctx.moveTo(x,y);});ctx.stroke();
  finite.forEach(([re,im],i)=>{if(i%Math.max(1,Math.floor(finite.length/60)))return;ctx.fillStyle=`rgba(95,235,255,${.25+.75*i/finite.length})`;ctx.beginPath();ctx.arc(ox+re*scale,oy-im*scale,2.2,0,Math.PI*2);ctx.fill();});
}

const brainNodes=[['thalamic input',.12,.52],['orbit memory',.32,.22],['periodicity',.55,.18],['boundary salience',.36,.72],['symmetry',.62,.77],['novelty',.80,.32],['integration',.80,.69]];
const brainEdges=[[0,1],[0,3],[1,2],[1,4],[1,6],[2,4],[2,5],[2,6],[3,4],[3,6],[4,6],[5,6],[3,5]];
function brainActivation(){const f=state.features;return [(.2+.75*f.escape_speed),(.15+.7*f.boundedness),(.1+.9*f.periodicity),(.18+.82*f.instability),(.12+.7*f.angular_turning),(.12+.85*f.orbit_entropy),(.1+.45*f.spectral_concentration+.35*f.lyapunov_proxy)].map(clamp);}
function drawBrain(time=0){
  const canvas=canvases.brain,{width:w,height:h}=fitCanvas(canvas);const ctx=canvas.getContext('2d');ctx.fillStyle='#020306';ctx.fillRect(0,0,w,h);const act=brainActivation();
  ctx.save();ctx.globalCompositeOperation='lighter';
  brainEdges.forEach(([a,b],i)=>{const A=brainNodes[a],B=brainNodes[b],pulse=.5+.5*Math.sin(time*.003+i+act[a]*5);ctx.strokeStyle=`rgba(95,235,255,${.06+.18*pulse*(act[a]+act[b])/2})`;ctx.lineWidth=1+2*pulse;ctx.beginPath();ctx.moveTo(A[1]*w,A[2]*h);ctx.quadraticCurveTo((A[1]+B[1])*.5*w,(A[2]+B[2])*.5*h-25*Math.sin(i),B[1]*w,B[2]*h);ctx.stroke();});
  brainNodes.forEach(([label,x,y],i)=>{const p=.5+.5*Math.sin(time*.005*(1+i*.04)+i*1.7);const r=(15+28*act[i]+7*p)*Math.min(1,w/900);const glow=ctx.createRadialGradient(x*w,y*h,0,x*w,y*h,r*2.5);glow.addColorStop(0,`rgba(95,235,255,${.35+.4*act[i]})`);glow.addColorStop(1,'rgba(95,235,255,0)');ctx.fillStyle=glow;ctx.beginPath();ctx.arc(x*w,y*h,r*2.5,0,Math.PI*2);ctx.fill();ctx.fillStyle='#08141c';ctx.strokeStyle=i===6?'#b9ff6a':'#5febff';ctx.lineWidth=1.5;ctx.beginPath();ctx.arc(x*w,y*h,r,0,Math.PI*2);ctx.fill();ctx.stroke();ctx.fillStyle='#eafaff';ctx.font=`${Math.max(10,w/90)}px ui-monospace,monospace`;ctx.textAlign='center';ctx.fillText(label.toUpperCase(),x*w,y*h+r+18);ctx.fillStyle='#5febff';ctx.fillText(`${Math.round(act[i]*100)}`,x*w,y*h+4);});ctx.restore();
  requestAnimationFrame(drawBrain);
}

function compare() {
  const item=analogues[state.analogue];const a=featureNames.map(n=>state.features[n]||0),b=item.features;const distances=a.map((v,i)=>Math.abs(v-b[i]));const sim=clamp(1-Math.sqrt(distances.reduce((s,v)=>s+v*v,0)/distances.length));
  const strongest=featureNames[distances.indexOf(Math.min(...distances))],weakest=featureNames[distances.indexOf(Math.max(...distances))];const gap=Math.abs(state.prediction-sim);
  $('#similarityScore').textContent=pct(sim);$('#predictionScore').textContent=pct(state.prediction);$('#gapScore').textContent=pct(gap);$('#strongestMatch').textContent=labelize(strongest);$('#weakestMatch').textContent=labelize(weakest);$('#mechanismText').textContent=item.mechanism;
  const badge=$('#evidenceBadge');badge.textContent=layerLabel(item.layer);badge.className=`evidence-badge ${layerClass(item.layer)}`;
  state.comparison={sim,gap,strongest,weakest};drawShareCard();
}
function layerLabel(layer){return ({demonstrated_connection:'DEMONSTRATED CONNECTION',structural_analogy:'STRUCTURAL ANALOGY',philosophical_interpretation:'PHILOSOPHICAL INTERPRETATION'})[layer];}
function layerClass(layer){return ({demonstrated_connection:'demonstrated',structural_analogy:'analogy',philosophical_interpretation:'philosophy'})[layer];}

function updateFeatures(){
  const root=$('#featureBars');root.innerHTML='';featureNames.forEach(name=>{const value=state.features[name]||0;const row=document.createElement('div');row.className='feature-row';row.innerHTML=`<span>${labelize(name)}</span><span class="feature-track"><span class="feature-fill" style="display:block;width:${value*100}%"></span></span><span class="feature-value">${Math.round(value*100)}</span>`;root.appendChild(row);});
}

async function runPoint({ rerenderMandelbrot=true }={}) {
  const result=orbitFor(state.c.re,state.c.im,state.maxIter);Object.assign(state,result);state.features=extractFeatures(result);
  $('#realInput').value=state.c.re.toFixed(9);$('#imagInput').value=state.c.im.toFixed(9);$('#orbitStatus').textContent=`${state.orbit.length} finite samples`;$('#escapeStatus').textContent=state.escaped?`escaped at n=${state.escapeIteration}`:'bounded for finite run';$('#juliaStatus').textContent=`c=${state.c.re.toFixed(5)} ${state.c.im<0?'−':'+'} ${Math.abs(state.c.im).toFixed(5)}i`;$('#mandelbrotStatus').textContent=state.escaped?'selected point escapes':'selected point remained bounded';
  if(rerenderMandelbrot) renderEscape(canvases.mandelbrot,'mandelbrot');renderEscape(canvases.julia,'julia',{c:state.c});drawOrbit();updateFeatures();compare();
}

function canvasToComplex(event) {
  const rect=canvases.mandelbrot.getBoundingClientRect(),x=(event.clientX-rect.left)/rect.width,y=(event.clientY-rect.top)/rect.height,aspect=rect.width/rect.height;
  return {re:state.view.re+(x-.5)*state.view.span,im:state.view.im+(y-.5)*state.view.span/aspect};
}

function wireMandelbrotInteraction(){
  const c=canvases.mandelbrot;
  c.addEventListener('wheel',(event)=>{event.preventDefault();const before=canvasToComplex(event);const factor=event.deltaY>0?1.35:.72;state.view.span=clamp(state.view.span*factor,1e-9,4.5);const after=canvasToComplex(event);state.view.re+=before.re-after.re;state.view.im+=before.im-after.im;$('#zoomStatus').textContent=`zoom ${(3.2/state.view.span).toExponential(state.view.span<.001?2:0)}×`;renderEscape(c,'mandelbrot');},{passive:false});
  c.addEventListener('pointerdown',(event)=>{state.dragging=true;state.dragStart={x:event.clientX,y:event.clientY};state.viewStart={...state.view};c.setPointerCapture(event.pointerId);});
  c.addEventListener('pointermove',(event)=>{if(!state.dragging)return;const rect=c.getBoundingClientRect(),aspect=rect.width/rect.height;state.view.re=state.viewStart.re-(event.clientX-state.dragStart.x)/rect.width*state.view.span;state.view.im=state.viewStart.im-(event.clientY-state.dragStart.y)/rect.height*state.view.span/aspect;renderEscape(c,'mandelbrot');});
  c.addEventListener('pointerup',(event)=>{const moved=Math.hypot(event.clientX-state.dragStart.x,event.clientY-state.dragStart.y);state.dragging=false;if(moved<7){state.c=canvasToComplex(event);runPoint();}});
}

function sonify(){
  const AudioContext=window.AudioContext||window.webkitAudioContext;if(!AudioContext)return;
  if(!state.audio)state.audio=new AudioContext();const ac=state.audio,now=ac.currentTime+.03;const points=state.orbit.length>96?Array.from({length:96},(_,i)=>state.orbit[Math.floor(i*(state.orbit.length-1)/95)]):state.orbit;
  points.forEach(([re,im],i)=>{const radius=Math.hypot(re,im),angle=Math.atan2(im,re),freq=clamp(110*Math.pow(2,Math.min(5,Math.log2(1+radius)))*(1+.5*(1+Math.sin(angle*3))),45,4000);const osc=ac.createOscillator(),gain=ac.createGain(),pan=ac.createStereoPanner();osc.type=i%4?'sine':'triangle';osc.frequency.setValueAtTime(freq,now+i*.055);pan.pan.value=clamp(Math.tanh(re),-1,1);const g=clamp(.16/(1+.35*radius),.02,.18);gain.gain.setValueAtTime(.0001,now+i*.055);gain.gain.exponentialRampToValueAtTime(g,now+i*.055+.01);gain.gain.exponentialRampToValueAtTime(.0001,now+i*.055+.07+.08*state.features.periodicity);osc.connect(gain).connect(pan).connect(ac.destination);osc.start(now+i*.055);osc.stop(now+i*.055+.18);});
}

function seeded(seed){let x=Math.sin(seed*999.13)*43758.5453;return x-Math.floor(x);}
function drawBranch(ctx,x,y,len,angle,depth,spread,seed){if(depth<=0||len<2)return;const x2=x+Math.cos(angle)*len,y2=y+Math.sin(angle)*len;ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(x2,y2);ctx.stroke();const branches=depth>3?2:1+(seeded(seed)>.68?1:0);for(let i=0;i<branches;i++){const side=branches===1?(seeded(seed+4)>.5?1:-1):(i?1:-1);drawBranch(ctx,x2,y2,len*(.66+.08*seeded(seed+i)),angle+side*(spread*(.72+.35*seeded(seed+8+i))),depth-1,spread,seed*1.71+i+1);}}
function drawAnalogue(canvas,type,index=0){
  const {width:w,height:h}=fitCanvas(canvas,1);const ctx=canvas.getContext('2d');ctx.fillStyle='#050810';ctx.fillRect(0,0,w,h);ctx.strokeStyle='rgba(95,235,255,.78)';ctx.lineWidth=Math.max(1,w/330);ctx.shadowBlur=12;ctx.shadowColor='#5febff';
  if(['neuron','lightning','river','tree'].includes(type)){const base=type==='tree'?[w/2,h*.95]:type==='river'?[w*.08,h*.45]:type==='lightning'?[w*.2,0]:[w*.3,h*.65];const angle=type==='tree'?-Math.PI/2:type==='river'?0:type==='lightning'?Math.PI*.4:-.15;drawBranch(ctx,...base,h*.28,angle,7,type==='lightning'?.55:.45,11+index);}
  else if(type==='cardioid'||type==='caustic'){ctx.beginPath();for(let i=0;i<=420;i++){const a=i/420*Math.PI*2,r=(type==='cardioid'?1:1.25)*(1+Math.cos(a));const x=w/2+Math.cos(a)*r*w*.19,y=h/2+Math.sin(a)*r*h*.31;i?ctx.lineTo(x,y):ctx.moveTo(x,y);}ctx.stroke();if(type==='caustic'){ctx.globalAlpha=.2;for(let i=0;i<36;i++){ctx.beginPath();ctx.moveTo(w*.08+i*w*.024,h*.08);ctx.quadraticCurveTo(w*.5,h*(.2+i*.012),w*.85,h*.88);ctx.stroke();}}}
  else if(type==='rose'){for(let ring=1;ring<4;ring++)for(let i=0;i<12;i++){ctx.beginPath();ctx.ellipse(w/2+Math.cos(i*Math.PI/6)*ring*w*.065,h/2+Math.sin(i*Math.PI/6)*ring*h*.09,w*.08,h*.16,i*Math.PI/6,0,Math.PI*2);ctx.stroke();}}
  else if(type==='waves'){for(let source of [-1,1])for(let r=12;r<w*.8;r+=18){ctx.globalAlpha=.18+.12*Math.sin(r);ctx.beginPath();ctx.arc(w/2+source*w*.24,h/2,r,0,Math.PI*2);ctx.stroke();}}
  else if(type==='tower'){ctx.beginPath();ctx.moveTo(w*.25,h*.92);ctx.quadraticCurveTo(w*.43,h*.43,w*.48,h*.08);ctx.lineTo(w*.52,h*.08);ctx.quadraticCurveTo(w*.57,h*.43,w*.75,h*.92);ctx.closePath();ctx.stroke();for(let y=.2;y<.9;y+=.1){ctx.beginPath();ctx.moveTo(w*(.35+y*.15),h*y);ctx.lineTo(w*(.65-y*.15),h*y);ctx.stroke();}}
  else {for(let i=0;i<80;i++){const a=i*.55,r=3*Math.sqrt(i),x=w/2+Math.cos(a)*r,y=h/2+Math.sin(a)*r;ctx.beginPath();ctx.arc(x,y,2+i*.02,0,Math.PI*2);ctx.stroke();}}
  ctx.shadowBlur=0;ctx.globalAlpha=1;
}

function buildAtlas(){
  const grid=$('#atlasGrid');Object.entries(analogues).forEach(([key,item],i)=>{const card=document.createElement('article');card.className='atlas-card panel';card.innerHTML=`<canvas></canvas><span class="truth ${layerClass(item.layer)}">${layerLabel(item.layer)}</span><h3>${item.label}</h3><p>${item.mechanism}</p><button class="ghost" type="button">Compare this</button>`;grid.appendChild(card);drawAnalogue(card.querySelector('canvas'),item.draw,i);card.querySelector('button').addEventListener('click',()=>{state.analogue=key;$('#analogueSelect').value=key;compare();location.hash='lab';});});
}

function drawShareCard(){
  if(!state.comparison)return;const c=canvases.share,ctx=c.getContext('2d'),w=c.width,h=c.height;const grad=ctx.createLinearGradient(0,0,w,h);grad.addColorStop(0,'#090d18');grad.addColorStop(.6,'#07131b');grad.addColorStop(1,'#130d24');ctx.fillStyle=grad;ctx.fillRect(0,0,w,h);
  ctx.strokeStyle='rgba(95,235,255,.18)';ctx.lineWidth=2;for(let x=0;x<w;x+=54){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,h);ctx.stroke();}for(let y=0;y<h;y+=54){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(w,y);ctx.stroke();}
  ctx.fillStyle='#5febff';ctx.font='700 28px ui-monospace,monospace';ctx.fillText('GAUGEGAP FOUNDRY · LAB 001',70,86);ctx.fillStyle='#f6f8ff';ctx.font='800 78px system-ui,sans-serif';ctx.fillText('I tested the',70,190);ctx.fillText('“code of reality.”',70,278);
  const preview=document.createElement('canvas');preview.width=940;preview.height=430;drawMiniMandel(preview,state.c);ctx.drawImage(preview,70,340,940,430);
  ctx.fillStyle='#97a4ba';ctx.font='28px system-ui,sans-serif';ctx.fillText(`c = ${state.c.re.toFixed(8)} ${state.c.im<0?'−':'+'} ${Math.abs(state.c.im).toFixed(8)}i`,70,820);ctx.fillStyle='#f6f8ff';ctx.font='700 42px system-ui,sans-serif';ctx.fillText(`Compared with: ${analogues[state.analogue].label}`,70,895);
  const items=[['Measured similarity',pct(state.comparison.sim)],['My prediction',pct(state.prediction)],['Gauge gap',pct(state.comparison.gap)],['Strongest match',labelize(state.comparison.strongest)]];items.forEach(([k,v],i)=>{const x=70+(i%2)*490,y=970+Math.floor(i/2)*120;ctx.fillStyle='#97a4ba';ctx.font='24px system-ui,sans-serif';ctx.fillText(k,x,y);ctx.fillStyle=i===2?'#ffc66d':'#f6f8ff';ctx.font='700 42px system-ui,sans-serif';ctx.fillText(v,x,y+48);});
  ctx.fillStyle=analogues[state.analogue].layer==='demonstrated_connection'?'#b9ff6a':analogues[state.analogue].layer==='structural_analogy'?'#ffc66d':'#ff79c6';ctx.font='800 24px ui-monospace,monospace';ctx.fillText(layerLabel(analogues[state.analogue].layer),70,1245);ctx.fillStyle='#97a4ba';ctx.font='22px system-ui,sans-serif';ctx.fillText('Visual similarity is not proof of a shared physical mechanism.',70,1300);
}
function drawMiniMandel(canvas,c){const ctx=canvas.getContext('2d'),w=canvas.width,h=canvas.height,img=ctx.createImageData(w,h),data=img.data,max=90;for(let y=0;y<h;y+=2)for(let x=0;x<w;x+=2){const cr=-.5+(x/w-.5)*3.2,ci=(y/h-.5)*1.48;let zr=0,zi=0,i=0;for(;i<max&&zr*zr+zi*zi<4;i++){const t=zr*zr-zi*zi+cr;zi=2*zr*zi+ci;zr=t;}const col=palette(i*.035,i===max);for(let dy=0;dy<2;dy++)for(let dx=0;dx<2;dx++){const p=((y+dy)*w+x+dx)*4;data[p]=col[0];data[p+1]=col[1];data[p+2]=col[2];data[p+3]=255;}}ctx.putImageData(img,0,0);const px=(c.re+2.1)/3.2*w,py=(c.im/.74+.5)*h;ctx.strokeStyle='#fff';ctx.lineWidth=3;ctx.beginPath();ctx.arc(px,py,11,0,Math.PI*2);ctx.stroke();}

function initBulb(){
  const canvas=canvases.bulb,gl=canvas.getContext('webgl',{antialias:false});if(!gl){canvas.replaceWith(Object.assign(document.createElement('p'),{textContent:'WebGL is required for the live Mandelbulb.'}));return;}
  const vertex=`attribute vec2 p;void main(){gl_Position=vec4(p,0.,1.);}`;
  const fragment=`precision highp float;uniform vec2 r;uniform float t;uniform float power;uniform float steps;mat2 rot(float a){float c=cos(a),s=sin(a);return mat2(c,-s,s,c);}float de(vec3 p){vec3 z=p;float dr=1.;float rr=0.;for(int i=0;i<12;i++){rr=length(z);if(rr>2.4)break;float th=acos(z.z/max(rr,.0001));float ph=atan(z.y,z.x);float zr=pow(rr,power);dr=pow(rr,power-1.)*power*dr+1.;th*=power;ph*=power;z=zr*vec3(sin(th)*cos(ph),sin(ph)*sin(th),cos(th))+p;}return .5*log(rr)*rr/dr;}vec3 normal(vec3 p){vec2 e=vec2(.001,0.);return normalize(vec3(de(p+e.xyy)-de(p-e.xyy),de(p+e.yxy)-de(p-e.yxy),de(p+e.yyx)-de(p-e.yyx)));}void main(){vec2 uv=(gl_FragCoord.xy*2.-r)/r.y;vec3 ro=vec3(0.,0.,3.25),rd=normalize(vec3(uv,-1.7));ro.xz*=rot(t*.18);rd.xz*=rot(t*.18);ro.yz*=rot(.35);rd.yz*=rot(.35);float d=0.,travel=0.;vec3 p;for(int i=0;i<96;i++){if(float(i)>steps)break;p=ro+rd*travel;d=de(p);travel+=d;if(d<.0015||travel>6.)break;}vec3 col=vec3(.005,.008,.015);if(travel<6.){vec3 n=normal(p),light=normalize(vec3(.8,.6,1.));float diff=max(.0,dot(n,light));float rim=pow(1.-max(.0,dot(n,-rd)),2.);col=vec3(.12,.55,.7)*diff+vec3(.45,.22,.9)*rim+.025;}col*=1.-.14*length(uv);gl_FragColor=vec4(pow(col,vec3(.7)),1.);}`;
  const shader=(type,src)=>{const s=gl.createShader(type);gl.shaderSource(s,src);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))console.warn(gl.getShaderInfoLog(s));return s;};const program=gl.createProgram();gl.attachShader(program,shader(gl.VERTEX_SHADER,vertex));gl.attachShader(program,shader(gl.FRAGMENT_SHADER,fragment));gl.linkProgram(program);gl.useProgram(program);const buf=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buf);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,3,-1,-1,3]),gl.STATIC_DRAW);const loc=gl.getAttribLocation(program,'p');gl.enableVertexAttribArray(loc);gl.vertexAttribPointer(loc,2,gl.FLOAT,false,0,0);
  function frame(ms){const {width,height}=fitCanvas(canvas,1);gl.viewport(0,0,width,height);gl.uniform2f(gl.getUniformLocation(program,'r'),width,height);gl.uniform1f(gl.getUniformLocation(program,'t'),ms/1000);gl.uniform1f(gl.getUniformLocation(program,'power'),Number($('#bulbPower').value));gl.uniform1f(gl.getUniformLocation(program,'steps'),Number($('#bulbDetail').value));gl.drawArrays(gl.TRIANGLES,0,3);requestAnimationFrame(frame);}requestAnimationFrame(frame);
}

function populateControls(){const select=$('#analogueSelect');Object.entries(analogues).forEach(([key,item])=>select.add(new Option(item.label,key)));select.value=state.analogue;}
function bindControls(){
  $('#applyPoint').addEventListener('click',()=>{state.c={re:Number($('#realInput').value),im:Number($('#imagInput').value)};runPoint();});
  $('#iterationInput').addEventListener('input',(e)=>{$('#iterationOutput').textContent=e.target.value;state.maxIter=Number(e.target.value);});$('#iterationInput').addEventListener('change',()=>runPoint());
  $('#predictionInput').addEventListener('input',(e)=>{state.prediction=Number(e.target.value)/100;$('#predictionOutput').textContent=e.target.value+'%';compare();});
  $('#analogueSelect').addEventListener('change',(e)=>{state.analogue=e.target.value;compare();});$('#playSound').addEventListener('click',sonify);
  $('#resetView').addEventListener('click',()=>{state.view={re:-.5,im:0,span:3.2};$('#zoomStatus').textContent='zoom 1.00×';renderEscape(canvases.mandelbrot,'mandelbrot');});
  $('#randomBoundary').addEventListener('click',()=>{const points=[[-.743643887,.131825904],[-.1011,.9563],[-1.25066,.02012],[-.16,1.0405],[-.7453,.1127]];const p=points[Math.floor(Math.random()*points.length)];state.c={re:p[0]+(Math.random()-.5)*1e-5,im:p[1]+(Math.random()-.5)*1e-5};state.view={re:state.c.re,im:state.c.im,span:.015};runPoint();location.hash='lab';});
  $('#modeToggle').addEventListener('click',()=>{document.body.classList.toggle('focus');$('#modeToggle').textContent=document.body.classList.contains('focus')?'Exit focus':'Focus mode';});
  $('#bulbPower').addEventListener('input',(e)=>$('#bulbPowerOutput').textContent=e.target.value);$('#bulbDetail').addEventListener('input',(e)=>$('#bulbDetailOutput').textContent=e.target.value);
  $('#downloadCard').addEventListener('click',()=>{const a=document.createElement('a');a.download=`gaugegap-${state.analogue}-${Date.now()}.png`;a.href=canvases.share.toDataURL('image/png');a.click();});
  $('#copyResult').addEventListener('click',async()=>{const text=`I tested ${analogues[state.analogue].label} against the Mandelbrot point c=${state.c.re.toFixed(8)}${state.c.im<0?'':'+'}${state.c.im.toFixed(8)}i. Measured feature similarity: ${pct(state.comparison.sim)}. My prediction: ${pct(state.prediction)}. Gauge gap: ${pct(state.comparison.gap)}. Verdict: ${layerLabel(analogues[state.analogue].layer)}. Visual similarity is not proof of a shared physical mechanism.`;try{await navigator.clipboard.writeText(text);$('#copyStatus').textContent='Result copied.';}catch{$('#copyStatus').textContent=text;}});
}

async function init(){populateControls();bindControls();wireMandelbrotInteraction();buildAtlas();renderEscape(canvases.hero,'hero',{re:-.61,im:.02,span:2.6,maxIter:110});await runPoint();drawBrain();initBulb();window.addEventListener('resize',()=>{renderEscape(canvases.mandelbrot,'mandelbrot');renderEscape(canvases.julia,'julia',{c:state.c});drawOrbit();document.querySelectorAll('.atlas-card canvas').forEach((c,i)=>drawAnalogue(c,Object.values(analogues)[i].draw,i));});}
init();
