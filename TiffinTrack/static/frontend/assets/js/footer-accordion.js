/*=====================
    footer accordion js
==========================*/
const footerButton = document.querySelectorAll(".footer-title");
const showNav = document.querySelector(".content");
for (var i = 0; i < footerButton.length; ++i) {
  footerButton[i].addEventListener('click', function () {
    this.parentNode.classList.toggle('open-footer-content');
  })
}