
const NodeRSA = require('node-rsa')
const cryptico = require('cryptico-js');
const CryptoJS = require('crypto-js');


function generateAes(){
    return CryptoJS.lib.WordArray.random(16);
}

export function generateRsa(seed) {
    // we only use cryptico to generate deterministic RSA 
    const RSAkey = cryptico.generateRSAKey(seed, 2048);
    const _private = JSON.stringify(RSAkey.toJSON());
    const private = JSON.parse(_private);
    const key = new NodeRSA();
    key.importKey({
        n: Buffer.from(private.n, 'hex'),
        e: 65537,
        d: Buffer.from(private.d, 'hex'),
        p: Buffer.from(private.p, 'hex'),
        q: Buffer.from(private.q, 'hex'),
        dmp1: Buffer.from(private.dmp1, 'hex'),
        dmq1: Buffer.from(private.dmq1, 'hex'),
        coeff: Buffer.from(private.coeff, 'hex')
        }, 'components');

    return [key.exportKey('private'), key.exportKey('public')];
    }

export function getKeys(seed) {
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