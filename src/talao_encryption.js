
const NodeRSA = require('node-rsa')
const cryptico = require('cryptico-js');
const CryptoJS = require('crypto-js');

import {talao_rsa_public_key} from "./constant.js";


export function rsaEncrypt(_clear, public_rsa_key) {
  const key = new NodeRSA();
  const rsa_key = key.importKey(public_rsa_key);
  const encrypted = rsa_key.encrypt(_clear);
  const encryptedHex = encrypted.toString('hex');
  return '0x' + encryptedHex;
}

export function rsaDecrypt(ethereum, private_rsa_key) {
  const rsa_key = new NodeRSA(private_rsa_key);
  const encrypted = ethereum.substr(2);
  const buffer = Buffer.from(encrypted, 'hex');
  return rsa_key.decrypt(buffer);
}

function generateAes(){
  // private and secret key are string in JS but bytes in python (str.encode() or bytes(str, 'utf-8')
  const aes = CryptoJS.lib.WordArray.random(16);
  return aes.toString();
}

export function generateRsa(seed) {
    // we only use cryptico to generate deterministic RSA
    const RSAkey = cryptico.generateRSAKey(seed, 2048);
    const _priv = JSON.stringify(RSAkey.toJSON());
    const priv = JSON.parse(_priv);
    const key = new NodeRSA();
    key.importKey({
        n: Buffer.from(priv.n, 'hex'),
        e: 3,
        d: Buffer.from(priv.d, 'hex'),
        p: Buffer.from(priv.p, 'hex'),
        q: Buffer.from(priv.q, 'hex'),
        dmp1: Buffer.from(priv.dmp1, 'hex'),
        dmq1: Buffer.from(priv.dmq1, 'hex'),
        coeff: Buffer.from(priv.coeff, 'hex')
        }, 'components');
    return [key.exportKey('private'), key.exportKey('public')];
    }

export  function aesEncrypt(message, password){
    // password is str (16 hex) (public, private or secret keys) 
    // message is str
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


export async function createworkspacekeys(seed) {
  // seed is created with a signature
    const new_key = generateRsa(seed);
    const public_rsa_key = new_key[1]
    const _secret = generateAes();
    const _private = generateAes();
    console.log('secret = ', _secret)
    console.log('private = ', _private)
    const secret_encrypted = rsaEncrypt (_secret, public_rsa_key).toString('hex');
    const private_encrypted = rsaEncrypt (_private, public_rsa_key).toString('hex');
    const private_encrypted_with_talao_rsa = rsaEncrypt (_private, talao_rsa_public_key).toString('hex');
    return [public_rsa_key, private_encrypted, secret_encrypted, private_encrypted_with_talao_rsa];
  }