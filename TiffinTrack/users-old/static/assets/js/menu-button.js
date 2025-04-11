/*=====================
    menu button js
=======================*/
var menuButton = document.querySelectorAll(".menu-button");
var bgOverlay = document.querySelectorAll(".bg-overlay");
var productSidebar = document.querySelectorAll(".product-sidebar");
var navItem = document.querySelectorAll(".product-sidebar nav .nav .nav-link");

menuButton.forEach(function (button) {
  button.addEventListener("click", function () {
    console.log("click");
    bgOverlay.forEach(function (element) {
      element.classList.add("show");
    });
    productSidebar.forEach(function (element) {
      element.classList.add("show");
    });
  });
});

function closeOverlay() {
  bgOverlay.forEach(function (element) {
    element.classList.remove("show");
  });
  productSidebar.forEach(function (element) {
    element.classList.remove("show");
  });
}

productSidebar.forEach(function (element) {
  element.addEventListener("click", closeOverlay);
});
bgOverlay.forEach(function (element) {
  element.addEventListener("click", closeOverlay);
});
