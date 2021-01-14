import WalletConnectProvider from "@walletconnect/web3-provider";

var QRCode = require('qrcode')
var canvas = document.getElementById('canvas')

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
    console.log('wallet closed ');
  });
}


async function oninit(mobile) {
  console.log('provider debut oninit = ', provider)
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
    QRCode.toCanvas(canvas, uri, function (error) {
      if (error) {console.error(error);
      }
      else 
        {console.log('connexion success !');
        console.log('provider = ',provider);}
        })
    });
  }

  onSubscribe();

  provider.enable()
  .catch(e => {
    console.log(e);
    })
  .then(value => {
    console.log('provider = ',value);
    window.location = "/wc_login/?wallet_address=" + value;
    });

}

async function getaccountaddress(){
  let mobile_account = '';
  let mobile_wallet ='';
  let mobile_icon = '';

  provider = new WalletConnectProvider({
    rpc: {
      1 : "https://talao.co/rpc",
    },
    qrcode: false,
  });

  // init
  await provider.enable();
  console.log('call de getaccount, provider = ', provider);

  mobile_account = provider.accounts[0];
  mobile_wallet = provider.wc._peerMeta['name'];
  mobile_icon = provider.wc._peerMeta['icons'][0];
  return [mobile_account, mobile_wallet, mobile_icon ];
  }


async function onend() {
  console.log('call de onend ', provider);
  if (!provider) {
    provider = new WalletConnectProvider({
      rpc: {
        1 : "https://talao.co/rpc",
      },
      qrcode : false,
    });
  // init
  await provider.enable();
  }
  await provider.disconnect();
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
      console.log('signature = ',result); // eslint-disable-line
      // check signature here
      signature = result;
    })
    .catch(error => {
      // Error returned when rejected
      console.error(error); // eslint-disable-line
    });
  return signature;
}

window.onEnd = onend;
window.onInit = oninit;
window.sign = mypersonalmessage;
window.getAccountAddress = getaccountaddress;
