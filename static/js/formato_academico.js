/* Notación matemática local con MathML nativo; no carga scripts externos. */
(() => {
  'use strict';
  const ns = 'http://www.w3.org/1998/Math/MathML';
  function nodo(nombre, ...hijos) {
    const elemento = document.createElementNS(ns, nombre);
    elemento.append(...hijos.map(h => typeof h === 'string' ? document.createTextNode(h) : h));
    return elemento;
  }
  function formula(fuente) {
    let indice = 0;
    const simbolos = {pi:'π',omega:'ω',theta:'θ',alpha:'α',beta:'β',epsilon:'ε',times:'×',cdot:'·',le:'≤',ge:'≥',in:'∈',to:'→',leftrightarrow:'↔',infty:'∞',lVert:'‖',rVert:'‖',mu:'μ',ell:'ℓ',angle:'∠'};
    function grupo() {
      while (fuente[indice] === ' ') indice++;
      if (fuente[indice] === '{') { indice++; const valor = secuencia('}'); indice++; return valor; }
      return atomo();
    }
    function atomo() {
      const caracter = fuente[indice++];
      if (caracter === '{') { const contenido = secuencia('}'); indice++; return contenido; }
      if (caracter === '\\') {
        const comando = (fuente.slice(indice).match(/^[a-zA-Z]+/) || [''])[0]; indice += comando.length;
        if (comando === 'frac') return nodo('mfrac', grupo(), grupo());
        if (comando === 'sqrt') return nodo('msqrt', grupo());
        if (['bar','overline','vec','hat'].includes(comando)) {
          const base = grupo();
          const numeral = base.querySelector('mtext');
          if (comando === 'overline' && numeral) {
            numeral.style.textDecoration = 'overline';
            return base;
          }
          const acento = nodo('mo', comando === 'vec' ? '→' : comando === 'hat' ? '^' : '‾');
          acento.setAttribute('stretchy', 'true');
          const resultado = nodo('mover', base, acento); resultado.setAttribute('accent','true'); return resultado;
        }
        if (comando === 'text') {
          if (fuente[indice] !== '{') throw new Error('Texto matemático sin llaves');
          const inicio = ++indice;
          while (indice < fuente.length && fuente[indice] !== '}') indice++;
          const contenido = fuente.slice(inicio, indice++);
          return nodo('mtext', contenido);
        }
        if (comando === 'mathrm') {
          const contenido = grupo();
          const estilo = nodo('mstyle', contenido); estilo.setAttribute('mathvariant','normal'); return estilo;
        }
        if (['sin','sen','cos','sec','tan'].includes(comando)) {
          const funcion = nodo('mi', comando); funcion.setAttribute('mathvariant','normal'); return funcion;
        }
        if (simbolos[comando]) return nodo(['pi','omega','theta','alpha','beta','epsilon','mu'].includes(comando) ? 'mi' : 'mo', simbolos[comando]);
        throw new Error(`Comando matemático no soportado: ${comando}`);
      }
      if (/[0-9]/.test(caracter)) {
        let numero = caracter;
        while (/[0-9]/.test(fuente[indice] || 'x')) numero += fuente[indice++];
        return nodo('mn', numero);
      }
      if (/[a-zA-Zα-ωΑ-Ω]/.test(caracter)) return nodo('mi', caracter);
      return nodo('mo', caracter === '-' ? '−' : caracter);
    }
    function secuencia(final) {
      const hijos = [];
      while (indice < fuente.length && fuente[indice] !== final) {
        if (/\s/.test(fuente[indice])) { indice++; continue; }
        let base = atomo(); let inferior; let superior;
        while (fuente[indice] === '_' || fuente[indice] === '^') {
          const tipo = fuente[indice++]; const valor = grupo();
          if (tipo === '_') inferior = valor; else superior = valor;
        }
        if (inferior && superior) base = nodo('msubsup', base, inferior, superior);
        else if (inferior) base = nodo('msub', base, inferior);
        else if (superior) base = nodo('msup', base, superior);
        hijos.push(base);
      }
      return nodo('mrow', ...hijos);
    }
    const math = nodo('math', secuencia());
    math.setAttribute('aria-label', fuente); math.classList.add('academic-math');
    return math;
  }
  function escribir(elemento, texto) {
    elemento.replaceChildren();
    for (const fragmento of (texto || '').split(/((?<!\\)\$(?:\\.|[^$\\])+(?<!\\)\$)/g)) {
      if (fragmento.startsWith('$') && fragmento.endsWith('$')) {
        const contenedor = document.createElement('span'); contenedor.className = 'academic-math-scroll';
        contenedor.append(formula(fragmento.slice(1,-1))); elemento.append(contenedor);
      }
      else elemento.append(document.createTextNode(fragmento.replace(/\\\$/g, '$')));
    }
  }
  window.FormatoAcademico = {escribir};
})();
