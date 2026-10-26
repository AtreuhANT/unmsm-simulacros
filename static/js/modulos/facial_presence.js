/**
 * MÓDULO 1: FACIAL PRESENCE & BIOMETRIC IDENTITY MONITOR (FASE 6)
 * Supervisión biométrica Edge periódica no acumulada y tolerante a fluctuaciones lumínicas.
 * - Intervalo no invasivo de 6 segundos (IA-03: <10% CPU).
 * - Distinción de incertidumbre temporal vs infracción sostenida (IA-02).
 * - Deduplicación de alertas por episodio continuo (MO-01).
 */

class FacialPresenceMonitor {
  constructor() {
    this.video = null;
    this.canvas = null;
    this.storedDescriptors = [];
    this.intervalId = null;
    this.callbacks = null;
    this.isChecking = false;
    this.absenceEpisode = null;
    this.absenceSequence = 0;
    this.generation = 0;

    // Control de estados por racha consecutiva (evita falsos positivos por parpadeo o inclinación momentánea)
    this.absenceStreak = 0;
    this.multipleFacesStreak = 0;
    this.mismatchStreak = 0;

    // Banderas para deduplicar eventos durante un mismo episodio
    this.absenceReported = false;
    this.multipleReported = false;
    this.mismatchReported = false;

    this.MATCH_THRESHOLD = 0.55; // Umbral oficial UNMSM
    this.INTERVAL_MS = 6000;     // Cada 6 segundos (optimización de consumo de CPU)
  }

  init(videoElement, canvasElement, storedDescriptors, callbacks) {
    this.video = videoElement;
    this.canvas = canvasElement;
    this.callbacks = callbacks || {};

    // Normalizar descriptores a Float32Array
    this.storedDescriptors = (storedDescriptors || []).map(desc => {
      return desc instanceof Float32Array ? desc : new Float32Array(desc);
    });

    this.startPeriodicCheck();
  }

  startPeriodicCheck() {
    if (this.intervalId) clearInterval(this.intervalId);
    this.intervalId = setInterval(() => this.runCheck(), this.INTERVAL_MS);
  }

  stop() {
    this.generation++;
    this.closeAbsence('interrumpido');
    this.multipleFacesStreak = 0;
    this.multipleReported = false;
    this.mismatchStreak = 0;
    this.mismatchReported = false;
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
    if (this.canvas) {
      const ctx = this.canvas.getContext('2d');
      if (ctx) ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }
  }

  emitAbsence(estado,frame=this.video) {
    if (!this.callbacks?.onAbsenceObservation) return;
    if (!this.absenceEpisode) {
      if (estado !== 'ausente') return;
      this.absenceEpisode = crypto.randomUUID();
      this.absenceSequence = 0;
    }
    const observacion = { episodioId: this.absenceEpisode, secuencia: ++this.absenceSequence, estado };
    Promise.resolve(this.callbacks.onAbsenceObservation(observacion,frame))
      .catch(error => console.warn('[FACIAL] No se pudo comunicar la observación:',error.name));
  }

  closeAbsence(estado) {
    if (!this.absenceEpisode) return;
    this.emitAbsence(estado);
    this.absenceEpisode = null;
    this.absenceSequence = 0;
    this.absenceStreak = 0;
    this.absenceReported = false;
  }

  getMinEuclideanDistance(currentDescriptor) {
    if (!this.storedDescriptors || this.storedDescriptors.length === 0) return 0.0;

    let minDistance = 999.0;
    for (const stored of this.storedDescriptors) {
      const dist = faceapi.euclideanDistance(currentDescriptor, stored);
      if (dist < minDistance) minDistance = dist;
    }
    return minDistance;
  }

  async runCheck() {
    if (!this.video || this.video.paused || this.video.ended) {
      this.closeAbsence('interrumpido');
      return;
    }
    if (this.isChecking) return;
    this.isChecking = true;
    const generation = this.generation;

    try {
      if (!this.video.videoWidth || !this.video.videoHeight) throw new Error('Fotograma no disponible');
      const frame=document.createElement('canvas');
      frame.width=this.video.videoWidth; frame.height=this.video.videoHeight;
      frame.getContext('2d').drawImage(this.video,0,0);
      // Detección ligera con TinyFaceDetector
      const detections = await faceapi
        .detectAllFaces(frame, new faceapi.TinyFaceDetectorOptions({ inputSize: 224, scoreThreshold: 0.5 }))
        .withFaceLandmarks(true)
        .withFaceDescriptors();
      if (generation !== this.generation) return;
      if (detections.length > 0) this.closeAbsence('presente');

      // Renderizar feedback visual en canvas si está disponible
      if (this.canvas && this.video.clientWidth > 0) {
        const displaySize = { width: this.video.clientWidth, height: this.video.clientHeight };
        this.canvas.width = displaySize.width;
        this.canvas.height = displaySize.height;
        const resized = faceapi.resizeResults(detections, displaySize);
        const ctx = this.canvas.getContext('2d');
        ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        faceapi.draw.drawDetections(this.canvas, resized);
      }

      // =======================================================================
      // CASO A: AUSENCIA DE ROSTRO
      // =======================================================================
      if (detections.length === 0) {
        this.emitAbsence('ausente',frame);
        this.absenceStreak++;
        this.multipleFacesStreak = 0;
        this.multipleReported = false;
        this.mismatchStreak = 0;
        this.mismatchReported = false;

        if (this.callbacks.onStatusChange) {
          this.callbacks.onStatusChange('warning', 'Sin rostro detectado');
        }

        // Dos observaciones consecutivas; los segundos los registra el servidor.
        if (this.absenceStreak >= 2 && !this.absenceReported) {
          this.absenceReported = true;
          if (this.callbacks.onStatusChange) {
            this.callbacks.onStatusChange('danger', 'Ausencia facial prolongada');
          }
          if (this.callbacks.onViolation && !this.callbacks.onAbsenceObservation) {
            this.callbacks.onViolation(
              'facial_presence',
              'ausencia_prolongada',
              'No se detecta rostro frente a la cámara web en observaciones consecutivas'
            );
          }
        }
      }

      // =======================================================================
      // CASO B: MÚLTIPLES PERSONAS DETECTADAS
      // =======================================================================
      else if (detections.length >= 2) {
        this.multipleFacesStreak++;
        this.absenceStreak = 0;
        this.absenceReported = false;
        this.mismatchStreak = 0;

        if (this.callbacks.onStatusChange) {
          this.callbacks.onStatusChange('danger', `Alerta: ${detections.length} personas en cámara`);
        }

        if (this.multipleFacesStreak >= 2 && !this.multipleReported) {
          this.multipleReported = true;
          if (this.callbacks.onViolation) {
            this.callbacks.onViolation(
              'facial_presence',
              'multiple_rostro',
              `Se detectaron ${detections.length} personas en cámara de manera continuada`
            );
          }
        }
      }

      // =======================================================================
      // CASO C: UN ROSTRO (VERIFICACIÓN BIOMÉTRICA CONTRA PLANTILLA)
      // =======================================================================
      else {
        this.absenceStreak = 0;
        this.absenceReported = false;
        this.multipleFacesStreak = 0;
        this.multipleReported = false;

        const currentDescriptor = detections[0].descriptor;
        const minDistance = this.getMinEuclideanDistance(currentDescriptor);

        if (minDistance > this.MATCH_THRESHOLD) {
          this.mismatchStreak++;
          if (this.callbacks.onStatusChange) {
            this.callbacks.onStatusChange('warning', `Discrepancia facial (d=${minDistance.toFixed(2)})`);
          }

          if (this.mismatchStreak >= 2 && !this.mismatchReported) {
            this.mismatchReported = true;
            if (this.callbacks.onStatusChange) {
              this.callbacks.onStatusChange('danger', 'Identidad no coincide');
            }
            if (this.callbacks.onViolation) {
              this.callbacks.onViolation(
                'facial_presence',
                'no_coincide',
                `Discrepancia biométrica con la plantilla registrada (Distancia: ${minDistance.toFixed(3)})`
              );
            }
          }
        } else {
          // Identidad conforme
          this.mismatchStreak = 0;
          this.mismatchReported = false;
          if (this.callbacks.onStatusChange) {
            this.callbacks.onStatusChange('ok', 'Coincidencia facial; presencia sujeta a comprobación');
          }
        }
      }
    } catch (err) {
      if (generation !== this.generation) return;
      this.closeAbsence('interrumpido');
      this.multipleFacesStreak = 0;
      this.multipleReported = false;
      this.mismatchStreak = 0;
      this.mismatchReported = false;
      console.warn('[FACIAL] Excepción en ciclo de inspección:', err);
      if (this.callbacks.onStatusChange) {
        this.callbacks.onStatusChange('danger', 'La supervisión facial no pudo analizar la imagen. Comprueba la cámara.');
      }
    } finally {
      this.isChecking = false;
    }
  }
}

window.FacialPresenceMonitor = FacialPresenceMonitor;
