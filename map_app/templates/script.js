// Crear el mapa centrado en México
const map = L.map('map').setView([23.6345, -102.5528], 5);

// Añadir una capa base (OSM)
const osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

// Añadir capas adicionales
const satelite = L.tileLayer('https://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', {
    attribution: '&copy; Google Satellite',
    subdomains: ['mt0', 'mt1', 'mt2', 'mt3']
});

const terreno = L.tileLayer('https://{s}.google.com/vt/lyrs=p&x={x}&y={y}&z={z}', {
    attribution: '&copy; Google Terrain',
    subdomains: ['mt0', 'mt1', 'mt2', 'mt3']
});

// Controles para cambiar capas
const baseMaps = {
    "OSM": osm,
    "Satélite": satelite,
    "Terreno": terreno
};

L.control.layers(baseMaps).addTo(map);
