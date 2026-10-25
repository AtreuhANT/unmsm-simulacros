/* Contenido del examen y su revisión: DOM seguro y recursos locales. */
(() => {
  'use strict';
  const ns = 'http://www.w3.org/2000/svg';
  const crear = (tag, texto, clase) => {
    const e = document.createElement(tag);
    if (texto) e.textContent = texto;
    if (clase) e.className = clase;
    return e;
  };
  function escribir(elemento, texto) { FormatoAcademico.escribir(elemento, texto || ''); }
  function svgNodo(tag, atributos) {
    const e = document.createElementNS(ns, tag);
    for (const [k,v] of Object.entries(atributos)) e.setAttribute(k,v);
    return e;
  }
  function imagen(figura, q) {
    const e = crear('img');
    const ruta = (q.base_recursos || '') + figura.imagen;
    if (!/^[a-zA-Z0-9_./-]+$/.test(ruta) || ruta.includes('..')) return e;
    e.src = (window.STATIC_BASE || '/static/') + ruta;
    e.alt = figura.descripcion || 'Figura de apoyo';
    e.className = 'academic-image';
    return e;
  }
  function cuadricula(descripcion) {
    const svg = svgNodo('svg', {viewBox:'0 0 270 270',role:'img','aria-label':descripcion});
    for (let f=0;f<5;f++) for (let c=0;c<5;c++) {
      if (f!==0 && f!==4 && c!==0 && c!==4) continue;
      svg.append(svgNodo('rect', {x:10+c*50,y:10+f*50,width:50,height:50,fill:'white',stroke:'#007eb5','stroke-width':1.5}));
    }
    return svg;
  }
  function geometria(q) {
    const rect = q.figura === 'rectangulo';
    const valores = [...q.enunciado.matchAll(/(\d+) cm/g)].map(m=>m[1]);
    const svg = svgNodo('svg', {viewBox:'0 0 360 235',role:'img','aria-label':'Esquema de apoyo, no dibujado a escala. '+q.enunciado});
    svg.append(svgNodo('path', {d:rect?'M65 40 H300 V180 H65 Z':'M65 40 V180 H300 Z',fill:'rgba(130,35,58,.06)',stroke:'currentColor','stroke-width':2}));
    if (!rect) svg.append(svgNodo('path', {d:'M65 165 H80 V180',fill:'none',stroke:'currentColor'}));
    for (const [texto,x,y] of [[valores[0]+' cm',rect?182:29,rect?215:110],[valores[1]+' cm',rect?329:182,rect?110:215]]) {
      const t = svgNodo('text', {x,y,'text-anchor':'middle',fill:'currentColor','font-size':16});
      t.textContent = texto; svg.append(t);
    }
    return svg;
  }
  function mostrar(contenedor, q) {
    contenedor.replaceChildren(); contenedor.classList.add('academic-content');
    if (q.lectura) {
      const lectura = crear('section', undefined, 'academic-reading');
      lectura.lang = q.lectura.idioma || 'es';
      lectura.append(crear('h3', q.lectura.titulo));
      for (const bloque of q.lectura.bloques || []) {
        if (bloque.titulo) lectura.append(crear('h4', bloque.titulo));
        for (const parrafo of bloque.parrafos || []) lectura.append(crear('p', parrafo));
      }
      for (const figura of q.lectura.figuras || []) lectura.append(imagen(figura,q));
      if (q.lectura.fuente) lectura.append(crear('p', q.lectura.fuente, 'academic-source'));
      contenedor.append(lectura);
    }
    const enunciado = crear('p', undefined, 'academic-prompt');
    escribir(enunciado,q.enunciado_rico || q.enunciado);
    if (q.subrayados) {
      // El banco usa palabras literales; no interpretar patrones regulares externos.
      enunciado.replaceChildren();
      for (const fragmento of q.enunciado.split(/([\p{L}\p{N}_]+)/u)) {
        enunciado.append(q.subrayados.includes(fragmento.toLowerCase()) ? crear('u',fragmento) : document.createTextNode(fragmento));
      }
    }
    contenedor.append(enunciado);
    const figuras = crear('div', undefined, 'academic-figures');
    for (const figura of q.figuras || []) figuras.append(figura.tipo==='cuadricula-borde' ? cuadricula(figura.descripcion) : imagen(figura,q));
    if (q.figura) figuras.append(geometria(q),crear('p','Esquema de apoyo; no está a escala.','academic-source'));
    if (figuras.childNodes.length) contenedor.append(figuras);
    if (q.tabla) {
      const wrapper = crear('div', undefined, 'academic-table');
      const tabla = crear('table'); const thead=crear('thead'); const tr=crear('tr');
      for (const titulo of q.tabla.columnas) { const th=crear('th',titulo); th.scope='col';tr.append(th); }
      thead.append(tr);tabla.append(thead);const tbody=crear('tbody');
      for (const valores of q.tabla.filas) { const fila=crear('tr');for(const valor of valores) fila.append(crear('td',valor));tbody.append(fila); }
      tabla.append(tbody);wrapper.append(tabla);contenedor.append(wrapper);
    }
    if (q.texto_despues_figura) {
      const continuacion=crear('p',undefined,'academic-prompt');
      escribir(continuacion,q.texto_despues_figura_rico||q.texto_despues_figura);contenedor.append(continuacion);
    }
  }
  window.ContenidoAcademico = {mostrar, escribir};
})();
