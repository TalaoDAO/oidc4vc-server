
//import Web3 from "./node_modules/web3";
import WalletConnectProvider from "./@walletconnect/web3-provider";

//  Create WalletConnect Provider
const provider = new WalletConnectProvider({
  rpc: {
    50000 : "http://18.190.21.227:8502"
  },
});

//  Enable session (triggers QR Code modal)
//await provider.enable();

//var web3 = new Web3(new Web3.providers.HttpProvider('http://18.190.21.227:8502'));

//  Create Web3 instance
const web3 = new Web3(provider);


web3.eth.getChainId().then(value => {
    document.getElementById("demo").innerHTML= value;
    document.getElementById("other").innerHTML= 2*value;
    }, reason => {
    document.getElementById("demo").innerHTML= reason;
    });