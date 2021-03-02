const webpack = require("webpack");
const path = require("path");

let config = {
   mode: 'development',
    entry: "./src/index.js",
    output: {
      path: path.resolve(__dirname, "/home/thierry/Talao/static"),
      filename: "./wc-talao.min.js"
    },
node: {
  fs: "empty"
}
}
  module.exports = config;
