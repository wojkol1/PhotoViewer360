'use strict';
// Create viewer.
var viewer = new Marzipano.Viewer(document.getElementById('pano'));

// Create source.
var source = Marzipano.ImageUrlSource.fromString(
  "image.jpg"
);

// Create geometry.
var geometry = new Marzipano.EquirectGeometry([{ width: 8192 }]);

// Create view.
var limiter = Marzipano.RectilinearView.limit.traditional(8192, 100*Math.PI/180);
var view = new Marzipano.RectilinearView({ yaw:Math.PI/180},limiter);

var data = window.data;

// Create scene.
var scene = viewer.createScene({
  source: source,
  geometry: geometry,
  view: view,
  pinFirstLevel: true,
  data:data
});

//Wyświetlanie info o zdjęciu
var fileMetadata = document.querySelector('#photo_data');
var fileToggleMetadata = document.querySelector('#file_metadata');

// Display scene.
scene.switchTo();

var viewChangeHandler = function() {
  var yaw = view.yaw();
	var d_yaw=yaw/(Math.PI/4)
	console.log('yaw= ' + d_yaw);
  };

var viewPitchHandler = function() {
  var pitch = view.pitch();
	console.log('pitch= ' + pitch);
  };

var viewFovHandler = function() {
  var fov = view.fov();
  var d_fov=fov/(Math.PI/8)
  console.log('fov= ' + fov);
  };
 
view.addEventListener('change', viewChangeHandler);
view.addEventListener('change', viewPitchHandler);
view.addEventListener('change', viewFovHandler);

//////////////////////////// NOWE PODEJŚCIE///////////////////////////////////////////////

var x = document.getElementById("coordinates")
var y = 50.257793416666665
var a = 21.39206213888889
var b = 50.25775097222222
var az = 295

var imgHotspot = document.createElement('img');
imgHotspot.src = 'img/hotspot.png';
imgHotspot.classList.add('hotspot');
imgHotspot.addEventListener('click', function() {
  scene.switchTo();
});

var position = {yaw: ((Math.PI/180)*az)-(Math.atan2(x-a,y-b))};

scene.hotspotContainer().createHotspot(imgHotspot, position);

//////////////////////////// NOWE PODEJŚCIE///////////////////////////////////////////////


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
