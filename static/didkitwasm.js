import initDIDKit, * as DIDKit from './didkit_wasm.js';

async function init_didkit() {
await initDIDKit("./../../static/didkit_wasm_bg.wasm");

	const version = DIDKit.getVersion();
    console.log('didkit version : ', version)
}
init_didkit();

window.DIDKit = DIDKit;
