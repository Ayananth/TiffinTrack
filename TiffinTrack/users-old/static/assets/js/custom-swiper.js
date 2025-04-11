/*=====================
    custom swiper js
   ==========================*/

var sliderOne = new Swiper(".banner1-slider", {
  slidesPerView: 5,
  spaceBetween: 12,
  loop: true,
  pagination: {
    el: ".swiper-pagination",
    clickable: true,
  },
  breakpoints: {
    0: {
      slidesPerView: 2,
    },
    375: {
      slidesPerView: 2.5,
    },
    576: {
      slidesPerView: 3,
    },
    767: {
      slidesPerView: 4,
    },
    991: {
      slidesPerView: 4.5,
    },
    1200: {
      slidesPerView: 5,
    },
  },
});

var sliderTwo = new Swiper(".categories-slider", {
  slidesPerView: 8,
  spaceBetween: 10,
  loop: true,
  navigation: {
    nextEl: ".categories-next",
    prevEl: ".categories-prev",
  },

  breakpoints: {
    0: {
      slidesPerView: 2,
      spaceBetween: 10,
    },
    375: {
      slidesPerView: 3,
    },
    576: {
      slidesPerView: 4,
      spaceBetween: 15,
    },
    767: {
      slidesPerView: 6,
    },
    991: {
      slidesPerView: 7,
    },
    1200: {
      slidesPerView: 8,
      spaceBetween: 20,
    },
  },
});

var slider9 = new Swiper(".categories-no-arrow", {
  slidesPerView: 8,
  spaceBetween: 10,
  loop: true,

  breakpoints: {
    0: {
      slidesPerView: 2,
      spaceBetween: 10,
    },
    375: {
      slidesPerView: 3,
    },
    576: {
      slidesPerView: 4,
      spaceBetween: 10,
    },
    767: {
      slidesPerView: 5,
    },
    991: {
      slidesPerView: 6,
      spaceBetween: 15,
    },
    1200: {
      slidesPerView: 7,
    },
    1400: {
      slidesPerView: 8,
      spaceBetween: 20,
    },
  },
});

var sliderFour = new Swiper(".brands-logo", {
  slidesPerView: 8,
  loop: true,
  navigation: {
    nextEl: ".brand-next",
    prevEl: ".brand-prev",
  },
  breakpoints: {
    0: {
      slidesPerView: 2,
    },
    375: {
      slidesPerView: 3,
    },
    576: {
      slidesPerView: 4,
    },
    767: {
      slidesPerView: 5,
    },
    991: {
      slidesPerView: 6,
    },
    1200: {
      slidesPerView: 8,
    },
  },
});

var sliderFive = new Swiper(".grocery-categories", {
  slidesPerView: 6,
  spaceBetween: 20,
  loop: true,
  navigation: {
    nextEl: ".swiper-button-next",
    prevEl: ".swiper-button-prev",
  },
  breakpoints: {
    0: {
      slidesPerView: 2,
    },
    576: {
      slidesPerView: 3,
    },
    768: {
      slidesPerView: 4,
    },
    992: {
      slidesPerView: 5,
    },
    1200: {
      slidesPerView: 6,
    },
    1400: {
      slidesPerView: 7,
    },
  },
});

var sliderSix = new Swiper(".grocery-product", {
  slidesPerView: 6,
  spaceBetween: 20,
  loop: true,

  navigation: {
    nextEl: ".swiper-button-next",
    prevEl: ".swiper-button-prev",
  },
  breakpoints: {
    0: {
      slidesPerView: 1,
    },
    375: {
      slidesPerView: 2,
    },
    576: {
      slidesPerView: 3,
    },
    767: {
      slidesPerView: 4,
    },
    991: {
      slidesPerView: 4,
    },
    1200: {
      slidesPerView: 5,
    },
    1400: {
      slidesPerView: 6,
    },
  },
});

var sliderSeven = new Swiper(".pharmacy-categories", {
  slidesPerView: 10,
  spaceBetween: 20,
  loop: true,
  navigation: {
    nextEl: ".swiper-button-next",
    prevEl: ".swiper-button-prev",
  },
  breakpoints: {
    0: {
      slidesPerView: 2,
    },
    576: {
      slidesPerView: 3,
    },
    768: {
      slidesPerView: 4,
    },
    992: {
      slidesPerView: 6,
    },
    1200: {
      slidesPerView: 8,
    },
    1400: {
      slidesPerView: 10,
    },
  },
});

var sliderEight = new Swiper(".pharmacy-related-product", {
  slidesPerView: 6,
  spaceBetween: 20,
  loop: true,

  navigation: {
    nextEl: ".swiper-button-next",
    prevEl: ".swiper-button-prev",
  },
  breakpoints: {
    0: {
      slidesPerView: 1,
    },
    375: {
      slidesPerView: 2,
    },
    576: {
      slidesPerView: 3,
    },
    767: {
      slidesPerView: 4,
    },
    991: {
      slidesPerView: 4,
    },
    1200: {
      slidesPerView: 6,
    },
  },
});

var sliderNine = new Swiper(".testimonial", {
  loop: true,
  autoplay: {
    delay: 0,
    disableOnInteraction: true,
  },
  slidesPerView: 2.5,
  spaceBetween: 32,
  speed: 10000,

  breakpoints: {
    0: {
      slidesPerView: 1,
    },
    375: {
      slidesPerView: 1.2,
    },
    425: {
      slidesPerView: 1.3,
    },
    576: {
      slidesPerView: 1.5,
    },
    768: {
      slidesPerView: 2,
    },
    992: {
      slidesPerView: 2.5,
    },
  },
});

var sliderTen = new Swiper(".categories-slider-2", {
  slidesPerView: 7,
  spaceBetween: 10,
  loop: true,
  navigation: {
    nextEl: ".categories-next",
    prevEl: ".categories-prev",
  },

  breakpoints: {
    0: {
      slidesPerView: 2,
    },
    502: {
      slidesPerView: 3,
      spaceBetween: 10,
    },
    690: {
      slidesPerView: 4,
    },
    1185: {
      slidesPerView: 5,
      spaceBetween: 15,
    },
    1393: {
      slidesPerView: 6,
    },
    1584: {
      slidesPerView: 7,
    },
  },
});

var sliderEleven = new Swiper(".brands-logo-2", {
  slidesPerView: 8,
  loop: true,
  speed: 2000,
  autoplay: {
    delay: 1000,
    disableOnInteraction: false,
  },
  breakpoints: {
    0: {
      slidesPerView: 2,
    },
    350: {
      slidesPerView: 3,
    },
    460: {
      slidesPerView: 4,
    },
    615: {
      slidesPerView: 5,
    },
    1092: {
      slidesPerView: 6,
    },
    1300: {
      slidesPerView: 7,
    },
    1560: {
      slidesPerView: 8,
    },
  },
});

var sliderTwelve = new Swiper(".popular-slider", {
  slidesPerView: 5,
  spaceBetween: 20,
  loop: true,
  navigation: {
    nextEl: ".popular-next",
    prevEl: ".popular-prev",
  },
  breakpoints: {
    0: {
      slidesPerView: 1.2,
      spaceBetween: 10,
    },
    375: {
      slidesPerView: 1.5,
      spaceBetween: 10,
    },
    470: {
      slidesPerView: 2,
      spaceBetween: 10,
    },
    715: {
      slidesPerView: 3,
      spaceBetween: 10,
    },
    991: {
      slidesPerView: 2.5,
      spaceBetween: 10,
    },
    1315: {
      slidesPerView: 4,
      spaceBetween: 15,
    },
    1612: {
      slidesPerView: 5,
      spaceBetween: 20,
    },
  },
});

//product swiper

var thumbnailSlider2 = new Swiper(".thumbnailSlider2", {
  direction: "horizontal",
  watchSlidesProgress: true,
  spaceBetween: 8,
  slidesPerView: 4,

  freeMode: true,
  watchSlidesProgress: true,
});
var mainSlider2 = new Swiper(".mainslider2", {
  spaceBetween: 0,
  loop: true,
  thumbs: {
    swiper: thumbnailSlider2,
  },
});
