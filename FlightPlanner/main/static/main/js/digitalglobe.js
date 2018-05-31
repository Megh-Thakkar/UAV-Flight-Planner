var ol2d = new ol.Map({
        target: 'map',
        layers: [
            new ol.layer.Tile({
                title: 'DigitalGlobe Maps API: RECENT Imagery (Italy)',
                source: new ol.source.XYZ({
                    url: 'https://api.tiles.mapbox.com/v4/digitalglobe.92ee07af/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoiZGlnaXRhbGdsb2JlIiwiYSI6ImNqNTVqZmY0aDA2cjIzMnRncDFiMzJieGIifQ.VyZKulNqqeNoEn3AlB8lkw',
                    attribution: "© DigitalGlobe, Inc"
                })
            }),

            new ol.layer.Tile({
                title: 'DigitalGlobe Maps API: Terrain Map',
                source: new ol.source.XYZ({
                    url: 'https://api.tiles.mapbox.com/v4/digitalglobe.nako1fhg/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoiZGlnaXRhbGdsb2JlIiwiYSI6ImNqNTVqZmY0aDA2cjIzMnRncDFiMzJieGIifQ.VyZKulNqqeNoEn3AlB8lkw',
                    attribution: "© OpenStreetMap Contributors, © Mapbox, Inc"
                })
            })
            ],

        view: new ol.View({
            center: ol.proj.fromLonLat([12.486, 41.89]),
            zoom: 14
        })
});

// Layer Switcher functionality courtesy:
// https://github.com/walkermatt/ol3-layerswitcher
var layerSwitcher = new ol.control.LayerSwitcher({
        tipLabel: 'Legend' // Optional label for button
});
ol2d.addControl(layerSwitcher);

// 3D system ..
var ol3d = new olcs.OLCesium({map: ol2d});
var scene = ol3d.getCesiumScene();
var terrainProvider = new Cesium.CesiumTerrainProvider({
    url : 'https://assets.agi.com/stk-terrain/world'
});
scene.terrainProvider = terrainProvider;