/**
 * MÓDULO 3: SCREENSHOT & SHORTCUT GUARD (FASE 6)
 * Intercepta teclas de captura, herramientas de desarrollador, impresión y menú contextual.
 * - Debounce de 3 segundos por tipo de atajo para evitar inundación de telemetría.
 * - Prevención limpia sin alertas bloqueantes invasivas.
 */

class ScreenshotGuard {
  constructor() {
    this.callbacks = null;
    this.isActive = false;
    this.lastReportTimes = {};
    this.DEBOUNCE_MS = 3000;
  }

  init(callbacks) {
    this.callbacks = callbacks || {};
    this.isActive = true;
    this.attachEventListeners();
  }

  stop() {
    this.isActive = false;
  }

  notifyViolation(tipo, descripcion) {
    if (!this.isActive) return;

    const now = Date.now();
    const last = this.lastReportTimes[tipo] || 0;
    if (now - last < this.DEBOUNCE_MS) return;
    this.lastReportTimes[tipo] = now;

    if (this.callbacks.onViolation) {
      this.callbacks.onViolation('screenshot_guard', tipo, descripcion);
    }
  }

  attachEventListeners() {
    // 1. Intercepción de teclas restringidas (PrintScreen, F12, DevTools, Ctrl+P, Ctrl+U)
    window.addEventListener('keydown', (e) => {
      if (!this.isActive) return;

      const isCtrlOrCmd = e.ctrlKey || e.metaKey;
      const key = e.key ? e.key.toUpperCase() : '';

      // PrintScreen
      if (e.key === 'PrintScreen' || e.keyCode === 44) {
        e.preventDefault();
        this.notifyViolation('captura_pantalla', 'Intento de captura de pantalla bloqueado');
        return false;
      }

      // F12 (DevTools)
      if (e.key === 'F12' || e.keyCode === 123) {
        e.preventDefault();
        this.notifyViolation('devtools', 'Apertura de herramientas de desarrollador bloqueada');
        return false;
      }

      // Ctrl + Shift + I / J / C (DevTools / Consola)
      if (isCtrlOrCmd && e.shiftKey && (key === 'I' || key === 'J' || key === 'C')) {
        e.preventDefault();
        this.notifyViolation('devtools', `Intento de acceso a consola o inspector (${key}) bloqueado`);
        return false;
      }

      // Ctrl + U (Código fuente)
      if (isCtrlOrCmd && key === 'U') {
        e.preventDefault();
        this.notifyViolation('codigo_fuente', 'Intento de ver código fuente bloqueado');
        return false;
      }

      // Ctrl + P (Impresión)
      if (isCtrlOrCmd && key === 'P') {
        e.preventDefault();
        this.notifyViolation('impresion', 'Intento de impresión del examen bloqueado');
        return false;
      }
    }, true);

    // 2. Bloqueo de menú contextual (clic derecho)
    document.addEventListener('contextmenu', (e) => {
      if (!this.isActive) return;
      e.preventDefault();
      this.notifyViolation('clic_derecho', 'Uso de menú contextual bloqueado');
      return false;
    });

    // 3. Bloqueo de copiado de enunciados
    document.addEventListener('copy', (e) => {
      if (!this.isActive) return;
      e.preventDefault();
      this.notifyViolation('copia_texto', 'Intento de copia de enunciado bloqueado');
      return false;
    });

    document.addEventListener('cut', (e) => {
      if (!this.isActive) return;
      e.preventDefault();
      return false;
    });
  }
}

window.ScreenshotGuard = ScreenshotGuard;
