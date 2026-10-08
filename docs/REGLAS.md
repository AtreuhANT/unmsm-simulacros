# REGLAS DE PROCTORING Y SANCIONES

Documento extraído de la sección 7 de `ESPECIFICACION.md`. Es referencia de requisitos, no afirmación de implementación actual. El servidor es autoridad; los eventos del cliente son datos no confiables y requieren validación. Las anulaciones automáticas son provisionales y revisables.

## 7. REGLAS DE MONITOREO Y SANCIONES (CONFIGURABLES EN `config.py` Y DOCUMENTADAS EN `docs/REGLAS.md`)

El **servidor** asigna la severidad según el `tipo` (nunca confíes en la severidad que envíe el cliente) y aplica las reglas en `services/riesgo.py` cada vez que llega un lote de eventos o un heartbeat. Cada evento enviado por el cliente representa una **ventana confirmada** (no un frame suelto).

| Tipo de evento | Qué representa un evento | Severidad | Efecto |
|---|---|---|---|
| `rostro_ausente` | Ventana de 10 s sin rostro | LEVE | 1.º: advertencia. ≥ 6 ventanas acumuladas (60 s): `revision = PENDIENTE`. No anula. |
| `multiples_rostros` | Ventana de 5 s con ≥ 2 rostros (confianza ≥ 0.7 en ≥ 80% de los frames de la ventana) | GRAVE | Captura de evidencia en la 1.ª ventana y cada 3.ª. ≥ 3 ventanas consecutivas, o ≥ 6 acumuladas: **anulación provisional**. |
| `identidad_fallida` | Verificación periódica de identidad que no supera el umbral | LEVE | Reintento a los 10 s. **3 fallos consecutivos:** anulación provisional + evidencia. |
| `salida_foco` (`tab_switch`, `window_blur`, `fullscreen_exit`) | Salida de la ventana/pantalla completa. El servidor agrupa eventos del mismo episodio (misma ventana de 3 s) como **una** salida | LEVE | 1.ª y 2.ª: advertencia visible con contador. **3.ª: anulación provisional.** |
| `camara_perdida` | Pista de video terminada o cámara desconectada | LEVE | Overlay bloqueante para restablecerla. Si no se restablece en 60 s: anulación provisional. |
| `celular_detectado` | Detección de celular (opcional) | INFO | Solo evidencia. ≥ 3 detecciones: `revision = PENDIENTE`. **Nunca anula.** |
| `atajo_bloqueado` (PrintScreen, F12, Ctrl+U, etc.) | Intento de atajo | INFO | Solo registro. **Nunca sanciona.** |
| `sin_senal` | Generado por el servidor: sin heartbeat > 45 s | LEVE | ≥ 5 min acumulados: `revision = PENDIENTE`. No anula. |

**Anulación provisional:** `estado = 'ANULADO'`, `revision = 'PENDIENTE'`, `motivo_anulacion` con el motivo exacto. El cliente recibe la orden de terminar en el siguiente heartbeat y se muestra la pantalla de resultado con las observaciones. El supervisor puede **confirmar** (`ANULACION_CONFIRMADA`) o **reponer** (`REPUESTO`) con una nota; toda decisión queda en `auditoria`.

**Heartbeat:** el cliente envía uno cada 10 s; la respuesta trae el tiempo restante (según el servidor), el estado del intento y las advertencias vigentes. **Sin tareas en segundo plano:** la brecha de heartbeat se registra cuando llega el siguiente heartbeat o cuando el supervisor consulta.

**Tiempo:** `limite_en = inicio_en + duración`, calculado por el servidor al iniciar. Si el intento sigue `EN_CURSO` pasado `limite_en` + 30 s de gracia, el servidor lo finaliza al detectarlo (*finalización perezosa*) con las respuestas ya autoguardadas. `tiempo_segundos` lo calcula siempre el servidor.

