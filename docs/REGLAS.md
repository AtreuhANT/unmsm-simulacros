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

## Implementación aprobada de supervisión (2026-10-11)

### Inicio oficial y comprobación periódica de presencia

- Abrir la página del examen sin un intento activo muestra la interfaz de verificación, sin preguntas ni cronómetro oficial. Tras verificar identidad, entorno, cámara y modelos, una petición protegida por CSRF crea o recupera el intento y entrega las preguntas. El servidor fija inicio y vencimiento de forma atómica. Un examen ya iniciado sigue consumiendo tiempo durante recargas o problemas técnicos posteriores.
- Aproximadamente 45 segundos después de entrar y luego cada 8 minutos se propone un reto breve de cierres oculares con cantidad variable. Si no se confirma, se registra `presencia_no_confirmada` y se solicita revisión humana, sin anulación automática. Fallos técnicos del detector se reintentan y se muestran como tales.
- La coincidencia biométrica no demuestra presencia real. Un video reproducido, una cámara virtual o un cliente modificado pueden superar o evadir retos del navegador. El reto es un indicio adicional, no una garantía anti-suplantación.

### Evidencias fotográficas de celular

- Con consentimiento específico `celular-v2-fotos`, el detector congela el primer fotograma positivo antes de esperar la respuesta del servidor; luego intenta capturas aproximadamente a los 3, 7 y 10 segundos del episodio. Son cuatro JPEG como máximo por episodio. No graba video.
- El servidor vincula cada imagen con un intento, usuario y episodio, y exige observaciones recientes para aceptar la captura del momento indicado. El cliente no decide sanciones ni resultados.
- Las imágenes se guardan cifradas fuera de los archivos públicos y solo el administrador puede verlas en el informe de revisión. Caducan a los 30 días y requieren ejecutar la purga periódica descrita en [EVIDENCIAS.md](EVIDENCIAS.md).
- La detección y las fotos son indicios para revisión humana, no prueba concluyente de uso indebido. Un navegador manipulado podría alterar la captura; pueden existir falsos positivos y negativos.

- La tercera salida de foco comunicada al servidor cierra el intento como `ANULADO` provisional, crea un resultado con `revision = PENDIENTE` y muestra al alumno la causa. Las dos primeras muestran una advertencia. Un identificador por episodio evita contar dos veces el mismo envío. El administrador puede confirmar la anulación o reponer el resultado y debe dejar una nota; la decisión queda auditada.
- La detección opcional de celular usa inferencia de cámara en el navegador y requiere consentimiento antes de iniciar el examen. Si el servidor recibe observaciones continuas durante al menos 10 segundos, marca el intento para revisión humana. No cierra automáticamente el examen por celular. Al entregar, el resultado queda fuera del ranking mientras esté pendiente; el alumno ve el motivo de la revisión.
- La preparación exige un reto de parpadeo para reducir el uso de fotografías inmóviles. Si falla, muestra una alerta y permite reintentar; no sanciona por sí solo. El reto no demuestra presencia real frente a videos o ataques sofisticados.
- La API del navegador permite observar pérdida de foco o visibilidad de esta página. No permite enumerar pestañas, páginas ni otros navegadores abiertos; por tanto no se afirma detectar su mera existencia. Los avisos del navegador son señales para revisión y pueden fallar o manipularse.

