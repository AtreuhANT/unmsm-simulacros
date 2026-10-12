# Modelo del reto de ojos

- Archivo: `face_landmarker.task`, versión publicada `float16/1` (3 758 596 bytes).
- Origen: https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task
- SHA-256 de la descarga: `64184e229b263107bc2b804c6625db1341ff2bb731874b0bcc2fe6544e0bc9ff`.
- API utilizada: [Face Landmarker para web](https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker/web_js), con `outputFaceBlendshapes` y señales `eyeBlinkLeft`/`eyeBlinkRight`.
- Usa la biblioteca y WASM locales de MediaPipe ya incorporados. Procesa imágenes de la cámara en el navegador; el módulo del reto no almacena ni envía imágenes o puntuaciones oculares al servidor.
- Es un reto básico de movimiento, no una certificación de presencia real ni una defensa contra videos reproducidos. No modifica las plantillas existentes de identidad de face-api.
- La licencia exacta de redistribución de estos pesos sigue pendiente de verificación antes de despliegue público; la licencia de los ejemplos de la documentación no se asume aplicable al binario.
