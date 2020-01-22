for (let j = 0; j < process.argv.length; j++) {
    console.log(j + ' -> ' + (process.argv[j]));
}

if (process.argv.length < 5) {
    console.log('Usage: yarn pwmetrics URL --config=pwmetrics_config.js out_path [cold/warm]');
    console.log('out_path and/or type of caching is missing from arguments!');
    process.exit(1);
}
let url = process.argv[2];
// same out_path (outPath) should be used for warm caches.
let outPath = process.argv[4];
// showing the type of caching; either 'cold' or 'warm'
let caching = process.argv[5];

// The version of chrome which is capable of caching the main page
// should be placed under a directory called chrome-caching, next to this file.
let chromeCachingBinary = __dirname + '/experiments/chrome-caching/chrome';
let numOfRuns = 1;
// let jsonOutputPath = 'out/dontcare.json';
let userDataDir = '/tmp/' + outPath;

if (caching == 'warm') {
    numOfRuns = 5;
    // jsonOutputPath = 'out/' + outPath + '/warm.json';
} else if (caching == 'cold') {
    numOfRuns = 5;
    // jsonOutputPath = 'out/' + outPath + '/cold.json';
    userDataDir = '/tmp/nonexistent\$(date +%s%N)';
}

let flags = '--allow-insecure-localhost' +
    ' --disable-background-networking' +
    ' --disable-default-apps' +
    ' --disable-logging' +
    ' --headless' +
    ' --ignore-certificate-errors' +
    ' --incognito' +
    ' --no-check-certificate' +
    ' --no-default-browser-check' +
    ' --no-first-run' +
    ' --user-data-dir=' + userDataDir;

module.exports = {
    url: url,
    flags: {
        runs: numOfRuns,
        chromePath: chromeCachingBinary,
        chromeFlags: flags
    },
};

//json: true,
//outputPath: jsonOutputPath,

