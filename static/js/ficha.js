// Mejoras del onboarding. Todo funciona sin este archivo: son atajos y animación encima de controles normales.

// ---------- Sliders: mostrar el valor elegido
document.querySelectorAll('input[type="range"]').forEach((r) => {
  const out = document.querySelector(`output[for="${r.id}"]`);
  const pintar = () => { if (out) out.textContent = r.value; };
  r.addEventListener('input', pintar);
  pintar();
});

// ---------- Mi mes: arrastrar para marcar y atajos de repetición
const mes = document.querySelector('[data-mi-mes]');
if (mes) {
  const atajos = mes.querySelector('[data-atajos]');
  if (atajos) atajos.hidden = false;
  let pintando = null; // true = marcar, false = desmarcar

  mes.addEventListener('pointerdown', (e) => {
    const lbl = e.target.closest('.bloque-hora');
    if (!lbl) return;
    e.preventDefault();
    const cb = lbl.querySelector('input');
    pintando = !cb.checked;
    cb.checked = pintando;
  });
  mes.addEventListener('pointerover', (e) => {
    if (pintando === null) return;
    const lbl = e.target.closest('.bloque-hora');
    if (lbl) lbl.querySelector('input').checked = pintando;
  });
  window.addEventListener('pointerup', () => { pintando = null; });
  // El clic normal ya lo resolvió pointerdown: evitamos el doble cambio.
  mes.addEventListener('click', (e) => { if (e.target.closest('.bloque-hora') && e.detail) e.preventDefault(); });

  const semanas = [...mes.querySelectorAll('[data-semana]')];
  const casillas = (s) => [...s.querySelectorAll('input[name="bloques"]')];
  mes.querySelectorAll('[data-repetir]').forEach((b) => b.addEventListener('click', () => {
    const cada = Number(b.dataset.repetir);
    const base = casillas(semanas[0]).map((c) => c.checked);
    semanas.slice(1).forEach((s, i) => {
      const toca = (i + 1) % cada === 0;
      casillas(s).forEach((c, j) => { c.checked = toca && base[j]; });
    });
  }));
  mes.querySelector('[data-limpiar]')?.addEventListener('click', () => {
    mes.querySelectorAll('input[name="bloques"]').forEach((c) => { c.checked = false; });
  });
}

// ---------- Dados: tirar y repartir
const zona = document.querySelector('[data-dados]');
if (zona) {
  const VALORES = [15, 14, 13, 12, 10, 8];
  const bandeja = zona.querySelector('[data-bandeja]');
  const lista = zona.querySelector('[data-lista]');
  const instruccion = zona.querySelector('[data-instruccion]');
  const selects = [...zona.querySelectorAll('[data-casilla] select')];
  const sinMovimiento = matchMedia('(prefers-reduced-motion: reduce)').matches;
  let elegido = null;
  bandeja.hidden = false;

  const usados = () => selects.map((s) => Number(s.value)).filter(Boolean);

  function pintarDados() {
    const u = usados();
    lista.querySelectorAll('button').forEach((b) => {
      const v = Number(b.dataset.valor);
      const puesto = u.includes(v);
      b.disabled = puesto;
      b.setAttribute('aria-pressed', String(elegido === v));
      b.classList.toggle('puesto', puesto);
    });
    // En cada lista desplegable, los valores ya usados en otro atributo quedan deshabilitados.
    selects.forEach((s) => {
      [...s.options].forEach((o) => {
        if (!o.value) return;
        o.disabled = u.includes(Number(o.value)) && s.value !== o.value;
      });
    });
    const faltan = VALORES.length - u.length;
    instruccion.textContent = elegido
      ? `Elegiste el ${elegido}. Ahora toca el atributo donde va.`
      : faltan ? `Toca un dado y luego un atributo. Faltan ${faltan}.` : 'Listo: los seis dados están repartidos.';
  }

  function crearDados() {
    lista.innerHTML = '';
    VALORES.forEach((v) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'dado num';
      b.dataset.valor = v;
      b.textContent = v;
      b.setAttribute('aria-label', `Dado con ${v}`);
      b.addEventListener('click', () => { elegido = elegido === v ? null : v; pintarDados(); });
      lista.append(b);
    });
  }

  zona.querySelector('[data-tirar]').addEventListener('click', (e) => {
    e.currentTarget.textContent = 'Volver a tirar';
    selects.forEach((s) => { s.value = ''; });
    elegido = null;
    crearDados();
    const dados = [...lista.children];
    if (sinMovimiento) { pintarDados(); return; }
    dados.forEach((d) => d.classList.add('rodando'));
    let n = 0;
    const t = setInterval(() => {
      dados.forEach((d) => { d.textContent = 1 + Math.floor(Math.random() * 20); });
      if (++n > 10) {
        clearInterval(t);
        dados.forEach((d) => { d.textContent = d.dataset.valor; d.classList.remove('rodando'); });
        pintarDados();
      }
    }, 70);
  });

  // Tocar un atributo con un dado elegido lo coloca ahí (y devuelve el que había).
  zona.querySelectorAll('[data-casilla]').forEach((c) => {
    c.addEventListener('click', (e) => {
      if (elegido === null || e.target.tagName === 'SELECT' || e.target.tagName === 'OPTION') return;
      c.querySelector('select').value = String(elegido);
      elegido = null;
      pintarDados();
    });
  });
  selects.forEach((s) => s.addEventListener('change', pintarDados));

  if (usados().length) { crearDados(); pintarDados(); zona.querySelector('[data-tirar]').textContent = 'Volver a tirar'; }
}
