const config = require("../../Config Files/config");
const muxBroker = require("../../Brokers/Mux/muxBroker");
const WebSocket = require('../../Program Files/node_modules/ws');

// Create a WebSocket server
const wss = new WebSocket.Server({ port: 8080 });
console.log('MUX Websocket Server Initialized')

// Handle incoming connections
wss.on('connection', (ws) => {
    // Handle incoming messages
    ws.on('message', async (message) => {
        try {
            // Parse the message as JSON
            const msg = JSON.parse(message.toString('utf8'));
            // Check the message type
            if (msg.type === "managePositionOrder") {
                // Call the managePositionOrder function
                var data = await muxBroker.managePositionOrder(
                    config.assets[msg.asset][msg.orderType.toLowerCase() + 'Address'],
                    msg.tradeAmount,
                    msg.multiplier,
                    msg.price,
                    0,
                    msg.flag,
                    msg.wssNode,
                    msg.mnemonic,
                    msg.walletAddress
                );
            } else if (msg.type === "cancelPositionOrder") {
                // Call the cancelPositionOrder function
                var data = await muxBroker.cancelPositionOrder(
                    msg.orderId,
                    msg.wssNode,
                    msg.mnemonic,
                    msg.walletAddress
                );
            }
            // Send the data back to the client
            ws.send(JSON.stringify(data));
        } catch (error) {
            console.error(error);
            ws.send('error');
        }
    });
});