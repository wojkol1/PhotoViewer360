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

// Display scene.
scene.switchTo();

var viewChangeHandler = function() {
  var yaw = view.yaw();
	var d_yaw=yaw/(Math.PI/180)
	console.log('yaw= ' + d_yaw);
  };
 
view.addEventListener('change', viewChangeHandler);

//////////////////////////// NOWE PODEJŚCIE///////////////////////////////////////////////

const positions =[]
const coord_x =[]
const coord_y =[]

let data_coord = pythonSlot.getPhotoDetails();
//alert(data_coord.toString());
//$('#coord').text(data_coord.toString());

var aLines = data_coord.toString().split(",")
aLines.forEach(function(element){
// $('#coord').text(coord_end);
    var coord = element.split(" ")
//    $('#coord').text(coord[0]);
    if (coord[2] === '0.0'){
      var x = parseFloat(coord[0])
      var y = parseFloat(coord[1])
//      $('#coord').text(aLines);
      for (let i=0; i<(aLines.length); i++){
//         $('#coord').text(aLines[i]);
//        var coord_substr = aLines[i].substr(2)
        // $('#coord').text(aLines);
//        var coord_end = coord_substr.replace("'","").replace("]","")
        var coord = aLines[i].split(" ")
//         $('#coord').text('coord: '+coord);
          if (coord[2]!='0.0'){
            // $('#coord').text('coord: '+coord);
            var x1 = parseFloat(coord[0])
            coord_x.push(x1)
            var y1 = parseFloat(coord[1])
            coord_y.push(y1)
            var az = 295
            var position = (Math.PI/180)*az-(Math.atan2(x-x1,y-y1))
            // $('#coord').text('x1= '+x1+'x= '+x+'position: '+position);
            positions.push(position)
          }
      }
    }
})

for (let i=0; i<positions.length; i++) {
  var container = document.getElementById('container');
  container.innerHTML += '<div id="link-hotspot"><img class="link-hotspot-icon" src="img/hotspot.png"></div>'
}
var list = document.querySelectorAll("#link-hotspot");

for (let i=0; i<list.length; i++) {
  scene.hotspotContainer().createHotspot(list[i], {yaw: positions[i]});
  list[i].addEventListener('click', function() {
  /*
  pythonSlot - obiekt js umożliwiający komunikację z pythonem
  */
//      let a = pythonSlot.getPhotoDetails();
//      alert(a.toString());
  pythonSlot.showMessage('Hello from WebKit');
  pythonSlot.setXYtoPython(coord_x[i], coord_y[i], True)

  $('#coord').text('x= ' + coord_x[i]+', y= '+coord_y[i]);
  var coord = document.getElementById('coord');
  coord.innerHTML += toString(x+","+y)
});
}

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