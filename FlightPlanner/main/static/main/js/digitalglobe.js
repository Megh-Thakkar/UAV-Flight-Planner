var projection = ol.proj.get('EPSG:3857');


var ol2d = new ol.Map({
        target: 'map',
        layers: [
            new ol.layer.Tile({
                source: new ol.source.BingMaps({
                  imagerySet: 'Aerial',
                  key: 'AlNk4U61H2Tk9kCiRmzUws1dazVxUh6BUeV5YRJAq5_KEw-dsiKj7AbgYtFnS7mR'
                })
              }),
            new ol.layer.Vector({
                source: new ol.source.Vector({
                url: "http://127.0.0.1:8000/media/files/kmlfile7.kml",
                format: new ol.format.KML()
                })
            }),
            ],

        view: new ol.View({
            center: [876970.8463461736, 5859807.853963373],
          projection: projection,
          zoom: 10
        })
});

//var displayFeatureInfo = function(pixel) {
//        var features = [];
//        ol2d.forEachFeatureAtPixel(pixel, function(feature) {
//          features.push(feature);
//        });
//        if (features.length > 0) {
//          var info = [];
//          var i, ii;
//          for (i = 0, ii = features.length; i < ii; ++i) {
//            info.push(features[i].get('name'));
//          }
//          document.getElementById('info').innerHTML = info.join(', ') || '(unknown)';
//          ol2d.getTarget().style.cursor = 'pointer';
//        } else {
//          document.getElementById('info').innerHTML = '&nbsp;';
//          ol2d.getTarget().style.cursor = '';
//        }
//      };
//
//      ol2d.on('pointermove', function(evt) {
//        if (evt.dragging) {
//          return;
//        }
//        var pixel = ol2d.getEventPixel(evt.originalEvent);
//        displayFeatureInfo(pixel);
//      });
//
//      ol2d.on('click', function(evt) {
//        displayFeatureInfo(evt.pixel);
//      });

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