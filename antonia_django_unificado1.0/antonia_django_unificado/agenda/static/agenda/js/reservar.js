// Formulario de reserva en 3 pasos.
// Las validaciones se repiten en views.py, aquí son solo para mostrar el error al tiro.

const $ = (selector) => document.querySelector(selector);

const form = $("#form-reserva");
let pasoActual = Number(form.dataset.paso);
const URL_TRABAJADORAS = form.dataset.urlTrabajadoras;
const URL_DISPONIBILIDAD = form.dataset.urlDisponibilidad;

const campoRut = $("#rut");
const selectLocal = $("#sucursal");
const selectServicio = $("#servicio");
const selectTrabajadora = $("#trabajadora");
const campoFecha = $("#fecha");
const campoHora = $("#hora"); // campo oculto, se llena al elegir un horario


// ---------- RUT ----------

function limpiarRut(valor) {
  return valor.replace(/[^0-9kK]/g, "").toUpperCase().slice(0, 9);
}

// 123456785 -> 12.345.678-5
function formatearRut(valor) {
  const limpio = limpiarRut(valor);
  if (limpio.length <= 1) return limpio;
  const cuerpo = limpio.slice(0, -1);
  const dv = limpio.slice(-1);
  return cuerpo.replace(/\B(?=(\d{3})+(?!\d))/g, ".") + "-" + dv;
}

// Módulo 11
function rutValido(valor) {
  const limpio = limpiarRut(valor);
  if (limpio.length < 8) return false;
  let suma = 0;
  let multiplicador = 2;
  for (let i = limpio.length - 2; i >= 0; i--) {
    suma += parseInt(limpio[i]) * multiplicador;
    multiplicador = multiplicador === 7 ? 2 : multiplicador + 1;
  }
  const resultado = 11 - (suma % 11);
  const dvEsperado = resultado === 11 ? "0" : resultado === 10 ? "K" : String(resultado);
  return limpio.slice(-1) === dvEsperado;
}

campoRut.addEventListener("input", () => {
  campoRut.value = formatearRut(campoRut.value);
  const esInvalido = campoRut.value && !rutValido(campoRut.value);
  mostrarError("rut", esInvalido ? "RUT inválido" : "");
});


// ---------- Validaciones ----------

function mostrarError(campo, mensaje) {
  const elemento = $(`[data-error="${campo}"]`);
  if (elemento) elemento.textContent = mensaje;
}

function validarPaso1() {
  const reglas = {
    rut: (v) => !v ? "El RUT es obligatorio" : !rutValido(v) ? "RUT inválido" : "",
    nombre: (v) => v ? "" : "El nombre es obligatorio",
    apellido: (v) => v ? "" : "El apellido es obligatorio",
    telefono: (v) => !v ? "El teléfono es obligatorio"
      : !/^\+?[0-9]{9,12}$/.test(v.replace(/\s/g, "")) ? "Teléfono inválido" : "",
    email: (v) => !v ? "El correo es obligatorio"
      : !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) ? "Correo inválido" : "",
  };

  let todoBien = true;
  for (const [campo, regla] of Object.entries(reglas)) {
    const mensaje = regla($("#" + campo).value.trim());
    mostrarError(campo, mensaje);
    if (mensaje) todoBien = false;
  }
  return todoBien;
}

function validarPaso2() {
  const mensajes = {
    servicio: "Selecciona un servicio",
    trabajadora: "Selecciona una trabajadora",
    hora: "Selecciona un horario",
  };

  let todoBien = true;
  for (const [campo, mensaje] of Object.entries(mensajes)) {
    const estaVacio = !$("#" + campo).value;
    mostrarError(campo, estaVacio ? mensaje : "");
    if (estaVacio) todoBien = false;
  }
  return todoBien;
}


// ---------- Pasos ----------

function mostrarPaso(numero) {
  pasoActual = numero;

  document.querySelectorAll("[data-seccion]").forEach((seccion) => {
    seccion.classList.toggle("oculto", Number(seccion.dataset.seccion) !== numero);
  });

  // solo dentro de #indicador, el form también tiene data-paso
  document.querySelectorAll("#indicador [data-paso]").forEach((circulo) => {
    circulo.classList.toggle("activo", Number(circulo.dataset.paso) <= numero);
  });

  document.querySelectorAll("[data-linea]").forEach((linea) => {
    linea.classList.toggle("activa", Number(linea.dataset.linea) < numero);
  });

  if (numero === 3) llenarResumenFinal();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// para avanzar hay que validar, para volver no
document.querySelectorAll("[data-ir]").forEach((boton) => {
  boton.addEventListener("click", () => {
    const destino = Number(boton.dataset.ir);
    const avanza = destino > pasoActual;
    if (avanza && pasoActual === 1 && !validarPaso1()) return;
    if (avanza && pasoActual === 2 && !validarPaso2()) return;
    mostrarPaso(destino);
  });
});


// ---------- Trabajadoras y horarios ----------

function textoElegido(select) {
  return select.options[select.selectedIndex]?.text || "";
}

function servicioElegido() {
  return selectServicio.options[selectServicio.selectedIndex];
}

function llenarResumenPaso2() {
  const opcion = servicioElegido();
  const caja = $("#resumen-paso2");
  if (!opcion || !opcion.value) {
    caja.classList.add("oculto");
    return;
  }
  caja.classList.remove("oculto");
  $('[data-r="servicio"]').textContent = opcion.dataset.nombre;
  $('[data-r="duracion"]').textContent = opcion.dataset.duracion + " min";
  $('[data-r="precio"]').textContent = opcion.dataset.precio;
}

// preseleccion: trabajadora que venía elegida si la página volvió con error
async function cargarTrabajadoras(preseleccion) {
  if (!selectServicio.value) {
    selectTrabajadora.innerHTML = '<option value="">Selecciona un servicio primero</option>';
    return;
  }

  const respuesta = await fetch(`${URL_TRABAJADORAS}?sucursal=${selectLocal.value}&servicio=${selectServicio.value}`);
  const { trabajadoras } = await respuesta.json();

  selectTrabajadora.innerHTML =
    '<option value="">Selecciona una trabajadora</option>' +
    trabajadoras.map((t) => `<option value="${t.id}">${t.nombre} · ${t.especialidad}</option>`).join("");

  const sigueDisponible = trabajadoras.some((t) => String(t.id) === String(preseleccion));
  if (preseleccion && sigueDisponible) selectTrabajadora.value = preseleccion;
}

async function cargarHorarios() {
  const contenedor = $("#slots");
  const mensaje = $("#slots-msg");
  contenedor.innerHTML = "";

  if (!(selectServicio.value && selectTrabajadora.value && campoFecha.value)) {
    mensaje.textContent = "Elige servicio, trabajadora y fecha para ver los horarios libres.";
    return;
  }

  const respuesta = await fetch(
    `${URL_DISPONIBILIDAD}?trabajadora=${selectTrabajadora.value}&servicio=${selectServicio.value}&fecha=${campoFecha.value}`
  );
  const { horarios } = await respuesta.json();

  if (!horarios.includes(campoHora.value)) campoHora.value = "";

  mensaje.textContent = horarios.length
    ? "Disponibilidad calculada en tiempo real."
    : "No hay horarios libres para ese día. Prueba con otra fecha o trabajadora.";

  horarios.forEach((hora) => {
    const boton = document.createElement("button");
    boton.type = "button";
    boton.textContent = hora;
    boton.dataset.hora = hora;
    contenedor.appendChild(boton);

    boton.addEventListener("click", () => {
      campoHora.value = hora;
      mostrarError("hora", "");
      pintarBotonesHorario();
    });
  });
  pintarBotonesHorario();
}

function pintarBotonesHorario() {
  document.querySelectorAll("#slots button").forEach((boton) => {
    boton.className = "horario";
    boton.classList.toggle("elegido", boton.dataset.hora === campoHora.value);
  });
}

// si cambia algo, la hora elegida ya no sirve
selectServicio.addEventListener("change", async () => {
  campoHora.value = "";
  llenarResumenPaso2();
  await cargarTrabajadoras();
  cargarHorarios();
});

selectLocal.addEventListener("change", async () => {
  campoHora.value = "";
  await cargarTrabajadoras();
  cargarHorarios();
});

selectTrabajadora.addEventListener("change", () => {
  campoHora.value = "";
  cargarHorarios();
});

campoFecha.addEventListener("change", () => {
  campoHora.value = "";
  cargarHorarios();
});


// ---------- Resumen (paso 3) ----------

function llenarResumenFinal() {
  const opcion = servicioElegido();

  const fechaTexto = campoFecha.value
    ? new Date(campoFecha.value + "T00:00").toLocaleDateString("es-CL", { weekday: "long", day: "numeric", month: "long" })
    : "";

  const resumen = {
    cliente: `${$("#nombre").value} ${$("#apellido").value}`,
    rut: campoRut.value,
    sucursal: textoElegido(selectLocal),
    servicio: opcion?.dataset.nombre || "",
    fecha: fechaTexto,
    hora: campoHora.value,
    trabajadora: textoElegido(selectTrabajadora).split(" · ")[0],
    precio: opcion?.dataset.precio || "",
  };

  for (const [clave, valor] of Object.entries(resumen)) {
    $(`[data-c="${clave}"]`).textContent = valor;
  }
}


// al cargar (o si la página volvió con errores) se deja todo como estaba
async function iniciar() {
  llenarResumenPaso2();
  await cargarTrabajadoras(selectTrabajadora.dataset.valor);
  await cargarHorarios();
  mostrarPaso(pasoActual);
}

iniciar();
