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

  provider.on("close", () => {
    console.log('appel de on close, provider is disconected')
    });

  mobile_account = provider.accounts[0];
  mobile_wallet = provider.wc._peerMeta['name'];
  mobile_icon = provider.wc._peerMeta['icons'][0];
  return [mobile_account, mobile_wallet, mobile_icon ];
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

window.onEnd = onend;
window.onInit = onlogin;
window.signPersonalMessage = mypersonalmessage;
window.getAccountAddress = getaccountaddress;

