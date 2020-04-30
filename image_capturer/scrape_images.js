/*
Scrape canvas images from a visualization instance using puppeteer and a headless browser

$ node scrape_images.js to_directory initial_url limit

Starting with initial_url get images and put them in to_directory up to limit (no limit if limit<=0).

For example:

$ node scrape_images.js \
        http://localhost:8080/repos/radiation_viz/docs/index.html \
        /Users/awatters/tmp/viz \
        3
*/

const puppeteer = require('puppeteer');
//const fs = require("fs");
const Jimp = require('jimp')

var browser = null;

var run = (async() => {

    var argv = process.argv;
    console.log(argv);
    var to_directory = argv[3];
    var initial_url = argv[2];
    var limit = +(argv[4]);
    console.log(`Starting with ${initial_url} scrape images and put them in ${to_directory} up to ${limit} (no limit if limit<=0).`);

    // should refactor common logic xxxx
    var parameters = {};
    parameters.headless = true;
    parameters.args = ["--no-sandbox", "--use-gl=egl"];
    browser = await puppeteer.launch(parameters);
    console.log(await browser.version());
    const page = await browser.newPage();
    await page.setViewport({width: 6000, height:3000});
    await page.goto(initial_url, { waitUntil: 'networkidle2' });
    console.log(await page.evaluate("'Scraper webgl engine detected: ' + detect_gpu()"));
    var count = 0;
    function sleep(time) {
        return new Promise(function(resolve) { 
            setTimeout(resolve, time)
        });
    }
    await sleep(10000);
    while ((limit <= 0) || (count < limit)) {
        await page.waitForFunction('voxels_drawn');
        var prefix = await page.evaluate('chosen_prefix');
        console.log("at " + count + " scraping prefix " + prefix);
        await page.evaluate("initialize_surface();")
        await page.waitForFunction('surface_drawn');
        await page.evaluate("stop_animation = true");
        console.log("scraper: now getting canvas data");
        const data = await page.evaluate("get_canvas_data_json_object()")
        console.log("scraper: width: " + data.width + ", height: " + data.height);
        console.log("scraper: length: " + data.data.length);
        var d = data.data;
        var w = data.width;
        var h = data.height;
        var buff = new Uint8Array(d);
        var path = to_directory + "/" + prefix + ".png";
        
        new Jimp({ data: buff, width: w, height: h}, (err, image) => {
            if (err) {
                console.log("error: "+ err);
                //throw new Error(err);
            } else {
                image.flip(false, true).write(path);
            }
        });
        
        count ++;
        console.log("scraper at " + count + " wrote " + path);
        var next_url = await page.evaluate("load_next('', true)")
        if (next_url) {
            console.log("scraper loading next url and sleeping: " + next_url);
            await page.goto(next_url, { waitUntil: 'networkidle2' });
            await sleep(10000);
        } else {
            console.log("scraper: no next url at " + count);
            break;
        }
    }
    //browser.close();
    console.log("Scraper done at count " + count);

});

(async() => {
    try {
        await run();
    } finally {
        browser.close();
    }
})();
