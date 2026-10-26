# Evidencias fotográficas de supervisión

## Ausencias frente a la cámara

La preparación solicita además el consentimiento independiente `ausencia-v1-foto`. Sin él, el servidor no permite comenzar/recuperar el examen ni registrar episodios o fotografías de ausencia. Los intentos ya iniciados conservan su vencimiento mientras se acepta la condición nueva.

Cuando `face-api.js` no detecta rostros, el navegador congela el mismo fotograma analizado y envía una fotografía JPEG por episodio. Continúa comunicando observaciones; un rostro detectado nuevamente cierra el registro. Un error de análisis, video pausado o desconexión lo interrumpe, sin afirmar que la persona estuvo ausente durante el fallo técnico. La función detecta **rostros**, no cuerpos completos ni personas fuera del encuadre.

El servidor calcula los segundos entre recepciones, utiliza secuencias para deduplicar peticiones y omite huecos de más de 30 segundos. No acepta del navegador la duración como autoridad. Por el análisis periódico y la latencia, es una **duración estimada desde la primera detección**, no el momento exacto en que la persona salió o regresó. Si se corta la comunicación, parte del episodio puede quedar sin registrar. Se reintenta cada envío una vez y se muestra un aviso si falla; las imágenes o mensajes de un navegador modificado pueden ser falsificados.

Un episodio deja el resultado pendiente de revisión humana, sin anulación automática. El administrador ve cantidad de episodios, segundos acumulados, foto, inicio/fin y advertencias de medición incompleta. El alumno ve el motivo y sus observaciones; las fotografías se sirven exclusivamente por una ruta protegida para administradores, con `Cache-Control: no-store, private`.

Las imágenes se normalizan, cifran con un dominio de clave distinto al de celular y guardan en `instance/evidencias_ausencia/`. Se conserva una por episodio, hasta 60 episodios por intento; tras alcanzar el límite se muestra el fallo de registro. Caducan a los 30 días. El mismo comando `scripts.purgar_evidencias --execute` elimina también las fotografías expiradas de ausencia y conserva el registro de duración, ya sin archivo. El límite global de una ejecución sigue siendo 100 imágenes. Se debe conservar `SECRET_KEY` para descifrarlas.

El arranque añade de forma no destructiva dos columnas de consentimiento a `usuarios` y la tabla `episodios_ausencia`. No genera fotos retrospectivas ni modifica puntuaciones históricas. Para instalaciones existentes, reiniciar la aplicación para aplicar estas adiciones y cargar los scripts versionados nuevos.

## Fotografías de celular

Con consentimiento `celular-v2-fotos`, el examen intenta tomar cuatro fotografías JPEG en cada episodio continuo de detección: la primera en el mismo fotograma que dispara la alerta, antes de esperar la respuesta de la red; las siguientes aproximadamente a los 3, 7 y 10 segundos. La primera se envía tras confirmar el evento en el servidor. Las fotografías aparecen en el informe de resultado, accesible al administrador desde los casos pendientes de revisión humana. No se graba video. Los intentos anteriores a esta función no tienen fotografías retrospectivas.

El servidor comprueba la sesión, el propietario del intento, el consentimiento, el estado del examen, el token CSRF y las observaciones recientes asociadas al episodio. Normaliza el JPEG para quitar metadatos y cifra cada archivo antes de guardarlo en `instance/evidencias/`. Los archivos no son públicos ni se incluyen en Git. Docker utiliza el volumen persistente `evidencias`. La clave de cifrado se deriva de `SECRET_KEY`: hay que conservarla para poder leer fotografías existentes; al cambiarla, las anteriores dejan de descifrarse.

Cada fotografía caduca a los 30 días. Para eliminar archivos y registros expirados, programar una ejecución diaria de este comando en la instalación (tras configurar `.env` y las dependencias):

```powershell
.\.venv\Scripts\python.exe -m scripts.purgar_evidencias --execute
```

Sin `--execute`, el comando solo cuenta hasta 100 registros pendientes. Cada ejecución elimina como máximo 100; si hay más, repetirla. La caducidad impide consultarlas desde la aplicación, pero los archivos físicos permanecen hasta que corre la purga. Se deben respaldar y proteger tanto la base de datos como `instance/evidencias/` de forma coherente; no enviar fotografías ni la clave al repositorio.

Las capturas salen del navegador del examinado. La inferencia puede fallar y un cliente modificado puede falsificar eventos o imágenes. La revisión humana debe valorar las fotografías junto con el resto del contexto; ninguna fotografía aislada demuestra por sí sola que se utilizó un celular. Queda pendiente comprobar en una webcam real el tiempo efectivo y la tasa de falsos positivos/negativos.
