import  {foundation_abi, workspace_contract_abi, talao_token_abi} from "./constant.js";
import {generateRsa, aesDecrypt, rsaDecrypt, rsaEncrypt} from "./talao_encryption.js";

const foundation_contract = "0xb4C784Bda6A994f9879b791Ee2A243Aa47fDabb6";
const talao_token_contract = "0x6F4148395c94a455dc224A56A6623dEC2395b99B";

export async function ownerstocontracts(address,web3) {
    const contract = new web3.eth.Contract(foundation_abi, foundation_contract);
    const workspace_contract = await contract.methods.ownersToContracts(address).call();
    return workspace_contract;
    }

export async function contractstoowners(workspace_contract,web3) {
    const contract = new web3.eth.Contract(foundation_abi, foundation_contract);
    const address = await contract.methods.ownersToContracts(workspace_contract).call();
    return address;
    }

/*
This is the CreateVaultAccess of the token
*/
export async function create_vault_access(account, web3) {
  const contract = new web3.eth.Contract(talao_token_abi, talao_token_contract);
  const access = await contract.methods.hasVaultAccess(account, account).call();
  if (!access){
    await contract.methods.createVaultAccess("0").send({from: account, gas : "200000"})
    .once('sent', payload => { console.log('transaction sent = ', payload);
    })
    .once('receipt', receipt => {console.log('receipt = ',receipt);
    })
    .on('error', error => {console.log('error =', error);
    });
  }
}

export async function transfer_to(account_from, account_to, value, web3) {
  const contract = new web3.eth.Contract(talao_token_abi, talao_token_contract);
  await contract.methods.transfer(account_to, value).send({from: account_from, gas : "50000"})
  .once('sent', payload => { console.log('transaction sent = ',payload);
    })
  .on('error', error => {console.log('error = ', error);
    })
  .then(receipt => {console.log('receipt = ',receipt);
    });
  }

export async function destroy_workspace(address,web3){
  const workspace_contract = await ownerstocontracts(address, web3);
  const contract = new web3.eth.Contract(workspace_contract_abi, workspace_contract);
  await contract.methods.destroyWorkspace().send({from: address, gas : "200000"})
  .once('sent', payload => { console.log('transaction sent = ',payload);
    })
  .on('error', error => {console.log('error = ', error);
    })
  .then(receipt => {console.log('receipt = ',receipt);
    });
  }

export async function read_public_rsa(workspace_contract,web3){
  const contract = new web3.eth.Contract(workspace_contract_abi, workspace_contract);
  let result = null;
  await contract.methods.identityInformation().call()
  .then(data=>{
    result =  Buffer.from(data[4].substr(2),"hex").toString();
  });
  return result;
  }


/*
 Basic GET request JS client side
*/
let HttpClient = function() {
        this.get = function(aUrl, aCallback) {
            const anHttpRequest = new XMLHttpRequest();
            anHttpRequest.onreadystatechange = function() {
                if (anHttpRequest.readyState == 4 && anHttpRequest.status == 200)
                    aCallback(anHttpRequest.responseText);
            }
            anHttpRequest.open( "GET", aUrl, true );
            anHttpRequest.send( null );
        }
    }


/*
This function read the AES private key of an Identity then derive the rsa private key from the signature
and decrypt it. It returns the AES private key and the workspace contract
*/
export async function get_aes_private_key(address, provider, web3){
       const workspace_contract = await ownerstocontracts(address, web3);
       const contract = new web3.eth.Contract(workspace_contract_abi, workspace_contract);
       // derive private RSA key from wallet signature of 'Identity Signature'
       const signature = await sign_message('Identity Signature', provider);
       const keys = await generateRsa(signature);
       const private_rsa_key = keys[0];
       // get private AES key encrypted on workspace
       let aes_private_key_encrypted = null;
       await contract.methods.identityInformation().call()
       .then(data=>{aes_private_key_encrypted =  data[5];});
       // decrypt private AES key with RSA private key
       const aes_private_key = rsaDecrypt(aes_private_key_encrypted, private_rsa_key);
       return [aes_private_key, workspace_contract];
  }

  /* 
  Read the AES private key of the Identity owner with walletr and encrypt it with 
  the rsa key of another Identity
  */
export async function get_aes_private_key_encrypted(provider, web3, workspace_contract_to){
  // read aes private key on the workspace of the identity
  const result  = await get_aes_private_key(provider.accounts[0], provider, web3);
  // read the publice provate key of the client Identity for OpenId Connect flow
  const rsa_public_key = await read_public_rsa(workspace_contract_to, web3);
  // encrypt the aes private key of the Identity with the public RSA key of the client
  const aes_private_key_encrypted =  rsaEncrypt(result[0].toString(), rsa_public_key);
  return [aes_private_key_encrypted, result[1]];
  }

  /*
  Downloads the did auth of the Identity wallet and encrypt it with the Client rsa key
  */
export async function get_did_authn_encryted_for_other(provider, web3, workspace_contract_to){
  const did_authn = await did_authn(provider,web3);
  const rsa_public_key = await read_public_rsa(workspace_contract_to, web3);
  return rsaEncrypt(did_authn, rsa_public_key);
  }


  /*
  Download the did_authn of the Identity wallet, decrypt it and
  returns it plain text
  */
export  async function did_authn(provider,web3){
    const address = provider.accounts[0];
    const workspace_contract = await ownerstocontracts(address, web3);
    const contract = new web3.eth.Contract(workspace_contract_abi, workspace_contract);
    // look for the list of ERC725 Claims with topic = did auth
    const claim_list = await contract.methods.getClaimIdsByTopic('100105100095097117116104110').call();
    // look for the last ERC725 claim of the list
    const claim = await contract.methods.getClaim(claim_list.slice(-1)[0]).call();
    // download cipher text from IPFS data of the claim
    const client = new HttpClient();
    let ciphertext = null;
    let uri = 'https://gateway.pinata.cloud/ipfs/' + claim.uri;
      client.get(uri, function(response) {
      ciphertext = JSON.parse(response).ciphertext;
      });
    // derive private RSA key from wallet signature of 'Identity Signature'
    const signature = await sign_message('Identity Signature', provider);
    const keys = await generateRsa(signature);
    const private_rsa_key = keys[0];
    // get private AES key encrypted on workspace
    let aes_private_key_encrypted = null;
    await contract.methods.identityInformation().call()
      .then(data=>{aes_private_key_encrypted =  data[5];});
    // decrypt private AES key with RSA private key
    const aes_private_key = rsaDecrypt(aes_private_key_encrypted, private_rsa_key);
    // decrypt claim cipher text with AES key
    return aesDecrypt(ciphertext, aes_private_key.toString());
    }

/*
Basic ethereum sign method
*/
export async function sign_message(msg, provider){
    let signature = null;
    if (!provider) {
      throw new Error(`provider hasn't been created yet`);
    }
    // send personal_sign request
    await provider
      .send({ method: "personal_sign", params: [msg, provider.accounts[0]] })
      .then(result => {
        // return signature
        signature = result;
      })
      .catch(error => {
        // Error returned when rejected
        console.error(error); // eslint-disable-line
      });
    return signature;
}