/* Práctica original: comparte los estilos y la organización del área A. */
(() => {
  'use strict';
  const el = id => document.getElementById(id);
  const estados = new Map();
  let datos, estado, solicitud = 0;
  const ns = 'http://www.w3.org/2000/svg';
  function nodo(nombre, texto, clase) {
    const elemento = document.createElement(nombre);
    if (texto !== undefined) elemento.textContent = texto;
    if (clase) elemento.className = clase;
    return elemento;
  }
  function figura(q) {
    el('figuras-pregunta').replaceChildren();
    if (!q.figura) return;
    const svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('viewBox', '0 0 360 235');
    svg.setAttribute('role', 'img');
    svg.style.maxWidth = '420px';
    svg.style.width = '100%';
    const titulo = document.createElementNS(ns, 'title');
    titulo.textContent = 'Esquema de apoyo, no dibujado a escala. ' + q.enunciado;
    svg.append(titulo);
    const rectangulo = q.figura === 'rectangulo';
    const valores = [...q.enunciado.matchAll(/(\d+) cm/g)].map(m => m[1]);
    const forma = document.createElementNS(ns, 'path');
    forma.setAttribute('d', rectangulo ? 'M65 40 H300 V180 H65 Z' : 'M65 40 V180 H300 Z');
    forma.setAttribute('fill', 'rgba(130,35,58,0.06)');
    forma.setAttribute('stroke', 'currentColor');
    forma.setAttribute('stroke-width', '2');
    svg.append(forma);
    if (!rectangulo) {
      const angulo = document.createElementNS(ns, 'path');
      angulo.setAttribute('d', 'M65 165 H80 V180');
      angulo.setAttribute('fill', 'none');
      angulo.setAttribute('stroke', 'currentColor');
      svg.append(angulo);
    }
    for (const [texto, x, y] of [[`${valores[0]} cm`, rectangulo ? 182 : 29, rectangulo ? 215 : 110],
                                [`${valores[1]} cm`, rectangulo ? 329 : 182, rectangulo ? 110 : 215]]) {
      const etiqueta = document.createElementNS(ns, 'text');
      etiqueta.setAttribute('x', x); etiqueta.setAttribute('y', y);
      etiqueta.setAttribute('text-anchor', 'middle');
      etiqueta.setAttribute('fill', 'currentColor');
      etiqueta.setAttribute('font-size', '16');
      etiqueta.textContent = texto;
      svg.append(etiqueta);
    }
    el('figuras-pregunta').append(svg, nodo('p', 'Esquema de apoyo; no está a escala.', 'preview-hint'));
  }
  function actualizar() {
    const q = datos.preguntas[estado.indice];
    el('contador').textContent = `${estado.respuestas.size} de 100 respondidas`;
    el('seleccion').textContent = estado.respuestas.has(q.id) ? `Alternativa marcada: ${estado.respuestas.get(q.id)}` : 'Sin responder';
    for (const boton of el('matriz').querySelectorAll('button[data-id]')) {
      boton.classList.toggle('marked', estado.respuestas.has(Number(boton.dataset.id)));
      boton.setAttribute('aria-current', String(Number(boton.dataset.id) === q.id));
    }
  }
  function mostrar(indice) {
    estado.indice = indice;
    const q = datos.preguntas[indice];
    el('numero').textContent = `Pregunta ${q.id}`;
    el('titulo-pregunta').textContent = `Pregunta ${q.id}`;
    el('posicion').textContent = `${indice+1} de 100 disponibles`;
    el('origen-pregunta').textContent = `${q.curso} · Creación original para práctica`;
    el('enunciado-original').textContent = q.enunciado;
    const lectura = datos.lecturas.find(l => l.id === q.lectura_id);
    const contenedor = el('lectura-compartida');
    contenedor.replaceChildren(); contenedor.hidden = !lectura;
    if (lectura) {
      contenedor.append(nodo('h2', lectura.titulo), nodo('p', `Lectura compartida · Preguntas ${lectura.preguntas.join(', ')}`, 'reading-relation'));
      for (const bloque of lectura.bloques) {
        for (const parrafo of bloque.parrafos) contenedor.append(nodo('p', parrafo));
      }
    }
    figura(q);
    el('alternativas').replaceChildren();
    el('alternativas').classList.add('opciones-originales');
    for (const [letra, texto] of Object.entries(q.opciones)) {
      const etiqueta = nodo('label');
      const radio = document.createElement('input');
      radio.type = 'radio'; radio.name = 'respuesta'; radio.value = letra;
      radio.checked = estado.respuestas.get(q.id) === letra;
      radio.addEventListener('change', () => { estado.respuestas.set(q.id, letra); actualizar(); });
      etiqueta.append(radio, nodo('span', `${letra}) ${texto}`));
      el('alternativas').append(etiqueta);
    }
    el('anterior').disabled = indice === 0;
    el('siguiente').disabled = indice === 99;
    actualizar();
  }
  function crearBotones(numeros, seccion) {
    const rejilla = nodo('div', undefined, 'preview-matrix');
    for (const numero of numeros) {
      const boton = nodo('button', numero);
      boton.type = 'button'; boton.dataset.id = numero;
      boton.setAttribute('aria-label', `Ir a pregunta ${numero}`);
      boton.addEventListener('click', () => mostrar(numero-1));
      rejilla.append(boton);
    }
    seccion.append(rejilla);
  }
  async function cargar(area) {
    const actual = ++solicitud;
    el('error-carga').hidden = true;
    el('pregunta-practica').hidden = true;
    el('matriz').replaceChildren(); el('contador').textContent = '';
    el('titulo-area').textContent = `Cargando área ${area}…`;
    try {
      const respuesta = await fetch(`practica/area_${area.toLowerCase()}.json`);
      if (!respuesta.ok) throw new Error('No se pudo cargar el banco de preguntas.');
      const recibido = await respuesta.json();
      if (actual !== solicitud) return;
      datos = recibido;
      if (!estados.has(area)) estados.set(area, {indice: 0, respuestas: new Map()});
      estado = estados.get(area);
      el('titulo-area').textContent = `Área ${area} · ${datos.titulo}`;
      document.title = `Área ${area} · 100 preguntas de práctica | UNMSM`;
      for (const grupo of datos.grupos) {
        const seccion = nodo('section', undefined, 'course-group');
        seccion.setAttribute('aria-label', grupo.nombre_completo || grupo.nombre);
        seccion.append(nodo('h3', grupo.nombre));
        if (grupo.lecturas) {
          for (const id of grupo.lecturas) {
            const lectura = datos.lecturas.find(l => l.id === id);
            seccion.append(nodo('h4', lectura.titulo));
            crearBotones(lectura.preguntas, seccion);
          }
        } else crearBotones(grupo.preguntas, seccion);
        el('matriz').append(seccion);
      }
      mostrar(estado.indice);
      el('pregunta-practica').hidden = false;
      const url = new URL(location.href); url.searchParams.set('area', area);
      history.replaceState(null, '', url);
    } catch (error) {
      if (actual !== solicitud) return;
      el('error-carga').textContent = 'No se pudo cargar esta área. Comprueba la conexión y vuelve a seleccionarla.';
      el('error-carga').hidden = false;
    }
  }
  el('area-practica').addEventListener('change', event => cargar(event.target.value));
  el('anterior').addEventListener('click', () => { if (estado.indice > 0) mostrar(estado.indice-1); });
  el('siguiente').addEventListener('click', () => { if (estado.indice < 99) mostrar(estado.indice+1); });
  el('limpiar').addEventListener('click', () => { estado.respuestas.delete(datos.preguntas[estado.indice].id); mostrar(estado.indice); });
  const solicitada = new URLSearchParams(location.search).get('area')?.toUpperCase();
  const inicial = ['B','C','D','E'].includes(solicitada) ? solicitada : 'B';
  el('area-practica').value = inicial;
  cargar(inicial);
})();
