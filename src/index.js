import WalletConnectProvider from "@walletconnect/web3-provider";
import Web3 from "web3";
import {createworkspacekeys} from "./talao_encryption.js";
import {workspace_contract_abi} from "./constant.js";
import {did_authn, sign_message} from "./talao_transaction.js";

const QRCode = require('qrcode');
const canvas = document.getElementById('canvas');
const wc_on = '<i title ="Crypto Wallect connected" style="color: chartreuse;" class="fa fa-mobile-phone fa-3x"></i>';
const wc_off = '<i title="Crypto wallet disconnected" style="color: crimson;" class="fa fa-mobile-phone fa-3x"></i>';


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
    document.getElementById("connected").innerHTML = wc_off;

  });
}


async function onend() {
  if (provider)
  { await provider.disconnect();
    document.getElementById("connected").innerHTML = wc_off;
   console.log('Provider is disconnected');}
 }

async function onlogin(mobile) {
  console.log('provider = ', provider)
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
        console.log('provider = ',provider);
      }
        })
    });
  }

  onSubscribe();

  await provider.enable()
  .then(value => {
    console.log('value = ',value, 'provider = ', provider, 'accounts =', provider.accounts);
    mobile_account = provider.accounts[0];
    mobile_wallet = provider.wc._peerMeta['name'];
    mobile_logo = provider.wc._peerMeta['icons'][0];
    document.getElementById("connected").innerHTML = wc_on;
    })
  .catch(e => {
    console.log(e);
    });

  // create web3 object for future use
  web3 = new Web3(provider);

  if (!web3.utils.isAddress(mobile_account)) {
      console.log(`it s not an ethereum address`);
      await onend();
    }

  return [mobile_account, mobile_wallet, mobile_logo];

}

async function getdidauthn(){
  if (!provider) {
  //  throw new Error(`provider hasn't been created yet`);
  }
  return await did_authn(provider.accounts[0], provider, web3);
  }

async function isconnected() {
  console.log('provider = ', provider);
  if (provider.connected)
  { return true}
  else {return false;}
}


async function getaccountaddress(){
  /*
  This is the standard init call of a page
  */
 if (!provider) {
  //  throw new Error(`provider hasn't been created yet`);
  document.getElementById("connected").innerHTML = wc_off;
    }
  else {
    document.getElementById("connected").innerHTML = wc_on;
  }

  provider = new WalletConnectProvider({
    rpc: {
      1 : "https://talao.co/rpc",
    },
    qrcode: false,
  });
  // init provider
  await provider.enable();
  // create web3 object for future use
  onSubscribe();
  web3 = new Web3(provider);

  onSubscribe();
  
  console.log('provider = ', provider);
  console.log('address = ', provider.accounts[0]);
  console.log('crypto = ', crypto);
  document.getElementById("connected").innerHTML = wc_on;
  return [ provider.accounts[0], provider.wc._peerMeta['name'], provider.wc._peerMeta['icons'][0]];
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

async function create_workspace_keys (){
  const signature = await sign_message('Identity Signature', provider);
  return createworkspacekeys(signature);
  }

function signmessage(msg){
  return sign_message(msg, provider);
}

window.onEnd = onend;
window.onInit = onlogin;
window.sign = signmessage;
window.getDidAuthn = getdidauthn;
window.getAccountAddress = getaccountaddress;
window.checkSignature= checksignature;
window.createWorkspaceKeys=create_workspace_keys;
window.isConnected=isconnected;
