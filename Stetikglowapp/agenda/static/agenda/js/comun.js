// Comportamientos que se usan en todas las páginas.

if (window.lucide) lucide.createIcons();

// data-autoenviar: envía el formulario al cambiar
document.querySelectorAll("[data-autoenviar]").forEach((campo) => {
  campo.addEventListener("change", () => campo.form.submit());
});

// data-abrir-dialogo="id": abre ese <dialog>
document.querySelectorAll("[data-abrir-dialogo]").forEach((boton) => {
  boton.addEventListener("click", () => {
    document.getElementById(boton.dataset.abrirDialogo).showModal();
  });
});

// data-cerrar-dialogo: cierra el <dialog> donde está
document.querySelectorAll("[data-cerrar-dialogo]").forEach((boton) => {
  boton.addEventListener("click", () => boton.closest("dialog").close());
});

// data-confirmar="mensaje": pide confirmación antes de enviar
document.querySelectorAll("[data-confirmar]").forEach((boton) => {
  boton.addEventListener("click", (evento) => {
    if (!confirm(boton.dataset.confirmar)) evento.preventDefault();
  });
});

// data-imprimir
document.querySelectorAll("[data-imprimir]").forEach((boton) => {
  boton.addEventListener("click", () => window.print());
});
