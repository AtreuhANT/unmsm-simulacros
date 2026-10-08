/**
 * MONITOR ENGINE - UNMSM PROCTORING MASTER CONTROLLER (FASE 4)
 * Orquestador principal de la interfaz del examen con:
 * - Persistencia continua e incremental en PostgreSQL (respuestas_intento)
 * - Tolerancia estricta a fallos de red (cola de reintento offline + LocalStorage)
 * - Inmunidad ante recargas (F5) con sincronización de reloj en servidor
 * - Supervisión biométrica y anti-trampa Edge
 */

class MonitorEngine {
  constructor(config) {
    this.intentoId = config.intentoId;
    this.tokenSesion = config.tokenSesion;
    this.area = config.area;
    this.preguntas = config.preguntas || [];
    this.storedDescriptors = config.storedDescriptors || [];
    this.segundosRestantes = parseInt(config.segundosRestantes, 10) || (60 * 60);
    this.yaEnCurso = Boolean(config.yaEnCurso);

    this.currentIndex = 0;
    this.respuestas = {}; // { [preguntaId]: 'A' | 'B' | ... }

    // Parse inicial de respuestas ya persistidas en la BD
    if (config.respuestasIniciales) {
      Object.entries(config.respuestasIniciales).forEach(([k, val]) => {
        const qId = parseInt(k, 10);
        if (val && typeof val === 'object' && val.opcion) {
          this.respuestas[qId] = val.opcion;
        } else if (typeof val === 'string') {
          this.respuestas[qId] = val;
        }
      });
    }

    // LocalStorage fallback sync key
    this.storageKey = `unmsm_intento_${this.intentoId || this.tokenSesion}`;
    this.loadLocalStorageBackup();

    this.segundosTranscurridos = 0;
    this.timerInterval = null;
    this.heartbeatInterval = null;
    this.isTerminated = false;

    // Cola de sincronización incremental offline-resilient
    this.syncQueue = [];
    this.isSyncing = false;

    // Submódulos de supervisión
    this.facialMonitor = new FacialPresenceMonitor();
    this.focusMonitor = new FocusMonitor();
    this.screenshotGuard = new ScreenshotGuard();

    // Elementos del DOM
    this.dom = {
      video: document.getElementById('hud-webcam'),
      canvas: document.getElementById('hud-canvas'),
      statusChip: document.getElementById('hud-status-chip'),
      syncBadge: document.getElementById('sync-badge'),
      timerDisplay: document.getElementById('timer-display'),
      questionContainer: document.getElementById('question-container'),
      matrixContainer: document.getElementById('question-matrix'),
      strikesCount: document.getElementById('strikes-count'),
      btnPrev: document.getElementById('btn-prev-q'),
      btnNext: document.getElementById('btn-next-q'),
      btnClear: document.getElementById('btn-clear-q'),
      btnFinish: document.getElementById('btn-finish-exam'),
      // Modal pre-examen
      modalPreExam: document.getElementById('modal-pre-exam'),
      videoPreExam: document.getElementById('pre-exam-video'),
      step1: document.getElementById('pre-step-1'),
      step2: document.getElementById('pre-step-2'),
      btnVerifyFace: document.getElementById('btn-verify-face'),
      btnStartExamFull: document.getElementById('btn-start-exam-full'),
      preStatusText: document.getElementById('pre-status-text'),
      distanceFill: document.getElementById('distance-fill'),
      distanceText: document.getElementById('distance-text'),
      checkHands: document.getElementById('check-hands-desk')
    };

    this.cameraStream = null;
    this.attemptsLeft = 3;
    this.isFaceVerified = false;
  }

  // Inicialización del motor
  init() {
    this.setupNetworkListeners();
    this.renderQuestionMatrix();

    if (this.yaEnCurso) {
      // Examen ya en curso (recuperación ante F5 o reconexión)
      if (this.dom.modalPreExam) {
        this.dom.modalPreExam.style.display = 'none';
      }
      this.startExamSession(false);
    } else {
      this.initPreExamModal();
    }
  }

  // =========================================================================
  // DETECCIÓN DE RED Y ESTADOS DE SINCRONIZACIÓN (EX-04)
  // =========================================================================
  setupNetworkListeners() {
    window.addEventListener('online', () => {
      this.updateSyncBadge('syncing', 'Reconectado, sincronizando...');
      this.processSyncQueue();
    });
    window.addEventListener('offline', () => {
      this.updateSyncBadge('offline', '⚠️ Sin conexión (guardado en búfer local)');
    });
  }

  updateSyncBadge(status, text) {
    if (!this.dom.syncBadge) return;
    this.dom.syncBadge.className = `sync-badge ${status}`;

    let icon = '✓';
    if (status === 'syncing') icon = '<span class="sync-spin">⟳</span>';
    else if (status === 'offline') icon = '⚠️';

    this.dom.syncBadge.innerHTML = `<span>${icon}</span> ${text}`;
  }

  // =========================================================================
  // FASE PRE-EXAMEN: VERIFICACIÓN EN 2 PASOS
  // =========================================================================
  async initPreExamModal() {
    try {
      this.dom.preStatusText.textContent = 'Cargando modelos biométricos locales...';
      await faceapi.nets.tinyFaceDetector.loadFromUri('/static/models');
      await faceapi.nets.faceLandmark68TinyNet.loadFromUri('/static/models');
      await faceapi.nets.faceRecognitionNet.loadFromUri('/static/models');

      // Activar webcam para verificación de identidad
      this.cameraStream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: 'user' },
        audio: false
      });
      if (this.dom.videoPreExam) this.dom.videoPreExam.srcObject = this.cameraStream;
      if (this.dom.video) this.dom.video.srcObject = this.cameraStream;

      this.dom.preStatusText.textContent = 'Cámara activa. Mira de frente y presiona "Verificar Identidad".';
      this.dom.btnVerifyFace.disabled = false;

      this.dom.btnVerifyFace.addEventListener('click', () => this.verifyPreExamIdentity());
    } catch (err) {
      console.error('Error al inicializar cámara pre-examen:', err);
      this.dom.preStatusText.textContent = 'Error al acceder a la cámara. Por favor autoriza los permisos en el navegador.';
      alert('Se requiere acceso a la cámara web para rendir el simulacro.');
    }

    // Paso 2: Confirmación de manos y arranque en pantalla completa
    this.dom.checkHands.addEventListener('change', () => {
      this.dom.btnStartExamFull.disabled = !this.dom.checkHands.checked;
    });

    this.dom.btnStartExamFull.addEventListener('click', () => {
      this.startExamSession(true);
    });
  }

  async verifyPreExamIdentity() {
    this.dom.btnVerifyFace.disabled = true;
    this.dom.preStatusText.textContent = 'Analizando biometría facial...';

    try {
      const detection = await faceapi
        .detectSingleFace(this.dom.videoPreExam, new faceapi.TinyFaceDetectorOptions({ inputSize: 320, scoreThreshold: 0.6 }))
        .withFaceLandmarks(true)
        .withFaceDescriptor();

      if (!detection) {
        this.dom.preStatusText.textContent = 'No se detectó un rostro claro. Centra tu rostro con buena iluminación.';
        this.dom.btnVerifyFace.disabled = false;
        return;
      }

      // Si no hay descriptores previos guardados, auto-enrolar como primera referencia
      if (!this.storedDescriptors || this.storedDescriptors.length === 0) {
        this.dom.preStatusText.textContent = 'Registrando tu rostro como referencia de identidad...';
        const nuevoDescriptor = Array.from(detection.descriptor);
        
        await fetch('/api/intento/enrolar-facial', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ descriptores: [nuevoDescriptor] })
        });
        
        this.storedDescriptors = [nuevoDescriptor];
        this.isFaceVerified = true;
        this.dom.preStatusText.textContent = '¡Rostro registrado! Avanzando al Paso 2...';
        this.dom.preStatusText.style.color = '#10b981';

        setTimeout(() => {
          this.dom.step1.classList.remove('active');
          this.dom.step2.classList.add('active');
          document.getElementById('pill-step-1').classList.remove('active');
          document.getElementById('pill-step-2').classList.add('active');
        }, 1000);
        return;
      }

      // Convertir descriptores almacenados a Float32Array y comparar 1:1
      const storedFloatArrays = this.storedDescriptors.map(d => new Float32Array(d));
      let minDistance = 999.0;

      for (const stored of storedFloatArrays) {
        const dist = faceapi.euclideanDistance(detection.descriptor, stored);
        if (dist < minDistance) minDistance = dist;
      }

      const percent = Math.min(100, Math.round((1 - minDistance) * 100));
      this.dom.distanceFill.style.width = percent + '%';
      this.dom.distanceText.textContent = `Distancia euclidiana: ${minDistance.toFixed(3)} (Umbral exigido <= 0.55)`;

      if (minDistance <= 0.55) {
        this.dom.distanceFill.style.backgroundColor = '#10b981';
        this.dom.preStatusText.textContent = '¡Identidad verificada correctamente! Avanzando al Paso 2...';
        this.dom.preStatusText.style.color = '#10b981';
        this.isFaceVerified = true;

        setTimeout(() => {
          this.dom.step1.classList.remove('active');
          this.dom.step2.classList.add('active');
          document.getElementById('pill-step-1').classList.remove('active');
          document.getElementById('pill-step-2').classList.add('active');
        }, 1200);
      } else {
        this.attemptsLeft--;
        this.dom.distanceFill.style.backgroundColor = '#ef4444';
        this.dom.preStatusText.textContent = `Rostro no coincide con el postulante registrado. Intentos restantes: ${this.attemptsLeft}`;
        this.dom.preStatusText.style.color = '#ef4444';

        if (this.attemptsLeft <= 0) {
          alert('Acceso bloqueado: La identidad biométrica no coincide tras 3 intentos. Serás redirigido al panel.');
          window.location.replace('/dashboard');
        } else {
          this.dom.btnVerifyFace.disabled = false;
        }
      }
    } catch (err) {
      console.error('Error durante la verificación pre-examen:', err);
      this.dom.btnVerifyFace.disabled = false;
    }
  }

  // =========================================================================
  // INICIO OFICIAL DEL EXAMEN Y MONITOREO CONTINUO
  // =========================================================================
  async startExamSession(withWebcamVerification = true) {
    try {
      if (document.documentElement.requestFullscreen) {
        await document.documentElement.requestFullscreen();
      }
    } catch (e) {
      console.warn('Pantalla completa no disponible o rechazada:', e);
    }

    if (this.dom.modalPreExam) {
      this.dom.modalPreExam.style.display = 'none';
    }

    this.startTimer();

    // Iniciar supervisión
    if (withWebcamVerification && this.cameraStream) {
      this.initProctoringModules();
    } else {
      // Re-conectar cámara en caso de recarga
      try {
        if (!this.cameraStream) {
          this.cameraStream = await navigator.mediaDevices.getUserMedia({
            video: { width: 640, height: 480, facingMode: 'user' },
            audio: false
          });
          if (this.dom.video) this.dom.video.srcObject = this.cameraStream;
        }
      } catch (e) {
        console.warn('Cámara en sesión recuperada:', e);
      }
      this.initProctoringModules();
    }

    this.loadQuestion(0);
    this.bindExamControls();
  }

  initProctoringModules() {
    const callbacks = {
      onViolation: (modulo, tipo, desc) => this.handleViolation(modulo, tipo, desc),
      onFatalViolation: (modulo, tipo, desc) => this.handleFatalViolation(modulo, tipo, desc),
      onStatusChange: (status, message) => {
        if (this.dom.statusChip) {
          this.dom.statusChip.className = `status-chip ${status}`;
          this.dom.statusChip.textContent = message;
        }
      },
      onStrikeUpdate: (strikes, maxStrikes) => {
        if (this.dom.strikesCount) {
          this.dom.strikesCount.textContent = `${strikes} / ${maxStrikes}`;
        }
      }
    };

    if (this.dom.video && this.dom.canvas) {
      this.facialMonitor.init(this.dom.video, this.dom.canvas, this.storedDescriptors, callbacks);
    }
    this.focusMonitor.init(callbacks);
    this.screenshotGuard.init(callbacks);
  }

  async handleViolation(modulo, tipo, descripcion) {
    if (this.isTerminated) return;
    console.warn(`[SUPERVISIÓN] ${modulo} -> ${tipo}: ${descripcion}`);
    this.showViolationToast(descripcion);

    try {
      await fetch('/api/evento-monitoreo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          modulo: modulo,
          tipo: tipo,
          descripcion: descripcion,
          segundo_examen: this.segundosTranscurridos,
          token_sesion: this.tokenSesion
        })
      });
    } catch (err) {
      console.error('Error al enviar evento de monitoreo:', err);
    }
  }

  async handleFatalViolation(modulo, tipo, motivo) {
    if (this.isTerminated) return;
    console.warn(`[SUPERVISIÓN CRÍTICA] ${modulo} -> ${tipo}: ${motivo}`);

    // Registrar observación grave para auditoría humana del evaluador (MO-02)
    await this.handleViolation(modulo, `grave_${tipo}`, `Incidencia Grave: ${motivo}`);

    // Notificación clara y no destructiva al postulante
    this.showViolationToast(`🚨 OBSERVACIÓN GRAVE REGISTRADA: ${motivo}. Este evento será auditado formalmente.`);
  }

  showViolationToast(mensaje) {
    const toast = document.createElement('div');
    toast.className = 'alert alert-danger';
    toast.style.position = 'fixed';
    toast.style.top = '75px';
    toast.style.right = '20px';
    toast.style.zIndex = '9999';
    toast.style.maxWidth = '380px';
    toast.style.boxShadow = 'var(--shadow-lg)';
    toast.style.borderLeft = '4px solid var(--wine)';
    toast.innerHTML = `<strong>⚠️ Supervisión Académica:</strong><br>${mensaje}`;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 4500);
  }

  // =========================================================================
  // TEMPORIZADOR Y SINCRONIZACIÓN DE RELOJ CON POSTGRESQL (EX-02, EX-06)
  // =========================================================================
  startTimer() {
    if (this.timerInterval) clearInterval(this.timerInterval);
    if (this.heartbeatInterval) clearInterval(this.heartbeatInterval);

    this.updateTimerDisplay();

    this.timerInterval = setInterval(() => {
      this.segundosRestantes--;
      this.segundosTranscurridos++;
      this.updateTimerDisplay();

      if (this.segundosRestantes <= 0) {
        clearInterval(this.timerInterval);
        if (this.heartbeatInterval) clearInterval(this.heartbeatInterval);
        alert('⏳ El tiempo oficial del examen ha concluido. Entregando tus respuestas...');
        this.finalizarExamen('COMPLETADO', null);
      }
    }, 1000);

    // Heartbeat cada 60s para sincronización con PostgreSQL y control de drift
    this.heartbeatInterval = setInterval(async () => {
      if (this.isTerminated || !navigator.onLine) return;
      try {
        const resp = await fetch('/api/intento/activo');
        if (resp.ok) {
          const data = await resp.json();
          if (data.activo && data.segundos_restantes !== undefined) {
            const serverDiff = Math.abs(data.segundos_restantes - this.segundosRestantes);
            if (serverDiff > 3) {
              console.log(`[RELOJ] Sincronizando drift con PostgreSQL: ${this.segundosRestantes}s -> ${data.segundos_restantes}s`);
              this.segundosRestantes = data.segundos_restantes;
            }
          } else if (!data.activo) {
            this.finalizarExamen('COMPLETADO', null);
          }
        }
      } catch (e) {
        console.warn('[RELOJ] Heartbeat no respondió:', e);
      }
    }, 60000);
  }

  updateTimerDisplay() {
    const restante = Math.max(0, this.segundosRestantes);
    const horas = Math.floor(restante / 3600);
    const minutos = Math.floor((restante % 3600) / 60);
    const segs = restante % 60;

    const pad = (n) => String(n).padStart(2, '0');
    this.dom.timerDisplay.textContent = horas > 0 
      ? `${pad(horas)}:${pad(minutos)}:${pad(segs)}`
      : `${pad(minutos)}:${pad(segs)}`;

    if (restante <= 300 && restante > 60) {
      this.dom.timerDisplay.className = 'timer-display warning';
    } else if (restante <= 60) {
      this.dom.timerDisplay.className = 'timer-display danger';
    } else {
      this.dom.timerDisplay.className = 'timer-display';
    }
  }

  // =========================================================================
  // PERSISTENCIA CONTINUA E INCREMENTAL DE RESPUESTAS (EX-03, EX-04)
  // =========================================================================
  queueAnswerSync(preguntaId, opcion) {
    this.updateSyncBadge('syncing', 'Guardando...');
    this.syncQueue.push({
      preguntaId: parseInt(preguntaId, 10),
      opcion: opcion,
      timestamp: Date.now()
    });
    this.processSyncQueue();
  }

  async processSyncQueue() {
    if (this.isSyncing || this.syncQueue.length === 0) return;

    if (!navigator.onLine) {
      this.updateSyncBadge('offline', '⚠️ Sin conexión (guardado en búfer local)');
      return;
    }

    this.isSyncing = true;
    while (this.syncQueue.length > 0) {
      const item = this.syncQueue[0];
      try {
        const resp = await fetch('/api/intento/respuesta', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            intento_id: this.intentoId,
            pregunta_id: item.preguntaId,
            opcion_seleccionada: item.opcion,
            es_blanco: (item.opcion === null),
            marcado_revision: false
          })
        });

        if (!resp.ok) {
          const errData = await resp.json().catch(() => ({}));
          if (resp.status === 400 && errData.error && errData.error.includes('expirado')) {
            this.syncQueue = [];
            this.isSyncing = false;
            alert('El tiempo oficial del examen ha concluido.');
            this.finalizarExamen('COMPLETADO', null);
            return;
          }
          throw new Error(errData.error || 'Error al persistir');
        }

        // Remueve elemento confirmado por PostgreSQL
        this.syncQueue.shift();
      } catch (err) {
        console.warn('[SYNC] Error al sincronizar respuesta:', err);
        this.updateSyncBadge('offline', '⚠️ Sin conexión (guardado en búfer local)');
        this.isSyncing = false;
        return;
      }
    }

    this.isSyncing = false;
    this.updateSyncBadge('synced', 'Guardado en servidor ✓');
  }

  saveLocalStorageBackup() {
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(this.respuestas));
    } catch (e) {}
  }

  loadLocalStorageBackup() {
    try {
      const raw = localStorage.getItem(this.storageKey);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (parsed && typeof parsed === 'object') {
          Object.entries(parsed).forEach(([k, v]) => {
            const intK = parseInt(k, 10);
            if (!this.respuestas[intK] && v) {
              this.respuestas[intK] = v;
            }
          });
        }
      }
    } catch (e) {}
  }

  clearLocalStorageBackup() {
    try {
      localStorage.removeItem(this.storageKey);
    } catch (e) {}
  }

  // =========================================================================
  // NAVEGACIÓN Y RENDERIZADO DE PREGUNTAS
  // =========================================================================
  loadQuestion(index) {
    if (index < 0 || index >= this.preguntas.length) return;
    this.currentIndex = index;
    const q = this.preguntas[index];
    const qId = parseInt(q.id, 10);

    document.getElementById('question-number-badge').textContent = `Pregunta ${index + 1} de ${this.preguntas.length}`;
    document.getElementById('question-section-tag').textContent = q.seccion || 'Área General';
    document.getElementById('question-enunciado').textContent = q.enunciado;

    const optionsContainer = document.getElementById('options-list');
    optionsContainer.innerHTML = '';

    const seleccionActual = this.respuestas[qId] || this.respuestas[String(q.id)] || null;

    Object.entries(q.opciones).forEach(([letra, texto]) => {
      const optDiv = document.createElement('div');
      optDiv.className = `option-item ${seleccionActual === letra ? 'selected' : ''}`;
      optDiv.id = `opt-${qId}-${letra}`;
      optDiv.innerHTML = `
        <div class="option-letter">${letra}</div>
        <div class="option-text">${texto}</div>
      `;

      optDiv.addEventListener('click', () => {
        this.selectOption(qId, letra);
      });

      optionsContainer.appendChild(optDiv);
    });

    this.dom.btnPrev.disabled = (index === 0);
    this.dom.btnNext.textContent = (index === this.preguntas.length - 1) ? 'Revisar Todo' : 'Siguiente Pregunta →';

    this.updateMatrixSelection();
  }

  selectOption(preguntaId, letra) {
    const pid = parseInt(preguntaId, 10);
    const isDeselect = (this.respuestas[pid] === letra);
    const newOption = isDeselect ? null : letra;

    if (isDeselect) {
      delete this.respuestas[pid];
    } else {
      this.respuestas[pid] = letra;
    }

    this.saveLocalStorageBackup();
    this.loadQuestion(this.currentIndex);
    this.queueAnswerSync(pid, newOption);
  }

  clearCurrentOption() {
    const q = this.preguntas[this.currentIndex];
    if (!q) return;
    const pid = parseInt(q.id, 10);
    delete this.respuestas[pid];

    this.saveLocalStorageBackup();
    this.loadQuestion(this.currentIndex);
    this.queueAnswerSync(pid, null);
  }

  renderQuestionMatrix() {
    this.dom.matrixContainer.innerHTML = '';
    this.preguntas.forEach((q, idx) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'matrix-btn';
      btn.id = `matrix-btn-${idx}`;
      btn.textContent = idx + 1;
      btn.addEventListener('click', () => this.loadQuestion(idx));
      this.dom.matrixContainer.appendChild(btn);
    });
  }

  updateMatrixSelection() {
    this.preguntas.forEach((q, idx) => {
      const btn = document.getElementById(`matrix-btn-${idx}`);
      if (!btn) return;

      const qId = parseInt(q.id, 10);
      btn.classList.remove('active', 'answered');
      if (this.respuestas[qId] || this.respuestas[String(q.id)]) {
        btn.classList.add('answered');
      }
      if (idx === this.currentIndex) {
        btn.classList.add('active');
      }
    });

    const contestadas = Object.keys(this.respuestas).length;
    const counterEl = document.getElementById('nav-grid-counter');
    if (counterEl) {
      counterEl.textContent = `${contestadas} / ${this.preguntas.length} respondidas`;
    }
  }

  bindExamControls() {
    this.dom.btnPrev.onclick = () => {
      if (this.currentIndex > 0) this.loadQuestion(this.currentIndex - 1);
    };

    this.dom.btnNext.onclick = () => {
      if (this.currentIndex < this.preguntas.length - 1) {
        this.loadQuestion(this.currentIndex + 1);
      }
    };

    this.dom.btnClear.onclick = () => {
      this.clearCurrentOption();
    };

    this.dom.btnFinish.onclick = () => {
      const contestadas = Object.keys(this.respuestas).length;
      const enBlanco = this.preguntas.length - contestadas;

      const confirmar = confirm(
        `¿Deseas finalizar tu examen de admisión?\n\n` +
        `• Preguntas respondidas: ${contestadas}\n` +
        `• Preguntas en blanco: ${enBlanco}\n\n` +
        `Recuerda que cada respuesta incorrecta descuenta -1.125 puntos.`
      );

      if (confirmar) {
        this.finalizarExamen('COMPLETADO', null);
      }
    };
  }

  // =========================================================================
  // FINALIZACIÓN E IDEMPOTENCIA ESTRICTA (EX-05)
  // =========================================================================
  stopAllMonitors() {
    if (this.timerInterval) clearInterval(this.timerInterval);
    if (this.heartbeatInterval) clearInterval(this.heartbeatInterval);
    this.facialMonitor.stop();
    this.focusMonitor.stop();
    this.screenshotGuard.stop();
    if (this.cameraStream) {
      this.cameraStream.getTracks().forEach(track => track.stop());
    }
  }

  async finalizarExamen(estado = 'COMPLETADO', motivo = null) {
    if (this.isTerminated) return;
    this.isTerminated = true;

    this.stopAllMonitors();
    this.updateSyncBadge('syncing', 'Finalizando y calificando...');
    await this.submitFinalExam(estado, motivo);
  }

  async submitFinalExam(estado, motivo) {
    try {
      const response = await fetch('/api/guardar-resultado', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token_sesion: this.tokenSesion,
          area: this.area,
          respuestas: this.respuestas,
          tiempo_segundos: this.segundosTranscurridos,
          estado: estado,
          motivo_anulacion: motivo
        })
      });

      const resData = await response.json();
      this.clearLocalStorageBackup();

      if (resData.redirect) {
        if (document.fullscreenElement) {
          try { await document.exitFullscreen(); } catch (e) {}
        }
        window.location.replace(resData.redirect);
      } else {
        alert('Resultado procesado correctamente.');
        window.location.replace('/dashboard');
      }
    } catch (err) {
      console.error('Error al enviar resultado final:', err);
      alert('Hubo un problema de conexión al finalizar. Tus respuestas están resguardadas en el servidor. Reintentando...');
      setTimeout(() => this.submitFinalExam(estado, motivo), 3000);
    }
  }
}

window.MonitorEngine = MonitorEngine;
