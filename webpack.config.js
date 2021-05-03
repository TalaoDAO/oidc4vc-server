const webpack = require("webpack");
const path = require("path");

let config = {
  mode: 'development',
  entry : "./node_modules/@decentralized-identity/did-crypto-typescript/dist/lib/DidKey.js",
  //entry: "./src/index.js",
  output: {
      path: path.resolve(__dirname, "/home/thierry/Talao/static"),
      filename: "./didkey.js"
    },
  node: {
    fs: "empty"
  },
 
}
module.exports = config;
