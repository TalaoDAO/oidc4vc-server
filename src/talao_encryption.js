
const NodeRSA = require('node-rsa')
const cryptico = require('cryptico-js');
const CryptoJS = require('crypto-js');



function rsaEncrypt (aes_key, public_rsa_key) {
    const key = new NodeRSA();
    const rsa_key = key.importKey(public_rsa_key);
    return rsa_key.encrypt(aes_key);
  }
  
  function rsaDecrypt (aes_encrypted, private_rsa_key){
    const rsa_key = new NodeRSA(private_rsa_key);
    const key_encrypted = aes_encrypted.substr(2)
    const key_buffer = Buffer.from(key_encrypted, 'hex')
    return rsa_key.decrypt(key_buffer).toString('hex');
  }

function generateAes(){
    return CryptoJS.lib.WordArray.random(16);
}

export function generateRsa(seed) {
    // we only use cryptico to generate deterministic RSA 
    const RSAkey = cryptico.generateRSAKey(seed, 2048);
    const _priv = JSON.stringify(RSAkey.toJSON());
    const priv = JSON.parse(_priv);
    const key = new NodeRSA();
    key.importKey({
        n: Buffer.from(priv.n, 'hex'),
        e: 65537,
        d: Buffer.from(priv.d, 'hex'),
        p: Buffer.from(priv.p, 'hex'),
        q: Buffer.from(priv.q, 'hex'),
        dmp1: Buffer.from(priv.dmp1, 'hex'),
        dmq1: Buffer.from(priv.dmq1, 'hex'),
        coeff: Buffer.from(priv.coeff, 'hex')
        }, 'components');

    return [key.exportKey('private'), key.exportKey('public')];
    }

function getKeys(seed) {
    rsa =  generateRsa(seed);
    return [rsa[0], rsa[1], generateAes("private_key_____"), generateAes("secret_key______")];
    }

export  function aesEncrypt(message, password){
    // password (public, private or secret keys) is 16 octets
    // mesage is str
    // return is str
    let bytes = CryptoJS.PBKDF2(password, 'salt', { keySize: 128, iterations: 128 });
    let iv = CryptoJS.enc.Hex.parse(bytes.toString().slice(0, 32));
    let key = CryptoJS.enc.Hex.parse(bytes.toString().slice(32, 96));
    let ciphertext = CryptoJS.AES.encrypt(message, key, { iv: iv });
    return ciphertext.toString()
  }

export  function aesDecrypt(encrypted, password){
    let bytes = CryptoJS.PBKDF2(password, 'salt', { keySize: 128, iterations: 128 });
    let iv = CryptoJS.enc.Hex.parse(bytes.toString().slice(0, 32));
    let key = CryptoJS.enc.Hex.parse(bytes.toString().slice(32, 96));
    let decr = CryptoJS.AES.decrypt(encrypted, key,{ iv: iv });
    let decrypted = decr.toString(CryptoJS.enc.Utf8);
    return decrypted;
  }

 export  async function read_workspace_info(did) {
    const buffer = fs.readFileSync("./RSA_key/talaonet/" + did + ".pem");
    let result = null;
    await contract.methods.identityInformation().call()
    .then(data=>{
      result =  data;
    });
    return [result[1], rsaDecrypt(result[5], buffer.toString()), rsaDecrypt(result[6], buffer.toString())];
  }

export function createworkspacekeys(seed, address) {
    const new_key = generateRsa(seed);
    const private_rsa_key = new_key[0]
    const public_rsa_key = new_key[1]
    const _secret = generateAes();
    const _private = generateAes();
    const secret_encrypted = rsaEncrypt (_secret, public_rsa_key).toString('hex');
    const private_encrypted = rsaEncrypt (_private, public_rsa_key).toString('hex');
    return [public_rsa_key, private_encrypted, secret_encrypted, private_rsa_key];
  }