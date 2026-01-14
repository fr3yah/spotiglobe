var map = L.map('map').setView([35, 0], 1.4);

var tiles = L.tileLayer('https://tiles.stadiamaps.com/tiles/stamen_watercolor/{z}/{x}/{y}.{ext}', {
	minZoom: 1,
	maxZoom: 4
});



function getColor(d) {
    return d > 24  ? '#E31A1C' :
           d > 16  ? '#FC4E2A' :
           d > 8   ? '#FD8D3C' :
           d > 4   ? '#FEB24C' :
           d > 0   ? '#FED976' :
                      '#FFFFFF';
}

function style(feature) {
	var iso = feature.properties.iso_a2;
	var value = mapData?.[iso]?.[0] ?? 0;
	return {
    fillColor: getColor(value), // getColor() is a separate function you define
    weight: 2,
    opacity: 1,
    color: 'black',
    dashArray: '3',
    fillOpacity: 0.7
  }
    
}


L.geoJson(geoJson, {style: style}).addTo(map);