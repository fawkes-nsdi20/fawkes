const CDP = require('chrome-remote-interface');

async function example() {
    let client;
    try {
        const args = process.argv;
        // connect to endpoint
        client = await CDP();
        // extract domains
        const {
            Page
        } = client;

        // setup handlers: capture onload event
        Page.loadEventFired((params) => {
            loadEventFiredTime = params.timestamp;
        });

        // enable events then start!
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