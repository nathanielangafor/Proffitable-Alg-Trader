const WebSocket = require('/Users/appleid/Desktop/Other Files/V3/Program Files/node_modules/ws');

// Create a WebSocket server
const wss = new WebSocket.Server({ port: 8080 });

// Define a handler for incoming connections
wss.on('connection', (ws) => {
  // Define a handler for incoming messages
  ws.on('message', async (message) => {
    try {
      // Parse the message and pass the relevant data to the position manager
      const msg = JSON.parse(message.toString('utf8'));
      console.log(
        msg.asset + msg.type.toString().replace(/^\w/, c => c.toUpperCase()),
        msg.tradeSize,
        msg.multiplier,
        msg.price,
        0,
        msg.flag,
        msg.asset
      );
      // Send a success message to the client
      ws.send('SUCCESS');
    } catch (error) {
      console.error(error);
      // Send a fail message to the client
      ws.send('FAIL');
    }
  });
});
