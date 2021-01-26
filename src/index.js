import WalletConnectProvider from "@walletconnect/web3-provider";
import Web3 from "web3";
import  workspace_contract_abi from "./abi.js"

var QRCode = require('qrcode')
var canvas = document.getElementById('canvas')

let web3 = null;
let provider = null;

function onSubscribe() {
  if (!provider) {
    throw new Error(`provider hasn't been created yet`);
  }
  provider.on("accountsChanged", accounts => {
    console.log(accounts);
  });

  provider.on("chainChanged", chainId => {
    console.log(chainId);
  });

  provider.on("close", () => {
    provider = null;
    window.alert("Wallet disconnected !");

  });
}

async function onlogin(mobile) {
  console.log('provider debut oninit = ', provider)
  let mobile_account = "undefined";
  let mobile_wallet = "undefined";
  let mobile_logo = "undefined";
  // init walletconnect with or whithout builtin QR code
  if (mobile == 'mobile') {
    console.log('Call from mobile device');
    provider = new WalletConnectProvider({
      rpc: {
      50000 : "https://talao.co/rpc",
      },
      });
  }
  else {
    console.log('Call from Desktop');
    provider = new WalletConnectProvider({
      rpc: {
        50000 : "https://talao.co/rpc",
        },
        qrcode: false,
        });
    // display custom QRcode
    provider.connector.on("display_uri", (err, payload) => {
    var uri = payload.params[0];
    console.log('uri = ',uri);
    QRCode.toCanvas(canvas, uri,{width : 244}, function (error) {
      if (error) {console.error(error);
      }
      else 
        {console.log('connexion success !');
        console.log('provider = ',provider);}
        })
    });
  }

  onSubscribe();

  await provider.enable()
  .then(value => {
    console.log('value = ',value, 'provider = ', provider);
    mobile_account = provider.accounts[0];
    mobile_wallet = provider.wc._peerMeta['name'];
    mobile_logo = provider.wc._peerMeta['icons'][0];
    })
  .catch(e => {
    console.log(e);
    });

  return [mobile_account, mobile_wallet, mobile_logo];

}

async function getaccountaddress(){
  /*
  This is the standard init call of a page
  */
  provider = new WalletConnectProvider({
    rpc: {
      1 : "https://talao.co/rpc",
    },
    qrcode: false,
  });
  // init provider
  await provider.enable();

  // create web3 object for future use
  web3 = new Web3(provider);

  provider.on("close", () => {
  console.log('appel de on close, provider is disconected')
  });
  console.log('provider = ', provider);
  return [ provider.accounts[0], provider.wc._peerMeta['name'], provider.wc._peerMeta['icons'][0]];
  }

async function onend() {
 if (provider)
 { await provider.disconnect();
  console.log('passage dans onend, provider is disconnected');}
}

async function mypersonalmessage(msg) {
  let signature = null;
  if (!provider) {
    throw new Error(`provider hasn't been created yet`);
  }
  // send personal_sign request
  await provider
    .send({ method: "personal_sign", params: [msg, provider.accounts[0]] })
    .then(result => {
      // Returns message signature
      console.log('signature reçue dans index.js = ',result); // eslint-disable-line
      // check signature here
      signature = result;
    })
    .catch(error => {
      // Error returned when rejected
      console.error(error); // eslint-disable-line
    });
  return signature;
}

async function checksignature(did, signature, msg){
  if (!web3) {
    throw new Error(`web3 hasn't been created yet`);
  }
    // get the list of agent (key = 1) of this did
  const  workspace_contract_address = '0x' + did.split(":")[3];
  const contract = new web3.eth.Contract(workspace_contract_abi, workspace_contract_address);
  const keylist = await contract.methods.getKeysByPurpose(1).call();

  // calculate the keccak256 of the signer
  const signer = web3.eth.accounts.recover(msg, signature);
  const signerpublickey = web3.utils.soliditySha3(signer);
  return keylist.includes(signerpublickey);
}

window.onEnd = onend;
window.onInit = onlogin;
window.sign = mypersonalmessage;
window.getAccountAddress = getaccountaddress;
window.checkSignature= checksignature;
