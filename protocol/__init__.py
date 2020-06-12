
from .identity import Identity

from .Talao_token_transaction import destroyWorkspace, createVaultAccess
from .Talao_token_transaction import updateSelfclaims
from .Talao_token_transaction import contractsToOwners, isdid, token_balance
from .Talao_token_transaction import partnershiprequest, authorizepartnership, remove_partnership
from .Talao_token_transaction import ownersToContracts, createWorkspace, save_image, get_image
from .Talao_token_transaction import token_transfer, createVaultAccess, ether_transfer, read_workspace_info

from .nameservice import addName, deleteName,  getUsername,updateName
from .nameservice import namehash, load_register_from_file, workspaceFromPublickeyhex, data_from_publickey, username_and_email_list, username_to_data

from .key import add_key, delete_key, has_key_purpose

from .document import Document, read_profil

from .claim import Claim

from .file import File
