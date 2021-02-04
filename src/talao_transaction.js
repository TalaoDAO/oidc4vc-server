import  {foundation_abi} from "./abi.js";



export async function ownerstocontracts(address,web3) {
    const foundation_contract = "0xb4C784Bda6A994f9879b791Ee2A243Aa47fDabb6";
    const contract = new web3.eth.Contract(foundation_abi, foundation_contract);
    const workspace_contract = await contract.methods.ownersToContracts(address).call();
    console.log('workspace contract =', workspace_contract);
    return workspace_contract;
    }


export async function contractstoowners(workspace_contract,web3) {
    const foundation_contract = "0xb4C784Bda6A994f9879b791Ee2A243Aa47fDabb6";
    const contract = new web3.eth.Contract(foundation_abi, foundation_contract);
    const address = await contract.methods.ownersToContracts(workspace_contract).call();
    console.log('workspace contract =', address);
    return address;
    }

