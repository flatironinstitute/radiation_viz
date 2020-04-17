 

var DATA_DIR = "./processed_data";

var json_data;
var values_array;
var div_status, context, surfaces, voxel_mesh, surface_mesh;
var voxel_camera, voxel_renderer, voxel_scene;
var surface_camera, surface_renderer, surface_scene;
var voxelControls, voxelClock;
var surfaceControls, surfaceClock;
var voxels_initialized = false;
var surface_initialized = false;

var load_config = function() {
    debugger;
    div_status = $("#div_status");
    div_status.html("initializing.")
    //load_json("uniform");
    load_json("uniform");
};

var load_json = function(prefix) {
    var path = DATA_DIR + "/" + prefix + ".json";
    div_status.html("Getting json: " + path);
    $.getJSON(path, get_values).fail(on_load_failure(path));
};

var on_load_failure = function(path) {
    return function () {
        alert(path + ": Could not load local JSON data.\n" +
                "You may need to run a web server to avoid cross origin restrictions.")
    };
};

var get_values = function(data) {
    json_data = data;
    var bin_file_name = json_data.binary_file;
    var bin_file_url = DATA_DIR + "/" + bin_file_name;
    div_status.html("Getting binary: " + bin_file_url);
    var request = new XMLHttpRequest();
    request.open('GET', bin_file_url, true);
    request.responseType = 'blob';
    request.onload = function() {
        div_status.html("Binary loaded: " + bin_file_url);
        var reader = new FileReader();
        reader.readAsArrayBuffer(request.response);
        //reader.readAsDataURL(request.response);
        reader.onload =  function(a){
            div_status.html("Converting binary data: " + bin_file_url);
            values_array = new Float32Array(reader.result);
            do_plot();
        };
    };
    request.onerror = on_load_failure(bin_file_url);
    request.send();
};

var do_plot = function () {
    div_status.html("Initializing plot for " + json_data.binary_file)
    var layerScale = new Float32Array(json_data.r_values);
    var rowScale = new Float32Array(json_data.theta_values);
    var columnScale = new Float32Array(json_data.phi_values);
    context = div_status.feedWebGL2({});

    json_data.grid_mins = [0, 0, 0];
    json_data.grid_maxes = [json_data.phi_size, json_data.theta_size, json_data.r_size];

    var location_parameters = {
        RowScale: rowScale,
        ColumnScale: columnScale,
        LayerScale: layerScale,
    };

    var m = json_data.intensity_min;
    var M = json_data.intensity_max;
    //M = 0.3 // XXXXX TESTING ONLY
    var mid = 0.5 * (m + M);

    surfaces = div_status.webGL2surfaces3dopt(
        {
            feedbackContext: context,
            location: "polar_scaled",
            valuesArray: values_array,
            layerScale: layerScale,
            rowScale: rowScale,
            columnScale: columnScale,
            num_rows: json_data.theta_size,
            num_cols: json_data.phi_size,
            num_layers: json_data.r_size,
            num_blocks: json_data.num_blocks,
            color: [1, 0, 0],
            rasterize: true,
            threshold: mid,
            shrink_factor: 0.05,  // how much to shrink the arrays
            location: "polar_scaled",
            location_parameters: location_parameters,
        }
    );

    surfaces.set_grid_limits(json_data.grid_mins, json_data.grid_maxes);

    var slider = $("#value_slider");
    slider.empty();
    var slider_readout = $("#value_readout");

    var update_slider = (function () {
        var threshold = + slider.slider("option", "value");
        slider_readout.html(threshold.toFixed(5));
        surfaces.set_threshold(threshold);
        //surfaces.run();
        // only run the voxels initially
        surfaces.crossing.get_compacted_feedbacks();
        if (voxels_initialized) {
            update_voxels();
        } else {
            initialize_voxels();
            voxels_initialized = true;
        }
    });

    slider.slider({
        min: m,
        max: M,
        value: 0.5*(m+M),
        step: 0.001*(M-m),
        slide: update_slider,
        change: update_slider,
    })
    update_slider();

    var sync_button = $("#sync_button");

    var sync_surface = function () {
        if (surface_initialized) {
            update_surface();
        } else {
            initialize_surface();
            surface_initialized = true;
        }
    };
    sync_button.click(sync_surface);

    $("#focus_button").click(function() {
        var camera_shift = 2;
        surfaces.crossing.reset_three_camera(voxel_camera, camera_shift, voxelControls);
        surfaces.crossing.reset_three_camera(surface_camera, camera_shift, surfaceControls);
        sync_cameras();
    });

    var col_slider = set_up_dim_slider("X_slider", json_data.r_size, 2, "R limits");
    var row_slider = set_up_dim_slider("Y_slider", json_data.theta_size, 1, "theta limits");
    var layer_slider = set_up_dim_slider("Z_slider", json_data.phi_size, 0, "phi limits");
};

set_up_dim_slider = function(container, dim, index, label) {
    var $container = $("#"+container);
    $container.empty();
    $("<div>" + label + "</div>").appendTo($container);
    var slider = $("<div></div>").appendTo($container);
    var step = Math.max(0.01 * dim, 1);
    var update = function () {
        var limits = slider.slider("option", "values");
        json_data.grid_mins[index] = limits[0];
        json_data.grid_maxes[index] = limits[1];
        surfaces.set_grid_limits(json_data.grid_mins, json_data.grid_maxes);
        surfaces.crossing.get_compacted_feedbacks();
        if (voxels_initialized) {
            update_voxels();
        }
    };
    slider.slider({
        range: true,
        min: -1,
        max: dim+1,
        step: step,
        values: [0, dim],
        slide: update,
        change: update,
    });
    json_data.grid_maxes[index] = dim+1;
    return slider;
};
sync_cameras = function () {
    // https://stackoverflow.com/questions/49201438/threejs-apply-properties-from-one-camera-to-another-camera
    var d = new THREE.Vector3(),
        q = new THREE.Quaternion(),
        s = new THREE.Vector3();
    voxel_camera.matrixWorld.decompose( d, q, s );
    surface_camera.position.copy( d );
    surface_camera.quaternion.copy( q );
    surface_camera.scale.copy( s );
};

var update_surface = function () {
    surfaces.run();
    surfaces.check_update_link();
    sync_cameras();
    surface_renderer.render( surface_scene, surface_camera );
};

var initialize_surface = function () {
    surfaces.run();
    var container = document.getElementById( 'isosurface' );
    var $container = $(container);
    $container.empty();
    var canvas = document.createElement( 'canvas' ); 
    var context = canvas.getContext( 'webgl2', { alpha: false } ); 
    var renderer = new THREE.WebGLRenderer( { canvas: canvas, context: context } );
    surface_renderer = renderer;

    //renderer = new THREE.WebGLRenderer();
    renderer.setPixelRatio( window.devicePixelRatio );
    renderer.setSize( $container.width(), $container.height() );
    //renderer.setSize( window.innerWidth, window.innerHeight );
    renderer.outputEncoding = THREE.sRGBEncoding;
    container.appendChild( renderer.domElement );

    var camera = new THREE.PerspectiveCamera( 45, $container.width()/$container.height(), 0.1, 10000 );
    surface_camera = camera;

    var material = new THREE.MeshNormalMaterial( {  } );
    material.side = THREE.DoubleSide;

    var geometry = this.surfaces.linked_three_geometry(THREE);

    var mesh = new THREE.Mesh( geometry,  material );
    surface_mesh = mesh;

    var scene = new THREE.Scene();
    surface_scene = scene;

    scene.add(mesh);

    sync_cameras();
    //surface_renderer.render( surface_scene, surface_camera ); // in animate

    surfaceControls = new THREE.OrbitControls(camera, renderer.domElement);
    surfaceControls.userZoom = false;
    surfaceClock = new THREE.Clock();
};

var initialize_voxels = function () {
    var container = document.getElementById( "voxels" );
    var $container = $(container);
    $container.empty();
    var canvas = document.createElement( 'canvas' ); 
    var context = canvas.getContext( 'webgl2', { alpha: false } ); 
    var renderer = new THREE.WebGLRenderer( { canvas: canvas, context: context } );
    voxel_renderer = renderer;

    renderer.setPixelRatio( window.devicePixelRatio );
    renderer.setSize( $container.width(), $container.height() );
    renderer.outputEncoding = THREE.sRGBEncoding;
    container.appendChild( renderer.domElement );
    var camera = new THREE.PerspectiveCamera( 45, $container.width()/$container.height(), 0.1, 10000 );
    voxel_camera = camera;

    var voxels = surfaces.crossing;
    voxels.reset_three_camera(camera, 2.5);

    var scene = new THREE.Scene();
    voxel_scene = scene;

    var mesh = voxels.get_points_mesh({
        THREE: THREE,
        colorize: true,
    });
    voxel_mesh = mesh;
    scene.add(mesh);

    var axesHelper = new THREE.AxesHelper( 15 );
    scene.add(axesHelper);
    var g = new THREE.SphereGeometry(0.1, 6,6);
    var m = new THREE.MeshNormalMaterial();
    m.wireframe = true;
    var c = new THREE.Mesh(g, m);
    scene.add(c);

    //voxel_renderer.render( voxel_scene, voxel_camera );
    
    voxelControls = new THREE.OrbitControls(camera, renderer.domElement);
    voxelControls.userZoom = false;
    voxelClock = new THREE.Clock();

    animate();
};

var update_voxels = function () {
    voxel_mesh.update_sphere_locations(surfaces.crossing.compact_locations);
};

var animate = function () {
    var delta = voxelClock.getDelta();
    voxelControls.update(delta);

    if (surfaceClock) {
        delta = surfaceClock.getDelta();
        surfaceControls.update(delta);
    }

    voxel_renderer.render( voxel_scene, voxel_camera );
    if (surface_renderer) {
        surface_renderer.render( surface_scene, surface_camera );
    }
    requestAnimationFrame( animate );
};
