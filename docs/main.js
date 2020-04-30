 

var DATA_DIR = "./processed_data";
var CONFIG_FILENAME = "./config.json";

// limit dropdown to this length
var option_limit = 100;

var json_data, json_config, chosen_prefix, chosen_index, searchParams, main_url;
var voxels_canvas, surface_canvas;
var voxels_context, surface_context;
var values_array;
var div_status, context, surfaces, voxel_mesh, surface_mesh;
var voxel_camera, voxel_renderer, voxel_scene;
var surface_camera, surface_renderer, surface_scene;
var voxelControls, voxelClock;
var surfaceControls, surfaceClock;
var voxels_initialized = false;
var surface_initialized = false;
var voxels_drawn = false;
var surface_drawn = false;
var stop_animation = false;
var threshold, threshold_slider;

var load_config = function() {
    div_status = $("#div_status");
    div_status.html("loading configuration.");
    $.getJSON(CONFIG_FILENAME, process_config).fail(on_load_failure(CONFIG_FILENAME));
    searchParams = new URLSearchParams();
};

var process_config = function(data) {
    json_config = data
    div_status.html("initializing: " + detect_gpu());
    var files_info = data.files;
    chosen_prefix = files_info[0].prefix;
    chosen_index = 0;
    // look for prefix in url
    var url = location.toString();
    var split = url.split("?");
    if (split.length > 1) {
        searchParams = new URLSearchParams(split[1]);
    }
    var q = searchParams.get("q");
    main_url = url.split("?")[0];
    for (var i=0; i<files_info.length; i++) {
        var prefix = files_info[i].prefix;
        if (q == prefix) {
            chosen_prefix = prefix;
            chosen_index = i;
        }
    }
    // populate the dropdown selection
    var selection_span = $("#dataset_selection");
    var selection = $("<select/>").appendTo(selection_span);
    for (var i=0; i<files_info.length; i++) {
        var prefix = files_info[i].prefix;
        var option = $("<option/>");
        option.attr("value", prefix);
        option.text(prefix);
        if (prefix == chosen_prefix) {
            option.attr("selected", "selected");
        }
        selection.append(option);
        if (i > option_limit) {
            break;
        }
    }
    var select_change = function() {
        var val = selection.val();
        document.location.href = main_url + "?q=" + val;
    };
    selection.change(select_change)
    //load_json("uniform");
    load_json(chosen_prefix);
};

var detect_gpu = function() {
    var canvas = document.createElement('canvas');
    var gl;
    var debugInfo;
    var vendor;
    var renderer = "WEBGL NOT SUPPORTED";

    try {
        gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    } catch (e) {
    }

    if (gl) {
        debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
        vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
        renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
    }
    return renderer;
};

var load_next = function(match_string, delayed) {
    var data = json_config;
    var files_info = data.files;
    var next_index;
    var next_prefix;
    for (var index = chosen_index+1; index < files_info.length; index++) {
        var prefix = files_info[index].prefix;
        if ((!match_string) || (prefix.includes(match_string))) {
            next_index = index;
            next_prefix = prefix;
            break;
        }
    }
    if (!next_index) {
        var load_button = $("#load_next");
        load_button.html("NO NEXT")
        return null;  // No next file
    }
    chosen_index = next_index;
    chosen_prefix = next_prefix;
    var camera_json = get_camera_json_string();
    // invalidate the json data
    json_data = null;
    var href = main_url + "?q=" + chosen_prefix + "&camera=" + camera_json;
    if (!delayed) {
        document.location.href = href;
    }
    return href;
};

var load_json = function(prefix, next_action) {
    next_action = next_action || get_values;
    var path = DATA_DIR + "/" + prefix + ".json";
    div_status.html("Getting json: " + path);
    var on_success = function(data) { return next_action(data); }
    $.getJSON(path, on_success).fail(on_load_failure(path));
};

var on_load_failure = function(path) {
    return function () {
        alert(path + ": Could not load local JSON data.\n" +
                "You may need to run a web server to avoid cross origin restrictions.")
    };
};

var get_values = function(data, next_action) {
    next_action = next_action || do_plot;
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
            next_action();
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

    //json_data.grid_mins = [0, 0, 0];
    //json_data.grid_maxes = [json_data.phi_size, json_data.theta_size, json_data.r_size];
    var extremum = function(f, a) {
        var result = a[0];
        for (var i=0; i<a.length; i++) {
            result = f(result, a[i]);
        }
        return result;
    }
    var mina = function(a) { return extremum(Math.min, a); }
    var maxa = function(a) { return extremum(Math.max, a); }
    json_data.grid_mins = [mina(layerScale), mina(rowScale), mina(columnScale), ];
    json_data.grid_maxes = [maxa(layerScale), maxa(rowScale), maxa(columnScale), ];

    var location_parameters = {
        RowScale: rowScale,
        ColumnScale: columnScale,
        LayerScale: layerScale,
    };

    var m = json_data.intensity_min;
    var M = json_data.intensity_max;
    //M = 0.3 // XXXXX TESTING ONLY
    var mid = 0.5 * (m + M);
    threshold = mid;

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
    threshold_slider = slider
    slider.empty();
    var slider_readout = $("#value_readout");

    var update_slider = (function () {
        threshold = + slider.slider("option", "value");
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
        value: threshold,
        step: 0.001*(M-m),
        slide: update_slider,
        change: update_slider,
    })
    update_slider();

    var sync_button = $("#sync_button");

    sync_button.click(sync_surface);

    $("#focus_button").click(function() {
        var camera_shift = 2;
        surfaces.crossing.reset_three_camera(voxel_camera, camera_shift, voxelControls);
        surfaces.crossing.reset_three_camera(surface_camera, camera_shift, surfaceControls);
        sync_cameras();
    });

    var col_slider = set_up_dim_slider("X_slider", json_data.r_size, 2, "Phi limits");
    var row_slider = set_up_dim_slider("Y_slider", json_data.theta_size, 1, "Theta limits");
    var layer_slider = set_up_dim_slider("Z_slider", json_data.phi_size, 0, "R limits");
};

var sync_surface = function () {
    if (surface_initialized) {
        update_surface();
    } else {
        initialize_surface();
        surface_initialized = true;
    }
};

var set_up_dim_slider = function(container, dim, index, label) {
    var $container = $("#"+container);
    var M = json_data.grid_maxes[index];
    var m = json_data.grid_mins[index];
    $container.empty();
    $("<div>" + label + "</div>").appendTo($container);
    var slider = $("<div></div>").appendTo($container);
    var step = Math.max(0.01, 0.01 * (M - m));
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
        min: m - step,
        max: M + step,
        step: step,
        values: [m, M],
        slide: update,
        change: update,
    });
    //json_data.grid_maxes[index] = dim+1;
    return slider;
};

var sync_cameras = function () {
    // https://stackoverflow.com/questions/49201438/threejs-apply-properties-from-one-camera-to-another-camera
    var d = new THREE.Vector3(),
        q = new THREE.Quaternion(),
        s = new THREE.Vector3();
    voxel_camera.matrixWorld.decompose( d, q, s );
    surface_camera.position.copy( d );
    surface_camera.quaternion.copy( q );
    surface_camera.scale.copy( s );
};

var get_canvas_data_json_object = function (context, renderer, scene, camera) {
    // https://stackoverflow.com/questions/9470043/is-an-imagedata-canvaspixelarray-directly-available-to-a-canvas-webgl-context
    var gl = context || surface_context;
    renderer = renderer || surface_renderer;
    scene = scene || surface_scene;
    camera = camera || surface_camera;
    var w = gl.drawingBufferWidth;
    var h = gl.drawingBufferHeight;
    // this may leak resources if called many times?  xxxx
    var bufferTexture = new THREE.WebGLRenderTarget( w, h, { minFilter: THREE.LinearFilter, magFilter: THREE.NearestFilter});
    // render to a texture so we can read the pixels (?)
    renderer.setRenderTarget(bufferTexture);
    renderer.render(scene, camera);
    var buf = new Uint8Array(w * h * 4);
    //var sync = gl.fenceSync(gl.SYNC_GPU_COMMANDS_COMPLETE, 0);
    //gl.waitSync(sync, 0, gl.TIMEOUT_IGNORED);
    gl.flush();
    gl.finish();
    gl.readPixels(0, 0, w, h, gl.RGBA, gl.UNSIGNED_BYTE, buf);

    // xxxx debug code
    /*
    var maxes = [0,0,0,0];
    var mins = [255,255,255,255];
    //var jimg = new Jimp(w, h);
    for (var x=0; x<w; x++) {
        for (var y=0; y<h; y++) {
        var i = 4 * (y * w + x);
        for (var j=0; j<4; j++) {
            var k = i + j;
            var dk = buf[k]
            maxes[j] = Math.max(maxes[j], dk)
            mins[j] = Math.min(mins[j], dk)
        }
        }
    }
    console.log("maxes", maxes);
    console.log("mins", mins)
    */

    var data = Array.from(buf);
    return {data: data, height: h, width: w};
};

var get_camera_json_string = function () {
    var d = new THREE.Vector3(),
        q = new THREE.Quaternion(),
        s = new THREE.Vector3();
    voxel_camera.matrixWorld.decompose( d, q, s );
    var object = {
        d: d.toArray(),
        q: q.toArray(),
        s: s.toArray(),
        threshold: threshold,
    };
    return JSON.stringify(object);
};

var set_camera_from_json_string = function(s) {
    var object = JSON.parse(s);
    var d = new THREE.Vector3(),
        q = new THREE.Quaternion(),
        s = new THREE.Vector3();
    d.fromArray(object.d);
    q.fromArray(object.q);
    s.fromArray(object.s);
    voxel_camera.position.copy( d );
    voxel_camera.quaternion.copy( q );
    voxel_camera.scale.copy( s );
    threshold_slider.slider({value: object.threshold});
    sync_surface();
    if (surface_camera) {
        surface_camera.position.copy( d );
        surface_camera.quaternion.copy( q );
        surface_camera.scale.copy( s );
    }
    //threshold_slider.slider({value: object.threshold});
    //sync_surface();
    //sync_cameras();
};

var download_camera_settings = function () {
    var content = get_camera_json_string();
    var type = type="text/plain;charset=utf-8";
    var name = "camera_settings.json";
    var the_blob = new Blob([content], {type: type});
    saveAs(the_blob, name);
};

var update_surface = function () {
    surfaces.run();
    surfaces.check_update_link();
    sync_cameras();
    surface_renderer.render( surface_scene, surface_camera, null );
};

var initialize_surface = function () {
    surfaces.run();
    var container = document.getElementById( 'isosurface' );
    var $container = $(container);
    $container.empty();
    var canvas = document.createElement( 'canvas' ); 
    surface_canvas = canvas;
    var context = canvas.getContext( 'webgl2', { alpha: false } ); 
    surface_context = context;
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
    surface_initialized = true;
};

var initialize_voxels = function () {
    voxels_initialized = true;
    var container = document.getElementById( "voxels" );
    var $container = $(container);
    $container.empty();
    var canvas = document.createElement( 'canvas' ); 
    voxels_canvas = canvas;
    var context = canvas.getContext( 'webgl2', { alpha: false } ); 
    voxels_context = context;
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

    var camera_json = searchParams.get("camera");
    if (camera_json) {
        // auto load isosurface and set up cameras
        initialize_surface();
        //surface_initialized = true;
        set_camera_from_json_string(camera_json);
    }

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

    voxel_renderer.setRenderTarget(null);
    voxel_renderer.render( voxel_scene, voxel_camera);
    voxels_drawn = true;
    if (surface_renderer) {
        surface_renderer.setRenderTarget(null);
        surface_renderer.render( surface_scene, surface_camera);
        surface_drawn = true;
    }
    if (!stop_animation) {
        requestAnimationFrame( animate );
    }
};
