/** Detección local y opcional de celular con MediaPipe Tasks Vision. */
class PhoneMonitor {
  constructor() {
    this.detector = null;
    this.timer = null;
    this.active = false;
    this.busy = false;
    this.pendingReview = false;
    this.visibleLastCycle = false;
    this.missedCycles = 0;
    this.episodeStart = null;
    this.episodeId = null;
    this.lastPositiveAt = null;
    this.capturedSlots = new Set();
  }

  async start(video, onDetection, onStatus, onCapture) {
    this.active = true;
    this.visibleLastCycle = false;
    this.missedCycles = 0;
    this.episodeStart = null;
    this.episodeId = null;
    this.lastPositiveAt = null;
    this.capturedSlots.clear();
    try {
      const { FilesetResolver, ObjectDetector } = await import('/static/models/mediapipe/vision_bundle.mjs');
      if (!this.active) return;
      const vision = await FilesetResolver.forVisionTasks('/static/models/mediapipe/wasm');
      if (!this.active) return;
      this.detector = await ObjectDetector.createFromOptions(vision, {
        baseOptions: { modelAssetPath: '/static/models/mediapipe/efficientdet_lite0.tflite', delegate: 'CPU' },
        runningMode: 'VIDEO',
        scoreThreshold: 0.50,
        categoryAllowlist: ['cell phone']
      });
      if (!this.active) { this.detector.close(); return; }
      onStatus('Detector de celular activo. Mantén el celular fuera de la cámara.');
      this.timer = setInterval(async () => {
        if (!this.active || this.busy || this.pendingReview || video.readyState < 2) return;
        this.busy = true;
        try {
          const resultado = this.detector.detectForVideo(video, performance.now());
          const celular = resultado.detections.some(d => d.categories.some(c => c.categoryName === 'cell phone' && c.score >= 0.50));
          if (celular) {
            const now = performance.now();
            if (this.episodeStart === null || (this.lastPositiveAt !== null && now - this.lastPositiveAt > 2500)) {
              this.episodeStart = now;
              this.episodeId = crypto.randomUUID();
              this.capturedSlots.clear();
            }
            this.lastPositiveAt = now;
            this.missedCycles = 0;
            if (!this.visibleLastCycle) onStatus('Posible celular detectado. Si permanece visible durante 10 segundos, el caso irá a revisión humana.');
            this.visibleLastCycle = true;
            // Congelar el fotograma antes de esperar la respuesta del servidor.
            // El envío espera la confirmación de la detección asociada al episodio.
            const deteccion = onDetection(this.episodeId);
            // Primera foto en la primera observación (~1 s); después a los 3, 7 y 10 s.
            for (const [slot, elapsed] of [[1, 0], [3, 2000], [7, 6000], [10, 9000]]) {
              if (now - this.episodeStart >= elapsed && !this.capturedSlots.has(slot)) {
                this.capturedSlots.add(slot);
                if (onCapture) onCapture(video, this.episodeId, slot, deteccion).catch(error => {
                  console.warn('No se pudo guardar una captura de celular:', error.name);
                  onStatus('Posible celular detectado, pero una fotografía no pudo guardarse.');
                });
              }
            }
            const estado = await deteccion;
            if (estado?.revision_pendiente) {
              this.pendingReview = true;
              onStatus('Detección sostenida de celular: resultado pendiente de revisión humana.');
            }
          } else if (this.visibleLastCycle && ++this.missedCycles >= 2) {
            this.visibleLastCycle = false;
            this.missedCycles = 0;
            this.episodeStart = null;
            this.episodeId = null;
            this.lastPositiveAt = null;
            this.capturedSlots.clear();
            onStatus('Detector de celular activo. No se observa celular actualmente.');
          }
        } catch (error) {
          console.warn('Error del detector de objetos:', error);
          onStatus('Detector de celular no disponible; se mantiene la supervisión facial.');
          this.stop();
        } finally {
          this.busy = false;
        }
      }, 1000);
    } catch (error) {
      console.warn('No se pudo iniciar el detector de celular:', error);
      onStatus('Detector de celular no disponible; se mantiene la supervisión facial.');
      this.stop();
    }
  }

  stop() {
    this.active = false;
    if (this.timer) clearInterval(this.timer);
    this.timer = null;
    if (this.detector) this.detector.close();
    this.detector = null;
  }
}

window.PhoneMonitor = PhoneMonitor;
