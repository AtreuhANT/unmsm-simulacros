/**
 * MÓDULO 4: MOBILE & DEVICE GUARD
 * Validación en el cliente para asegurar entorno exclusivo de PC / Laptop de escritorio.
 */

class MobileGuard {
  static isMobileDevice() {
    const ua = navigator.userAgent || navigator.vendor || window.opera;
    const isMobileUA = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(ua);
    const hasTouchScreen = ('ontouchstart' in window) || (navigator.maxTouchPoints > 1);
    const isSmallScreen = window.innerWidth < 800;

    return isMobileUA || (hasTouchScreen && isSmallScreen);
  }

  static enforceDesktop() {
    if (MobileGuard.isMobileDevice()) {
      window.location.replace('/incompatible');
    }
  }
}

// Ejecutar comprobación inmediata
MobileGuard.enforceDesktop();
window.MobileGuard = MobileGuard;
