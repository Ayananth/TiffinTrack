/*=====================
    Sidebar toggle js
==========================*/
document
  .getElementById("sidebar-toggle")
  .addEventListener("click", function () {
      var divs = document.getElementById("shop-sidebar");
      var divs1 = document.getElementById("sidebar-overlay");
      divs.classList.add("show");
      divs1.classList.add("show");
  });
document.getElementById("sidebar-back").addEventListener("click", function () {
  var divs = document.getElementById("shop-sidebar");
  var divs1 = document.getElementById("sidebar-overlay");
    divs.classList.remove("show");
    divs1.classList.remove("show");
});
document
  .getElementById("sidebar-overlay")
  .addEventListener("click", function () {
    var divs = document.getElementById("shop-sidebar");
    var divs1 = document.getElementById("sidebar-overlay");
      divs.classList.remove("show");
      divs1.classList.remove("show");
  });