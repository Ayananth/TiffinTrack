/*=====================
    route map js
   ==========================*/

(function (A) {
  if (!Array.prototype.forEach)
    A.forEach =
      A.forEach ||
      function (action, that) {
        for (var i = 0, l = this.length; i < l; i++)
          if (i in this) action.call(that, this[i], i, this);
      };
})(Array.prototype);

var mapObject,
  markers = [],
  markersData = {
    Restaurant: [
      {
        location_latitude: 25.193357,
        location_longitude: 55.276787,
        data_title: "user",
        icon_name: "assets/images/svg/user-map.svg",
        name: "Armani Amal",
      },
      {
        location_latitude: 25.185015,
        location_longitude: 55.264164,
        data_title: "first",
        icon_name: "assets/images/svg/placed.svg",
        name: "MATTO Italian Restaurant dubai",
      },
      {
        location_latitude: 25.18912,
        location_longitude: 55.283807,
        data_title: "second",
        icon_name: "assets/images/svg/driver.svg",
        name: "The Kana Cafe Dubai",
      },
    ],
  };

var mapOptions = {
  zoom: 14,
  center: new google.maps.LatLng(25.181, 55.2709932),
  mapTypeId: google.maps.MapTypeId.ROADMAP,

  mapTypeControl: false,
  mapTypeControlOptions: {
    style: google.maps.MapTypeControlStyle.DROPDOWN_MENU,
    position: google.maps.ControlPosition.LEFT_CENTER,
  },
  panControl: false,
  panControlOptions: {
    position: google.maps.ControlPosition.TOP_RIGHT,
  },
  zoomControl: true,
  zoomControlOptions: {
    style: google.maps.ZoomControlStyle.LARGE,
    position: google.maps.ControlPosition.RIGHT_BOTTOM,
  },
  scrollwheel: false,
  scaleControl: false,
  scaleControlOptions: {
    position: google.maps.ControlPosition.LEFT_CENTER,
  },
  streetViewControl: true,
  streetViewControlOptions: {
    position: google.maps.ControlPosition.RIGHT_BOTTOM,
  },
  styles: [
    {
      featureType: "administrative.country",
      elementType: "all",
      stylers: [
        {
          visibility: "off",
        },
      ],
    },
    {
      featureType: "administrative.province",
      elementType: "all",
      stylers: [
        {
          visibility: "off",
        },
      ],
    },
    {
      featureType: "administrative.locality",
      elementType: "all",
      stylers: [
        {
          visibility: "off",
        },
      ],
    },
    {
      featureType: "administrative.neighborhood",
      elementType: "all",
      stylers: [
        {
          visibility: "off",
        },
      ],
    },
    {
      featureType: "administrative.land_parcel",
      elementType: "all",
      stylers: [
        {
          visibility: "off",
        },
      ],
    },
    {
      featureType: "landscape.man_made",
      elementType: "all",
      stylers: [
        {
          visibility: "simplified",
        },
      ],
    },
    {
      featureType: "landscape.natural.landcover",
      elementType: "all",
      stylers: [
        {
          visibility: "on",
        },
      ],
    },
    {
      featureType: "landscape.natural.terrain",
      elementType: "all",
      stylers: [
        {
          visibility: "off",
        },
      ],
    },
    {
      featureType: "poi.attraction",
      elementType: "all",
      stylers: [
        {
          visibility: "off",
        },
      ],
    },
    {
      featureType: "poi.business",
      elementType: "all",
      stylers: [
        {
          visibility: "off",
        },
      ],
    },
    {
      featureType: "poi.government",
      elementType: "all",
      stylers: [
        {
          visibility: "off",
        },
      ],
    },
    {
      featureType: "poi.medical",
      elementType: "all",
      stylers: [
        {
          visibility: "off",
        },
      ],
    },
    {
      featureType: "poi.park",
      elementType: "all",
      stylers: [
        {
          visibility: "on",
        },
      ],
    },
    {
      featureType: "poi.park",
      elementType: "labels",
      stylers: [
        {
          visibility: "off",
        },
      ],
    },
    {
      featureType: "poi.place_of_worship",
      elementType: "all",
      stylers: [
        {
          visibility: "off",
        },
      ],
    },
    {
      featureType: "poi.school",
      elementType: "all",
      stylers: [
        {
          visibility: "off",
        },
      ],
    },
    {
      featureType: "poi.sports_complex",
      elementType: "all",
      stylers: [
        {
          visibility: "off",
        },
      ],
    },
    {
      featureType: "road.highway",
      elementType: "all",
      stylers: [
        {
          visibility: "off",
        },
      ],
    },
    {
      featureType: "road.highway",
      elementType: "labels",
      stylers: [
        {
          visibility: "off",
        },
      ],
    },
    {
      featureType: "road.highway.controlled_access",
      elementType: "all",
      stylers: [
        {
          visibility: "off",
        },
      ],
    },
    {
      featureType: "road.arterial",
      elementType: "all",
      stylers: [
        {
          visibility: "simplified",
        },
      ],
    },
    {
      featureType: "road.local",
      elementType: "all",
      stylers: [
        {
          visibility: "simplified",
        },
      ],
    },
    {
      featureType: "transit.line",
      elementType: "all",
      stylers: [
        {
          visibility: "off",
        },
      ],
    },
    {
      featureType: "transit.station.airport",
      elementType: "all",
      stylers: [
        {
          visibility: "off",
        },
      ],
    },
    {
      featureType: "transit.station.bus",
      elementType: "all",
      stylers: [
        {
          visibility: "off",
        },
      ],
    },
    {
      featureType: "transit.station.rail",
      elementType: "all",
      stylers: [
        {
          visibility: "off",
        },
      ],
    },
    {
      featureType: "water",
      elementType: "all",
      stylers: [
        {
          visibility: "on",
        },
      ],
    },
    {
      featureType: "water",
      elementType: "labels",
      stylers: [
        {
          visibility: "off",
        },
      ],
    },
  ],
};
var marker;
mapObject = new google.maps.Map(document.getElementById("map"), mapOptions);

for (var key in markersData)
  markersData[key].forEach(function (item) {
    marker = new google.maps.Marker({
      position: new google.maps.LatLng(
        item.location_latitude,
        item.location_longitude
      ),
      map: mapObject,
      animation: google.maps.Animation.DROP,
      icon: item.icon_name,
      title: item.data_title,
    });

    if ("undefined" === typeof markers[key]) markers[key] = [];
    markers[key].push(marker);
  });

function hideAllMarkers() {
  for (var key in markers)
    markers[key].forEach(function (marker) {
      marker.setMap(null);
    });
}

function toggleMarkers(category) {
  hideAllMarkers();
  closeInfoBox();

  if ("undefined" === typeof markers[category]) return false;
  markers[category].forEach(function (marker) {
    marker.setMap(mapObject);
    marker.setAnimation(google.maps.Animation.BOUNCE);
  });
}

function onHtmlClick(location_type, key) {
  google.maps.event.trigger(markers[location_type][key], "click");
}
