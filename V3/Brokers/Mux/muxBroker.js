const config = require("../../Config Files/config");
const Web3 = require('../../Program Files/node_modules/web3');
const ethers = require('../../Program Files/node_modules/ethers');

const options = {
    reconnect: {
        auto: true,
        delay: 5000,
        maxAttempts: 10,
        onTimeout: false,
    },
}

/**
 * Initialize the MUX router contract
 * @param {string} wssNode - The wssNode url
 * @param {string} mnemonic - The mnemonic for the account
 * @return {Contract} muxRouter - The initialized MUX router contract
 */
 function initializeMuxRouter(wssNode, mnemonic) {
    // Create a WebSocket provider
    const wsProvider = new ethers.providers.WebSocketProvider(wssNode)
    // Create a wallet from the mnemonic
    const wallet = new ethers.Wallet.fromMnemonic(mnemonic)
    // Connect the wallet to the WebSocket provider
    const account = wallet.connect(wsProvider)
    // Create a new contract instance
    const muxRouter = new ethers.Contract(
        config.muxRouterContract,
        config.muxRouterAbi,
        account
    )
    return muxRouter
}

/**
 * Allows for limit buys (flag 128), limit sells (flag 32), and stop loss orders (flag 48)
 * @param {number} subAccountId - The ID of the sub-account to place the order on
 * @param {number} collateralAmount - The amount of collateral to use for the order
 * @param {number} multiplier - A multiplier to apply to the collateralAmount
 * @param {number} price - The price of the order
 * @param {number} profitTokenId - The ID of the token to receive profits in
 * @param {number} flag - The flag to use for the order (128 for limit buy, 32 for limit sell, 48 for stop loss)
 * @param {string} wssNode - The wssNode url
 * @param {string} mnemonic - The mnemonic for the account
 * @param {string} walletAddress - The address of the wallet
 * @return {Promise} tx - The transaction object for the placed order
 */
 async function managePositionOrder(accountId, collateralAmount, multiplier, price, profitTokenId, flag, wssNode, mnemonic, walletAddress) {
    // Build subAccountId
    const subAccountId = walletAddress + accountId 
    // Initialize the MUX router contract
    const muxRouter = initializeMuxRouter(wssNode, mnemonic)
    // Initialize a web3 instance
    const web3 = new Web3(
        new Web3.providers.WebsocketProvider(
            wssNode,
            options
        )
    )
    // Get the nonce of the account
    var nonce = await web3.eth.getTransactionCount(
        walletAddress
    )
    // Get the gas price
    var gp = await web3.eth.getGasPrice()
    // Fix the price to 2 decimal places
    price = parseFloat(price).toFixed(2)
    // Calculate the size of the order
    var size = (collateralAmount / price).toFixed(10)
    size = await web3.utils.toWei(size.toString(), 'ether')
    size = parseInt(size * multiplier).toString()
    // If the flag is a limit sell or stop loss order, set the collateral amount to 0
    if (flag == 32 || flag == 48) {
        collateralAmount = 0
    }
    // Place the order
    const tx = await muxRouter.placePositionOrder2(subAccountId, collateralAmount * 1000000, size, ethers.BigNumber.from((price * 1e+18).toLocaleString('fullwide', {
        useGrouping: false
    })), profitTokenId, flag, Math.floor(Date.now() / 1000) + 31536300, config.muxReferralCode, {
        nonce: nonce,
        gasPrice: gp,
    })
    return tx
}

/**
 * Cancel an order placed on the MUX network by ID
 * @param {number} orderId - The ID of the order to cancel
 * @param {string} wssNode - The wssNode url
 * @param {string} mnemonic - The mnemonic for the account
 * @param {string} walletAddress - The address for the account
 * @return {Promise} tx - The transaction object for the cancellation
 */
 async function cancelPositionOrder(orderId, wssNode, mnemonic, walletAddress) {
    // Initialize the MUX router contract
    const muxRouter = initializeMuxRouter(wssNode, mnemonic)
    // Initialize a web3 instance
    const web3 = new Web3(
        new Web3.providers.WebsocketProvider(
            wssNode,
            options
        )
    )
    // Get the nonce of the account
    var nonce = await web3.eth.getTransactionCount(
        walletAddress
    )
    // Get the gas price
    var gp = await web3.eth.getGasPrice()
    // Cancel the order
    const tx = await muxRouter.cancelOrder(orderId, {
        nonce: nonce,
        gasPrice: gp,
    })
    return tx
}

module.exports = {
    managePositionOrder,
    cancelPositionOrder
}