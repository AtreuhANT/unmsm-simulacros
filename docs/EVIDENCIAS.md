# Evidencias fotográficas del detector de celular

Con consentimiento `celular-v2-fotos`, el examen intenta tomar cuatro fotografías JPEG en cada episodio continuo de detección: la primera en el mismo fotograma que dispara la alerta, antes de esperar la respuesta de la red; las siguientes aproximadamente a los 3, 7 y 10 segundos. La primera se envía tras confirmar el evento en el servidor. Las fotografías aparecen en el informe de resultado, accesible al administrador desde los casos pendientes de revisión humana. No se graba video. Los intentos anteriores a esta función no tienen fotografías retrospectivas.

El servidor comprueba la sesión, el propietario del intento, el consentimiento, el estado del examen, el token CSRF y las observaciones recientes asociadas al episodio. Normaliza el JPEG para quitar metadatos y cifra cada archivo antes de guardarlo en `instance/evidencias/`. Los archivos no son públicos ni se incluyen en Git. Docker utiliza el volumen persistente `evidencias`. La clave de cifrado se deriva de `SECRET_KEY`: hay que conservarla para poder leer fotografías existentes; al cambiarla, las anteriores dejan de descifrarse.

Cada fotografía caduca a los 30 días. Para eliminar archivos y registros expirados, programar una ejecución diaria de este comando en la instalación (tras configurar `.env` y las dependencias):

```powershell
.\.venv\Scripts\python.exe -m scripts.purgar_evidencias --execute
```

Sin `--execute`, el comando solo cuenta hasta 100 registros pendientes. Cada ejecución elimina como máximo 100; si hay más, repetirla. La caducidad impide consultarlas desde la aplicación, pero los archivos físicos permanecen hasta que corre la purga. Se deben respaldar y proteger tanto la base de datos como `instance/evidencias/` de forma coherente; no enviar fotografías ni la clave al repositorio.

Las capturas salen del navegador del examinado. La inferencia puede fallar y un cliente modificado puede falsificar eventos o imágenes. La revisión humana debe valorar las fotografías junto con el resto del contexto; ninguna fotografía aislada demuestra por sí sola que se utilizó un celular. Queda pendiente comprobar en una webcam real el tiempo efectivo y la tasa de falsos positivos/negativos.
