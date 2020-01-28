const CDP = require('chrome-remote-interface');

async function example() {
    let client;
    let loadEventFiredTime = 0.0;
    try {
        const args = process.argv;
        // connect to endpoint
        client = await CDP();
        // extract domains
        const {
            Page,
            Network
        } = client;

        // setup handlers: capture onload event
        Page.loadEventFired((params) => {
            loadEventFiredTime = params.timestamp;
        });
        Network.requestWillBeSent((params) => {
           console.log(params.request.url);
        });

        // enable events then start!
        await Network.enable();
        await Page.enable();
        await Page.navigate({
            url: args[2]
        });
        await Page.loadEventFired();

    } catch (err) {
        console.error(err);
    } finally {
        if (client) {
            await client.close();
        }
    }
}

example();