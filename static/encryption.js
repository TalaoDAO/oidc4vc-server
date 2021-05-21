// Talao copyright


async function getKeyMaterial(password) {
  const password_buffer = str2ab(password);
  return window.crypto.subtle.importKey(
    "raw",
    password_buffer,
    {name: "PBKDF2"},
    false,
    ["deriveBits", "deriveKey"]
  );
}


async function Decode(ciphertext, password){
  const keyMaterial = await getKeyMaterial(password);
  salt = str2ab("123456789ABCDEF");
  const encryptingKey = await getKey(keyMaterial, salt);
  const encoded = base64ToArrayBuffer(ciphertext);
  const iv = str2ab("1000");
  var result;
  await window.crypto.subtle.decrypt(
            {
              name: "AES-GCM",
              iv: iv
            },
            encryptingKey,
            encoded
            )
            .then(
              (decrypted) => {
                const textdecrypted = ab2str(decrypted);
                result = textdecrypted;
                })
            .catch((e) => {result = "error";});
    return result;
}


async function Encode(text, password){
    const keyMaterial = await getKeyMaterial(password);
    const salt = str2ab("123456789ABCDEF");
    const encryptingKey = await getKey(keyMaterial, salt);
    const encoded = str2ab(text);
    const iv = str2ab("1000")
    const encrypted = await window.crypto.subtle.encrypt(
        {
            name: "AES-GCM",
            iv: iv
        },
        encryptingKey,
        encoded
        );
    return  arrayBufferToBase64(encrypted);
    }


// helper
function ab2str(buf) {
  return String.fromCharCode.apply(null, new Uint16Array(buf));
}


// helper
function str2ab(str) {
  var buf = new ArrayBuffer(str.length*2); // 2 bytes for each char
  var bufView = new Uint16Array(buf);
  for (var i=0, strLen=str.length; i < strLen; i++) {
    bufView[i] = str.charCodeAt(i);
  }
  return buf;
}


async function getKey(keyMaterial, salt) {
    return window.crypto.subtle.deriveKey(
      {
        "name": "PBKDF2",
        salt: salt,
        "iterations": 100000,
        "hash": "SHA-256"
      },
      keyMaterial,
      { "name": "AES-GCM", "length": 256},
      true,
      [ "encrypt", "decrypt" ]
    );
  }


function arrayBufferToBase64( buffer ) {
    var binary = '';
    var bytes = new Uint8Array( buffer );
    var len = bytes.byteLength;
    for (var i = 0; i < len; i++) {
        binary += String.fromCharCode( bytes[ i ] );
    }
    return window.btoa( binary );
}


function base64ToArrayBuffer(base64) {
    var binary_string =  window.atob(base64);
    var len = binary_string.length;
    var bytes = new Uint8Array( len );
    for (var i = 0; i < len; i++)        {
        bytes[i] = binary_string.charCodeAt(i);
    }
    return bytes.buffer;
}