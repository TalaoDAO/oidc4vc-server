//import Web3 from "web3";
import WalletConnectProvider from "@walletconnect/web3-provider";

var QRCode = require('qrcode')
var canvas = document.getElementById('canvas')

const Talao_Token_ABI=[{"constant":true,"inputs":[{"name":"freelance","type":"address"},{"name":"user","type":"address"}],"name":"hasVaultAccess","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"mintingFinished","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"newagent","type":"address"},{"name":"newplan","type":"uint256"}],"name":"agentApproval","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_from","type":"address"},{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transferFrom","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"newdeposit","type":"uint256"}],"name":"setVaultDeposit","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"freelance","type":"address"}],"name":"getFreelanceAgent","outputs":[{"name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"","type":"address"},{"name":"","type":"address"}],"name":"accessAllowance","outputs":[{"name":"clientAgreement","type":"bool"},{"name":"clientDate","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"ethers","type":"uint256"}],"name":"withdrawEther","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"_to","type":"address"},{"name":"_amount","type":"uint256"}],"name":"mint","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[],"name":"closeVaultAccess","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"tokens","type":"uint256"}],"name":"withdrawTalao","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_subtractedValue","type":"uint256"}],"name":"decreaseApproval","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"theMarketplace","type":"address"}],"name":"setMarketplace","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"price","type":"uint256"}],"name":"createVaultAccess","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[],"name":"finishMinting","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"owner","outputs":[{"name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[{"name":"result","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"marketplace","outputs":[{"name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"","type":"address"}],"name":"data","outputs":[{"name":"accessPrice","type":"uint256"},{"name":"appointedAgent","type":"address"},{"name":"sharingPlan","type":"uint256"},{"name":"userDeposit","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"vaultDeposit","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"},{"name":"_extraData","type":"bytes"}],"name":"approveAndCall","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_addedValue","type":"uint256"}],"name":"increaseApproval","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"newOwner","type":"address"}],"name":"transferOwnership","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"totalDeposit","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"freelance","type":"address"}],"name":"getVaultAccess","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"anonymous":false,"inputs":[{"indexed":true,"name":"client","type":"address"},{"indexed":true,"name":"freelance","type":"address"},{"indexed":false,"name":"status","type":"uint8"}],"name":"Vault","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"to","type":"address"},{"indexed":false,"name":"amount","type":"uint256"}],"name":"Mint","type":"event"},{"anonymous":false,"inputs":[],"name":"MintFinished","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"previousOwner","type":"address"},{"indexed":true,"name":"newOwner","type":"address"}],"name":"OwnershipTransferred","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"owner","type":"address"},{"indexed":true,"name":"spender","type":"address"},{"indexed":false,"name":"value","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"from","type":"address"},{"indexed":true,"name":"to","type":"address"},{"indexed":false,"name":"value","type":"uint256"}],"name":"Transfer","type":"event"}]
const token_address = '0x6F4148395c94a455dc224A56A6623dEC2395b99B';

//let web3 = null;
let provider = null;
//let contract = null;



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
    window.location = "/wc_login/?value=" + value;
    });


  // create web3 object
  //web3 = new Web3(provider);
  //contract = new web3.eth.Contract(Talao_Token_ABI, token_address);


  /*
  // get block number and display on console
  web3.eth.getBlockNumber().then(value => {
  console.log('block Number = ', value);
    });
*/

/*
  // at login if connected go to confirm mobile account
    web3.eth.getAccounts().then(account => {console.log(account);
      if (provider){
        window.location.href = "/wc_login/";
        }
      //document.getElementById("id_address").value = account[0];
   }, reason => {
    console.log("error Block Number =", reason);
   });
*/

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
    // Create a provider
    provider = new WalletConnectProvider({
      rpc: {
        1 : "https://talao.co/rpc",
      },
      qrcode : false,
    });
  // init
  await provider.enable();
  }
  provider.disconnect();
}

/*
  async function sendtoken(receiver) {
  contract.methods.transfer(receiver, '100000000000000000000').send({from: myaccount})
  .once('transactionHash', hash => { console.log(hash);
  })
  .once('receipt', receipt => {console.log(receipt);
  })
  .catch(e => {console.log(e);
  });
} */

/*
async function createvaultaccess() {
  contract.methods.createVaultAccess('0').send({from: myaccount})
  .once('transactionHash', hash => { console.log(hash);
  })
  .once('receipt', receipt => {console.log(receipt);
  })
  .catch(e => {console.log(e);
  });
}
*/

/*
async function signtransaction()  {
  if (!provider) {
    throw new Error(`provider hasn't been created yet`);
  }}


  // sign message
//       web3.eth.sign('test', myaccount, (err, sig) => {
 //      console.log(err, sig)
 //       })

/* ok
const tx =  web3.eth.sendTransaction({to:'0x3535353535353535353535353535353535353535', from:myaccount, value:'1000'});
console.log(tx);
*/

/* ok
web3.eth.sendTransaction({
    from: myaccount,
    gasPrice: "20000000000",
    gas: "21000",
    to: '0x3535353535353535353535353535353535353535',
    value: "100",
    data: ""
});
*/


/*
function mypersonalmessage(msg) {
  if (!provider) {
    throw new Error(`provider hasn't been created yet`);
  }
  // send personal_sign request
  provider
    .send({ method: "personal_sign", params: [msg, provider.accounts[0]] })
    .then(result => {
      // Returns message signature
      console.log(result); // eslint-disable-line
    })
    .catch(error => {
      // Error returned when rejected
      console.error(error); // eslint-disable-line
    });
} */

//window.sendToken = sendtoken;
//window.createVaultAccess = createvaultaccess;
//window.signTransaction = signtransaction;
window.onEnd = onend;
window.onInit = oninit;
//window.signPersonalMessage = mypersonalmessage;
window.getAccountAddress = getaccountaddress;

