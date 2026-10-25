# Vista previa del PDF del área A

## Refinamiento actual: SVG limpios y ecuaciones estructuradas

Las 14 figuras antes recortadas se reconstruyen como SVG con curvas, trazos, etiquetas y detalles vectoriales a partir de la geometría del PDF. Se omite la capa editorial de fondo de color específico, conservando datos y proporciones de los ejercicios. Los puntos inline del dominó se convierten en 26 círculos; pequeños sombreados se trazan como superficies vectoriales y el agua de la 83 usa un relleno geométrico con gradiente. Los archivos SVG no contienen mapas de bits incrustados. La cuadrícula 24 continúa dibujándose en el DOM. La infografía de la primera lectura se recompuso en ocho pasos HTML con su fuente conservada.

Las ecuaciones señaladas utilizan MathML nativo local mediante [formato_academico.js](../static/js/formato_academico.js): fracciones verticales, subíndices, exponentes, radicales, conjugados y vectores. No se descargan bibliotecas ni fuentes matemáticas externas. La 38 conserva las proposiciones del PDF, incluidas las que deben evaluarse como falsas; no se alteraron sus valores para convertirlas en afirmaciones verdaderas. La 64 tenía un error de segmentación en las abreviaturas de fechas, corregido a «2500 a. C. – 100 d. C.». La 84 distingue la flecha de B, la omega, el exponente −5, el versor y las unidades. Las expresiones largas pueden desplazarse dentro de su propio bloque en pantallas estrechas.

[refinar_graficos_area_a.py](../scripts/refinar_graficos_area_a.py) aplica esta etapa después de la conversión textual, seguida de `completar_area_a.py`. Requiere el entorno de importación con PyMuPDF, no el servidor Flask. Las páginas originales del panel de referencia conservan el documento tal como se recibió; los nuevos esquemas limpios son los que aparecen junto a cada enunciado.

Verificación: trece pruebas aisladas OK, SVG XML válidos sin elementos `image` ni raster incrustado, 26 puntos del dominó y etiquetas químicas presentes. Recorrido en navegador de 100 preguntas, sin errores JavaScript y cinco opciones por pregunta; fracciones, conjugados y exponentes comprobados en el DOM MathML. Sin desbordamiento a 390 px en las expresiones revisadas. La selección permanece y no se abren pestañas por las figuras.

## Estado actual: 100 preguntas textuales y figuras independientes

Los 100 enunciados y sus alternativas se muestran como texto seleccionable. Se convirtieron las preguntas 21–100 y se normalizaron raíces, potencias, fracciones, vectores y fórmulas químicas cotejando las expresiones complejas con los recortes originales. Las claves no cambian. Se conservan las peculiaridades del documento, incluida la unidad cm³ que el original imprime en el dato de área de la pregunta 36; esta transcripción no valida académicamente el material.

Se mantienen figuras independientes en 21, 26, 27, 28, 29, 30, 35, 36, 37, 41, 81, 83, 84 y 91. La 83 repetida en la solicitud se consideró una sola vez; también se conserva la 84 porque necesita su esquema. En la **24**, las dieciséis casillas del borde se reconstruyen con SVG directamente en el DOM: no se descarga un bitmap. La infografía de HV continúa como figura compartida. La tabla de sustancias de la 90 es una tabla HTML; las proposiciones de la 91 se colocan después de sus estructuras químicas. Las palabras de la 49 mantienen el subrayado.

Las imágenes, continuaciones y páginas de referencia ya no están envueltas en enlaces. Tampoco hay citas que abran ventanas externas en la vista del examen. Los clics sobre figuras no navegan ni crean pestañas. El panel de referencia se despliega en la misma página. No se cambió la supervisión ni se probó un intento oficial con cámara: esta comprobación verifica navegación y presentación de la vista previa.

La fuente editable sigue siendo [edicion_area_a.json](../data/examenes/edicion_area_a.json). [convertir_area_a_texto.py](../scripts/convertir_area_a_texto.py) regenera la conversión específica de 21–100 desde los datos originales y el PDF; después se ejecuta [completar_area_a.py](../scripts/completar_area_a.py) para aplicarla a los datos públicos y al banco privado. Regenerar esta extracción reemplaza las ediciones de 21–100; las correcciones manuales posteriores deben conservarse antes de repetirla. El preparador inicial de HV preserva ahora las ediciones de los otros cursos.

Verificación: once pruebas aisladas OK, recorrido en navegador de las 100 preguntas con cinco alternativas cada una, carga de las 14 figuras, cuadrícula SVG con 16 casillas, tabla con seis filas y continuación de vitaminas completa. Clics en SVG e imagen: una pestaña antes y después; cero enlaces de imágenes. Selección conservada al navegar y pantalla de 390 px sin desbordamiento. Jinja del dashboard compilada, diagnósticos sin errores y `git diff --check` sin errores.

Las siguientes secciones conservan los antecedentes de las etapas anteriores.

## Edición textual por bloques y navegador por cursos

Las preguntas 1–20 se presentan como texto HTML seleccionable: las diez originales y las diez de HV. HV contiene tres lecturas compartidas: Texto N.º 1 (11–13), Texto N.º 2 (14–17, con Texto A y Texto B) y Texto N.º 3 (18–20). Las lecturas se guardan una vez y cada pregunta referencia su lectura. La infografía de la primera lectura se conserva como imagen completa; enunciados, párrafos y alternativas son texto. La pregunta 16 mantiene separadas sus proposiciones y la alternativa E de la 18 recupera la última línea omitida por el primer recorte.

El navegador sigue la referencia visual del usuario con títulos de curso y subgrupos de lecturas, usando los colores existentes. Conserva contador global, selección y pregunta actual. Incluye Actitudinales 1–10 y todos los cursos hasta Biología. Utiliza la numeración del **examen**, que difiere de los rangos desplazados del solucionario: H.L.M. 21–30, Aritmética 31–34, Geometría 35–37, Álgebra 38–40, Trigonometría 41–42, Lenguaje 43–49, Literatura 50–53, Psicología 54–59, Educación Cívica 60–63, Historia del Perú 64–66, Historia Universal 67–68, Geografía 69–72, Economía 73–76, Filosofía 77–80, Física 81–85, Química 86–92 y Biología 93–100. Cada número aparece una sola vez.

La transición es por bloques para permitir revisión: las preguntas 21–100 conservan sus recortes hasta transcribir y revisar sus fórmulas, tablas y figuras. La referencia de página completa se descarga solo al abrir su panel; HV no descarga recortes de preguntas. No se modifica la calificación ni el banco activo.

La edición estructurada se conserva en [edicion_area_a.json](../data/examenes/edicion_area_a.json). El script [preparar_textos_area_a.py](../scripts/preparar_textos_area_a.py) extrae y normaliza esta primera etapa desde el PDF específico; usa PyMuPDF solo para la importación. El script de completado reaplica la edición guardada al regenerar la vista, preservando las claves privadas. Para añadir correcciones posteriores se edita la fuente estructurada; no se vuelve a extraer el PDF sobre una edición manual sin revisarla.

Verificación: ocho pruebas aisladas OK; navegador con 19 cursos y 100 botones, tres lecturas correctas, selección y contador conservados, carga de imágenes anteriores para cursos pendientes y página de referencia bajo demanda. Pantalla de 390 px sin desbordamiento horizontal. No se importó la aplicación ni se accedió a PostgreSQL.

## Actualización: 100 preguntas y claves de revisión

La vista reúne ahora diez [preguntas actitudinales originales con respuesta y justificación](PREGUNTAS_ACTITUDINALES_AREA_A.md), seguidas de las 90 preguntas del PDF. Las originales cubren inteligencia emocional, empatía, ética, liderazgo y vocación. Son material de práctica; no se presentan como preguntas oficiales ni como instrumento psicométrico validado.

El documento `RES_Adm_UNMSM 2026-I - area A.pdf` tiene seis páginas y proporciona respuestas en texto. Se revisaron visualmente sus páginas académicas. Contiene una entrada 21 vacía: sus respuestas 22–101 corresponden a las preguntas 21–100 del examen. Se emparejaron por el contenido y no por el número impreso sin corregir.

El [banco privado de revisión](../data/examenes/area_a_2026_i_revision.json) guarda las claves transcritas y el SHA-256 del PDF de respuestas. No está dentro de `static`, no reemplaza el banco activo y no habilita la calificación. Casos pendientes:

- **47:** las alternativas A y D contienen el mismo texto que la respuesta publicada. Clave única `null`; coincidencias A y D registradas. No se escoge una arbitrariamente.
- **71:** la respuesta publicada repite la de la pregunta anterior. El mismo texto aparece como alternativa B en el examen; se transcribe B con estado `requiere_revision`, sin afirmar su validez académica.

Las demás letras corresponden al contenido publicado, sin auditoría académica independiente de la solución. Las claves y justificaciones se excluyen del JSON y JavaScript públicos. La vista conserva su propósito de revisión visual, sin notas ni intentos oficiales. Cambiar el banco activo exige resolver los pendientes y considerar la asociación de intentos y resultados históricos a la versión del examen.

Para regenerar esta ampliación después de ejecutar el importador, usar `python scripts/completar_area_a.py 'C:\ruta\RES_Adm_UNMSM 2026-I - area A.pdf'`. El script usa las letras cotejadas de este documento específico; no es un extractor genérico de solucionarios.

## Antecedente de la primera importación

La importación del 25 de octubre de 2026 incorpora el documento entregado por el usuario, `EX_Adm_UNMSM 2026-I - area A.pdf`, a una vista navegable del proyecto.

- Acceso desde el panel principal: **Ver preguntas del PDF**.
- Ruta de la aplicación: `/static/vista_previa_area_a.html`.
- También puede servirse la carpeta `static` de forma independiente para revisar la presentación sin iniciar Flask ni acceder a PostgreSQL.
- Contenido real: 90 preguntas con numeración original 11–100. El documento no contiene preguntas 1–10 ni claves. La portada excluye Medicina Humana.
- Se conservan enunciados, fórmulas, figuras y alternativas como recortes PNG. Las preguntas que continúan en otra columna o página incluyen un segundo recorte. Las 22 páginas académicas completas están disponibles como referencia, incluidos los textos compartidos.
- Las selecciones A–E son temporales y sirven para revisar la presentación. Esta vista no inicia intentos, no aplica supervisión y no califica.

## Alcance y decisión

El banco existente necesita una clave para cada pregunta. Sustituirlo con este documento sin respuestas alteraría la calificación. Por ello esta primera incorporación utiliza datos separados en [static/importaciones/unmsm-2026-i-a](../static/importaciones/unmsm-2026-i-a/) y mantiene intacto el banco calificado. No se modificaron esquema, resultados, intentos ni reglas de supervisión. Tras la revisión visual se necesitan las claves y, si se desea un examen completo, las diez preguntas ausentes.

## Repetir la extracción

El script [importar_pdf_area_a.py](../scripts/importar_pdf_area_a.py) requiere PyMuPDF solamente en el entorno de importación. No es una dependencia del servidor web. Recibe la ruta al PDF y genera imágenes, un JSON con texto extraído y un JavaScript de datos para la vista. El JSON registra el SHA-256 del original. El script está ajustado al diseño de dos columnas de este PDF; otros diseños requieren validación antes de importar.

```powershell
python scripts/importar_pdf_area_a.py 'C:\ruta\EX_Adm_UNMSM 2026-I - area A.pdf'
python -m http.server 8765 --bind 127.0.0.1 --directory static
```

Abrir `http://127.0.0.1:8765/vista_previa_area_a.html`. El enlace al panel principal funciona al servir la vista desde la aplicación Flask.
