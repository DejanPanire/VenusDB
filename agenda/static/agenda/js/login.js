// Mostrar u ocultar la contraseña.

const botonOjo = document.getElementById("toggle-pass");
const campoClave = document.getElementById("password");

botonOjo.addEventListener("click", () => {
  campoClave.type = campoClave.type === "password" ? "text" : "password";
});
