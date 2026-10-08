/**
 * MÓDULO 2: FOCUS & FULLSCREEN MONITOR (FASE 6)
 * Supervisión continua del foco de pantalla, ventana y modo pantalla completa.
 * - Deduplicación de eventos por episodio (MO-01): agrupa blur + visibilitychange en 1 sola observación.
 * - Medición de duración fuera de la ventana (segundos ausente).
 * - Tolerancia a desenfoques accidentales menores a 2 segundos (MO-02).
 */

class FocusMonitor {
  constructor() {
    this.callbacks = null;
    this.observationsCount = 0;
    this.isActive = false;
    this.isWindowFocused = true;
    this.blurStartTime = 0;
    this.lastReportTime = 0;
    this.DEBOUNCE_MS = 2000; // 2 segundos de ventana mínima
  }

  init(callbacks) {
    this.callbacks = callbacks || {};
    this.observationsCount = 0;
    this.isActive = true;
    this.isWindowFocused = !document.hidden;
    this.attachEventListeners();
  }

  stop() {
    this.isActive = false;
  }

  handleFocusLost(tipo, motivo) {
    if (!this.isActive || !this.isWindowFocused) return;

    const now = Date.now();
    if (now - this.lastReportTime < this.DEBOUNCE_MS) return;

    this.isWindowFocused = false;
    this.blurStartTime = now;
    this.lastReportTime = now;
    this.observationsCount++;

    if (this.callbacks.onStrikeUpdate) {
      this.callbacks.onStrikeUpdate(this.observationsCount, 5);
    }

    if (this.callbacks.onViolation) {
      this.callbacks.onViolation('focus_monitor', tipo, `${motivo} (Observación #${this.observationsCount})`);
    }
  }

  handleFocusGained() {
    if (!this.isActive || this.isWindowFocused) return;
    this.isWindowFocused = true;

    const now = Date.now();
    const durationSecs = Math.max(1, Math.round((now - this.blurStartTime) / 1000));

    // Si estuvo fuera más de 3 segundos, registrar el retorno con duración exacta para auditoría
    if (durationSecs >= 3 && this.callbacks.onViolation) {
      this.callbacks.onViolation(
        'focus_monitor',
        'retorno_foco',
        `Postulante regresó a la evaluación tras permanecer ${durationSecs} segundos fuera de la ventana`
      );
    }
  }

  attachEventListeners() {
    // 1. Page Visibility API
    document.addEventListener('visibilitychange', () => {
      if (!this.isActive) return;
      if (document.hidden) {
        this.handleFocusLost('cambio_pestana', 'Pestaña oculta o minimizada');
      } else {
        this.handleFocusGained();
      }
    });

    // 2. Pérdida y retorno de Foco de la Ventana
    window.addEventListener('blur', () => {
      if (!this.isActive) return;
      this.handleFocusLost('desenfoque_ventana', 'Pérdida de foco del navegador (cambio de aplicación)');
    });

    window.addEventListener('focus', () => {
      if (!this.isActive) return;
      this.handleFocusGained();
    });

    // 3. Salida de Pantalla Completa
    document.addEventListener('fullscreenchange', () => {
      if (!this.isActive) return;
      if (!document.fullscreenElement) {
        this.handleFocusLost('salida_pantalla_completa', 'Salida del modo de pantalla completa obligatoria');
      }
    });
  }
}

window.FocusMonitor = FocusMonitor;
