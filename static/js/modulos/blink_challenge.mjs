// Reto básico de movimiento; no certifica identidad ni impide videos reproducidos.
export class BlinkSequence {
  constructor() {
    this.count = 0;
    this.phase = 'open';
    this.since = null;
    this.last = null;
  }

  update(left, right, now) {
    const valid = [left, right].every(n => Number.isFinite(n) && n >= 0 && n <= 1);
    if (!valid || (this.last !== null && now - this.last > 1500)) {
      this.phase = 'open';
      this.since = null;
    }
    this.last = now;
    if (!valid) return 'sin lectura';
    const open = left <= 0.3 && right <= 0.3;
    const closed = left >= 0.55 && right >= 0.55;
    const matches = this.phase === 'close' ? closed : open;
    if (!matches) {
      this.since = null;
    } else {
      if (this.since === null) this.since = now;
      const duration = this.phase === 'close' ? 100 : 150;
      if (now - this.since >= duration) {
        if (this.phase === 'reopen') {
          this.count++;
          this.phase = 'close';
        } else {
          this.phase = this.phase === 'open' ? 'close' : 'reopen';
        }
        this.since = null;
      }
    }
    return closed ? 'cerrados' : open ? 'abiertos' : 'en transición';
  }
}

export async function runBlinkChallenge(video, onUpdate) {
  let detector;
  const sequence = new BlinkSequence();
  onUpdate('Cargando detector de ojos…');
  try {
    const { FaceLandmarker, FilesetResolver } = await import('/static/models/mediapipe/vision_bundle.mjs');
    const files = await FilesetResolver.forVisionTasks('/static/models/mediapipe/wasm');
    detector = await FaceLandmarker.createFromOptions(files, {
      baseOptions: { modelAssetPath: '/static/models/mediapipe/face_landmarker.task', delegate: 'CPU' },
      runningMode: 'VIDEO',
      numFaces: 2,
      outputFaceBlendshapes: true,
      minFaceDetectionConfidence: 0.5,
      minFacePresenceConfidence: 0.5,
      minTrackingConfidence: 0.5
    });
    const deadline = performance.now() + 30000;
    let lastVideoTime = -1;
    let lastFrameAt = performance.now();
    while (performance.now() < deadline && sequence.count < 2) {
      await new Promise(resolve => requestAnimationFrame(resolve));
      const now = performance.now();
      if (video.paused || video.ended || !video.srcObject?.active) {
        throw new Error('La cámara se interrumpió. Reiníciala antes de reintentar.');
      }
      if (video.readyState < 2 || video.currentTime === lastVideoTime) {
        if (now - lastFrameAt > 3000) throw new Error('La imagen está detenida. Reinicia la cámara.');
        continue;
      }
      lastVideoTime = video.currentTime;
      lastFrameAt = now;
      const result = detector.detectForVideo(video, now);
      const single = result.faceLandmarks.length === 1;
      const categories = single ? result.faceBlendshapes[0]?.categories : null;
      const left = categories?.find(item => item.categoryName === 'eyeBlinkLeft')?.score;
      const right = categories?.find(item => item.categoryName === 'eyeBlinkRight')?.score;
      const state = sequence.update(left, right, now);
      const instruction = !single ? 'Debe verse un solo rostro, de frente.' :
        sequence.phase === 'close' ? 'Cierra ambos ojos un segundo.' : 'Abre ambos ojos mirando de frente.';
      const lectura = Number.isFinite(left) && Number.isFinite(right)
        ? ` · cierre izquierdo ${Math.round(left * 100)}%, derecho ${Math.round(right * 100)}%`
        : '';
      onUpdate(`Ojos: ${state}${lectura} · ${sequence.count}/2 completados · ${Math.max(0, Math.ceil((deadline - now) / 1000))} s. ${instruction}`);
    }
    if (sequence.count < 2) {
      onUpdate(`Se registraron ${sequence.count}/2 cierres completos. Reintenta con los ojos visibles y luz frontal. Esto no indica que hayas usado una foto.`);
    }
    return sequence.count >= 2;
  } finally {
    detector?.close();
  }
}
