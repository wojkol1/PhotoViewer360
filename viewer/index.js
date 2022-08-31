'use strict';
// Create viewer.
var viewer = new Marzipano.Viewer(document.getElementById('pano'));

// var last = source.DateLastModified

// Create source.
var source = Marzipano.ImageUrlSource.fromString(
  "image.jpg"
);

// Create geometry.
var geometry = new Marzipano.EquirectGeometry([{ width: 8192 }]);

// Create view.
var limiter = Marzipano.RectilinearView.limit.traditional(8192, 100*Math.PI/180);
var view = new Marzipano.RectilinearView({ yaw:Math.PI/180 },limiter);

// Create scene.
var scene = viewer.createScene({
  source: source,
  geometry: geometry,
  view: view,
  pinFirstLevel: true
});

//Wyświetlanie info o zdjęciu
var fileMetadata = document.querySelector('#photo_data');
var fileToggleMetadata = document.querySelector('#file_metadata');

function toggleMetadata() {
  fileToggleMetadata.classList.toggle('enabled');
}

// Set handler for scene list toggle.
fileToggleMetadata.addEventListener('click', toggleMetadata);


function showMetadata() {
  fileMetadata.classList.add('enabled');
  fileToggleMetadata.classList.add('enabled');
}

function hideMetadata() {
  fileMetadata.classList.remove('enabled');
  fileToggleMetadata.classList.remove('enabled');
}

function toggleMetadata() {
  fileMetadata.classList.toggle('enabled');
  fileToggleMetadata.classList.toggle('enabled');
}

// Display scene.
scene.switchTo();

var viewChangeHandler = function() {
    var yaw = view.yaw();
	var act_yaw=yaw;
	var d_yaw=yaw/(Math.PI/180)
	console.log(d_yaw);
  };
 
view.addEventListener('change', viewChangeHandler);

 // Create link hotspots.
//  var imgHotspot = document.createElement('img');
//  imgHotspot.src = 'img/hotspot.png';
//  imgHotspot.classList.add('hotspot');
//  imgHotspot.addEventListener('change', viewChangeHandler);
 
//  var position = { yaw: Math.PI/4, pitch: Math.PI/8 };
 
//  marzipanoScene.hotspotContainer().createHotspot(imgHotspot, position);

// DOM elements for view controls.
var viewUpElement = document.querySelector('#viewUp');
var viewDownElement = document.querySelector('#viewDown');
var viewLeftElement = document.querySelector('#viewLeft');
var viewRightElement = document.querySelector('#viewRight');
var viewInElement = document.querySelector('#viewIn');
var viewOutElement = document.querySelector('#viewOut');

// Dynamic parameters for controls.
var velocity = 0.7;
var friction = 3;

// Associate view controls with elements.
var controls = viewer.controls();
controls.registerMethod('upElement',    new Marzipano.ElementPressControlMethod(viewUpElement,     'y', -velocity, friction), true);
controls.registerMethod('downElement',  new Marzipano.ElementPressControlMethod(viewDownElement,   'y',  velocity, friction), true);
controls.registerMethod('leftElement',  new Marzipano.ElementPressControlMethod(viewLeftElement,   'x', -velocity, friction), true);
controls.registerMethod('rightElement', new Marzipano.ElementPressControlMethod(viewRightElement,  'x',  velocity, friction), true);
controls.registerMethod('inElement',    new Marzipano.ElementPressControlMethod(viewInElement,  'zoom', -velocity, friction), true);
controls.registerMethod('outElement',   new Marzipano.ElementPressControlMethod(viewOutElement, 'zoom',  velocity, friction), true);
