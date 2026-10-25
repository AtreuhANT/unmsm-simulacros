# Bancos originales de práctica B, C, D y E

Cada área contiene 100 preguntas: 10 actitudinales originales, 10 de comprensión de tres textos originales sin imágenes y 80 de los demás cursos. Se conserva la organización en 19 cursos de la referencia del área A. Las cuotas por curso son una decisión editorial para estos ejercicios, no una distribución oficial de la UNMSM. Las situaciones actitudinales son ejercicios de reflexión, sin validación psicométrica.

Las doce lecturas son distintas. Los problemas numéricos cambian datos según el área. Las materias generales comparten parte de su contenido entre bancos; no se presentan como 400 enunciados independientes. Todas las preguntas tienen cinco alternativas, una clave y una explicación. Geometría incorpora esquemas SVG con las dimensiones del enunciado; no hay imágenes ni figuras en Habilidad Verbal.

## Abrir y revisar

El dashboard ofrece cuatro enlaces a [la vista de práctica](../static/vista_previa_areas.html). También se puede abrir `/static/vista_previa_areas.html?area=B` desde Flask. Con el servidor estático existente, la dirección es `http://127.0.0.1:8765/vista_previa_areas.html?area=B`. El selector permite cambiar entre B, C, D y E sin perder las selecciones durante la sesión de la página.

Las claves y explicaciones se conservan exclusivamente en los bancos privados:

- [Área B](../data/examenes/area_b_practica.json).
- [Área C](../data/examenes/area_c_practica.json).
- [Área D](../data/examenes/area_d_practica.json).
- [Área E](../data/examenes/area_e_practica.json).

Los archivos de [datos públicos](../static/practica/) contienen las preguntas, lecturas, grupos y etiquetas de figuras sin claves ni explicaciones. El material fuente de Habilidad Verbal está en [lecturas originales](../data/examenes/lecturas_originales_bcde.json); las demás preguntas y el procedimiento de generación están en [el generador](../scripts/generar_areas_bcde.py).

## Regenerar y comprobar

```powershell
.\.venv\Scripts\python.exe scripts/generar_areas_bcde.py
.\.venv\Scripts\python.exe -m unittest tests.test_areas_bcde tests.test_importacion_area_a -v
```

Las comprobaciones no importan Flask ni acceden a PostgreSQL. Verifican cobertura 1–100, opciones únicas, claves privadas, tres lecturas sin figuras, cobertura por los 19 cursos y cálculos numéricos con procedimientos independientes.

## Alcance de esta entrega

Los bancos están integrados al examen supervisado de las cinco áreas, con 100 preguntas y 180 minutos para nuevos intentos. La vista estática sigue disponible para revisar sin iniciar el reloj. La distribución y las preguntas originales siguen siendo material de práctica, sin atribución oficial.

Cada intento nuevo se vincula con una copia inmutable en la tabla existente `examenes_versiones`; se usa en recargas, entrega, revisión académica y reposición por el administrador. Los intentos antiguos sin versión utilizan los bancos de diez preguntas archivados en `data/examenes/anteriores/`. Conservan su reloj original. No se cambia el esquema ni se recalifican resultados históricos.

Para publicar cambios futuros, regenerar primero y ejecutar `scripts/activar_bancos_100.py`. El script valida las cinco áreas y conserva los bancos históricos. Las versiones de intentos ya iniciados no se sustituyen.
