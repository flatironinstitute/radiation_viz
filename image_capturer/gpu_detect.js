
/*

Report on what GPU hardware if any the headless browser will use.


Run the script on a machine and examine the output: for example

1) Run on a mac:

$ node gpu_detect.js 
(node:36263) ExperimentalWarning: The fs.promises API is experimental
Chrome/81.0.4044.129
AMD Radeon Pro 560X OpenGL Engine

Indicates the AMD GPU will be used.

2) Run on a Linux machine with no GPU:

$ node gpu_detect.js 
HeadlessChrome/81.0.4044.0
Google SwiftShader

Indicates that the SwiftShader software emulation will be used (this is very slow!).

3) Run on a cluster node with a GPU but no display (in the flatiron cluster):

(nodetest) -bash-4.2$ module load slurm
(nodetest) -bash-4.2$ srun -N1 --pty --exclusive --gres=gpu:1 -p gpu bash -i
srun: job 553633 queued and waiting for resources
srun: job 553633 has been allocated resources
(base) bash-4.2$ 
(base) bash-4.2$ source activate nodetest
(nodetest) bash-4.2$ node gpu_detect.js 
HeadlessChrome/81.0.4044.0
Tesla P100-PCIE-16GB/PCIe/SSE2
(base) bash-4.2$ 
(nodetest) bash-4.2$ exit

Indicates the Tesla P100-PCIE-16GB/PCIe/SSE2 will be used

Possible arguments

   node gpu_detect.js mac
     -- Use standard installed Chrome location on a mac instead of default.

*/

const puppeteer = require('puppeteer');
const fs = require("fs");

// https://stackoverflow.com/questions/47587352/opening-local-html-file-using-puppeteer

(async() => {
  var parameters = {};
  parameters.headless = true;
  var args = {};
  for (var i=0; i<process.argv.length; i++) {
    args[process.argv[i]] = 1;
  }
  if (args.mac) {
    parameters.executablePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  }
  parameters.args = ["--no-sandbox", "--use-gl=egl"];
  const browser = await puppeteer.launch(parameters);
  try {
  console.log(await browser.version());
  const page = await browser.newPage();
  //var url = "file:///detect.html";
  //await page.goto(url, { waitUntil: 'networkidle2' });
  var contentHtml = fs.readFileSync('./detect.html', 'utf8');
  await page.setContent(contentHtml);
  console.log(await page.evaluate("detect()"));
  } catch (error) {
      console.log(error.message);
  }
  browser.close();
})();