/* Vista de revisión del documento: sin reloj, calificación ni llamadas al examen. */
(() => {
  'use strict';
  const datos = window.EXAMEN_IMPORTADO;
  const preguntas = datos.preguntas;
  const respuestas = new Map();
  const base = 'importaciones/unmsm-2026-i-a/';
  const el = id => document.getElementById(id);
  let indice = 0;
  for (const pagina of datos.paginas) {
    const opcion = document.createElement('option');
    opcion.value = pagina.numero;
    opcion.textContent = pagina.numero;
    el('pagina').append(opcion);
  }
  function mostrarPagina(numero) {
    const pagina = datos.paginas.find(p => p.numero === numero);
    if (!pagina) return;
    el('pagina').value = numero;
    el('pagina-imagen').src = base + pagina.imagen;
    el('pagina-imagen').alt = `Página ${numero} del PDF original, con textos y gráficos`;
    el('pagina-anterior').disabled = numero === datos.paginas[0].numero;
    el('pagina-siguiente').disabled = numero === datos.paginas.at(-1).numero;
  }
  function actualizarEstado() {
    const pregunta = preguntas[indice];
    el('contador').textContent = `${respuestas.size} de ${preguntas.length} respondidas`;
    el('seleccion').textContent = respuestas.has(pregunta.id) ? `Alternativa marcada: ${respuestas.get(pregunta.id)}` : 'Sin responder';
    for (const boton of el('matriz').querySelectorAll('button[data-id]')) {
      boton.classList.toggle('marked', respuestas.has(Number(boton.dataset.id)));
      boton.setAttribute('aria-current', String(Number(boton.dataset.id) === pregunta.id));
    }
  }
  function mostrarLectura(pregunta) {
    const contenedor = el('lectura-compartida');
    const lectura = (datos.lecturas || []).find(l => l.id === pregunta.lectura_id);
    contenedor.hidden = !lectura;
    if (!lectura) { contenedor.replaceChildren(); delete contenedor.dataset.lectura; return; }
    // Las preguntas del mismo texto comparten un solo contenido y sus figuras.
    if (contenedor.dataset.lectura === lectura.id) return;
    contenedor.dataset.lectura = lectura.id;
    contenedor.replaceChildren();
    const titulo = document.createElement('h2');
    titulo.textContent = lectura.titulo;
    const relacion = document.createElement('p');
    relacion.className = 'reading-relation';
    relacion.textContent = `Lectura compartida · Preguntas ${lectura.preguntas.join(', ')}`;
    contenedor.append(titulo, relacion);
    for (const bloque of lectura.bloques) {
      const seccion = document.createElement('div');
      seccion.lang = lectura.idioma || 'es';
      if (bloque.titulo) {
        const subtitulo = document.createElement('h3'); subtitulo.textContent = bloque.titulo; seccion.append(subtitulo);
      }
      for (const texto of bloque.parrafos) {
        const parrafo = document.createElement('p'); parrafo.textContent = texto; seccion.append(parrafo);
      }
      contenedor.append(seccion);
    }
    for (const figura of lectura.figuras) {
      const imagen = document.createElement('img');
      imagen.src = base + figura.imagen; imagen.alt = figura.descripcion;
      imagen.className = 'reading-figure'; imagen.loading = 'lazy';
      contenedor.append(imagen);
    }
    if (lectura.pasos) {
      const tituloPasos = document.createElement('h3'); tituloPasos.textContent = 'Cómo detectar noticias falsas';
      const pasos = document.createElement('ol'); pasos.className = 'reading-steps';
      for (const [nombre, explicacion] of lectura.pasos) {
        const paso = document.createElement('li');
        const titulo = document.createElement('strong'); titulo.textContent = nombre;
        const descripcion = document.createElement('p'); descripcion.textContent = explicacion;
        paso.append(titulo, descripcion); pasos.append(paso);
      }
      contenedor.append(tituloPasos, pasos);
    }
    const fuente = document.createElement('p'); fuente.className = 'reading-source';
    fuente.textContent = lectura.fuente;
    contenedor.append(fuente);
  }
  function mostrarFiguras(pregunta) {
    const contenedor = el('figuras-pregunta');
    contenedor.replaceChildren();
    for (const figura of pregunta.figuras || []) {
      if (figura.tipo === 'cuadricula-borde') {
        // Gráfico vectorial dibujado en la página, sin imagen ni descarga.
        const ns = 'http://www.w3.org/2000/svg';
        const svg = document.createElementNS(ns, 'svg');
        svg.setAttribute('viewBox', '0 0 270 270');
        svg.setAttribute('role', 'img');
        svg.setAttribute('aria-label', figura.descripcion);
        for (let fila = 0; fila < 5; fila++) {
          for (let columna = 0; columna < 5; columna++) {
            if (fila !== 0 && fila !== 4 && columna !== 0 && columna !== 4) continue;
            const celda = document.createElementNS(ns, 'rect');
            celda.setAttribute('x', 10 + columna * 50);
            celda.setAttribute('y', 10 + fila * 50);
            celda.setAttribute('width', 50); celda.setAttribute('height', 50);
            celda.setAttribute('fill', 'white'); celda.setAttribute('stroke', '#007eb5');
            celda.setAttribute('stroke-width', '1.5'); svg.append(celda);
          }
        }
        contenedor.append(svg);
      } else {
        const imagen = document.createElement('img');
        imagen.src = base + figura.imagen; imagen.alt = figura.descripcion;
        imagen.className = 'question-figure';
        contenedor.append(imagen);
      }
    }
    const tablaContenedor = el('tabla-pregunta');
    tablaContenedor.replaceChildren(); tablaContenedor.hidden = !pregunta.tabla;
    if (pregunta.tabla) {
      const tabla = document.createElement('table');
      const encabezado = document.createElement('thead');
      const fila = document.createElement('tr');
      for (const nombre of pregunta.tabla.columnas) {
        const th = document.createElement('th'); th.scope = 'col'; th.textContent = nombre; fila.append(th);
      }
      encabezado.append(fila); tabla.append(encabezado);
      const cuerpo = document.createElement('tbody');
      for (const valores of pregunta.tabla.filas) {
        const tr = document.createElement('tr');
        for (const valor of valores) { const td = document.createElement('td'); td.textContent = valor; tr.append(td); }
        cuerpo.append(tr);
      }
      tabla.append(cuerpo); tablaContenedor.append(tabla);
    }
    el('texto-despues-figura').hidden = !pregunta.texto_despues_figura;
    FormatoAcademico.escribir(el('texto-despues-figura'), pregunta.texto_despues_figura_rico || pregunta.texto_despues_figura || '');
  }
  function mostrar(posicion) {
    indice = posicion;
    const pregunta = preguntas[indice];
    el('numero').textContent = `Pregunta ${pregunta.id}`;
    el('titulo-pregunta').textContent = `Pregunta ${pregunta.id}`;
    el('posicion').textContent = `${indice + 1} de ${preguntas.length} disponibles`;
    const original = pregunta.id <= 10;
    const esTexto = original || pregunta.formato === 'texto';
    el('ampliar').hidden = esTexto;
    el('enunciado-original').hidden = !esTexto;
    el('referencia').hidden = original;
    el('origen-pregunta').textContent = original
      ? `Creación original para práctica · ${pregunta.competencia}`
      : `${pregunta.curso} · ${esTexto ? 'Texto transcrito del PDF' : 'Recorte original · Pendiente de transcripción'}`;
    mostrarLectura(pregunta);
    mostrarFiguras(pregunta);
    FormatoAcademico.escribir(el('enunciado-original'), pregunta.enunciado_rico || pregunta.enunciado || '');
    if (pregunta.subrayados) {
      const coincidencias = new RegExp(`\\b(${pregunta.subrayados.join('|')})\\b`, 'gi');
      el('enunciado-original').replaceChildren();
      for (const fragmento of pregunta.enunciado.split(coincidencias)) {
        if (pregunta.subrayados.includes(fragmento.toLowerCase())) {
          const subrayado = document.createElement('u'); subrayado.textContent = fragmento;
          el('enunciado-original').append(subrayado);
        } else el('enunciado-original').append(document.createTextNode(fragmento));
      }
    }
    if (!esTexto) {
      el('pregunta-imagen').src = base + pregunta.imagen;
      el('pregunta-imagen').alt = `Pregunta ${pregunta.id}: ${pregunta.texto}`;
    } else {
      el('pregunta-imagen').removeAttribute('src');
    }
    el('continuaciones').replaceChildren();
    for (const nombre of esTexto ? [] : (pregunta.imagenes || []).slice(1)) {
      const imagen = document.createElement('img');
      imagen.src = base + nombre; imagen.className = 'preview-crop';
      imagen.alt = `Continuación y alternativas de la pregunta ${pregunta.id}`;
      el('continuaciones').append(imagen);
    }
    el('alternativas').replaceChildren();
    for (const letra of 'ABCDE') {
      const etiqueta = document.createElement('label');
      const radio = document.createElement('input');
      radio.type = 'radio'; radio.name = 'respuesta'; radio.value = letra;
      radio.checked = respuestas.get(pregunta.id) === letra;
      radio.addEventListener('change', () => { respuestas.set(pregunta.id, letra); actualizarEstado(); });
      const textoOpcion = document.createElement('span');
      FormatoAcademico.escribir(textoOpcion, esTexto ? `${letra}) ${(pregunta.opciones_rico || pregunta.opciones)[letra]}` : letra);
      etiqueta.append(radio, textoOpcion);
      el('alternativas').append(etiqueta);
    }
    el('anterior').disabled = indice === 0;
    el('siguiente').disabled = indice === preguntas.length - 1;
    // La página original solo se descarga si el usuario abre la referencia.
    el('referencia').open = false;
    if (!original) el('pagina').value = pregunta.pagina;
    el('pagina-imagen').removeAttribute('src');
    el('alternativas').classList.toggle('opciones-originales', esTexto);
    actualizarEstado();
  }
  function crearBoton(numero, contenedor) {
    const posicion = preguntas.findIndex(p => p.id === numero);
    const boton = document.createElement('button');
    boton.type = 'button'; boton.textContent = numero; boton.dataset.id = numero;
    boton.setAttribute('aria-label', `Ir a pregunta ${numero}`);
    boton.addEventListener('click', () => mostrar(posicion));
    contenedor.append(boton);
  }
  for (const grupo of datos.grupos) {
    const seccion = document.createElement('section'); seccion.className = 'course-group';
    const titulo = document.createElement('h3'); titulo.textContent = grupo.nombre;
    if (grupo.nombre_completo) titulo.title = grupo.nombre_completo;
    seccion.setAttribute('aria-label', grupo.nombre_completo || grupo.nombre);
    seccion.append(titulo);
    if (grupo.lecturas) {
      for (const id of grupo.lecturas) {
        const lectura = datos.lecturas.find(l => l.id === id);
        const subtitulo = document.createElement('h4'); subtitulo.textContent = lectura.titulo;
        const rejilla = document.createElement('div'); rejilla.className = 'preview-matrix';
        seccion.append(subtitulo, rejilla);
        lectura.preguntas.forEach(numero => crearBoton(numero, rejilla));
      }
    } else {
      const rejilla = document.createElement('div'); rejilla.className = 'preview-matrix';
      grupo.preguntas.forEach(numero => crearBoton(numero, rejilla)); seccion.append(rejilla);
    }
    el('matriz').append(seccion);
  }
  el('anterior').addEventListener('click', () => { if (indice > 0) mostrar(indice - 1); });
  el('siguiente').addEventListener('click', () => { if (indice < preguntas.length - 1) mostrar(indice + 1); });
  el('limpiar').addEventListener('click', () => { respuestas.delete(preguntas[indice].id); mostrar(indice); });
  el('pagina').addEventListener('change', () => mostrarPagina(Number(el('pagina').value)));
  el('referencia').addEventListener('toggle', () => {
    if (el('referencia').open) mostrarPagina(Number(el('pagina').value));
  });
  el('pagina-anterior').addEventListener('click', () => mostrarPagina(Number(el('pagina').value) - 1));
  el('pagina-siguiente').addEventListener('click', () => mostrarPagina(Number(el('pagina').value) + 1));
  mostrar(0);
})();
