
from .identity import Identity

from .Talao_token_transaction import destroy_workspace, createVaultAccess,  transfer_workspace, has_vault_access
from .Talao_token_transaction import get_data_from_token, read_profil, get_category, get_keylist
from .Talao_token_transaction import contractsToOwners, token_balance, is_partner, get_partner_status
from .Talao_token_transaction import partnershiprequest, authorize_partnership, remove_partnership, reject_partnership
from .Talao_token_transaction import ownersToContracts, createWorkspace, get_all_credentials
from .Talao_token_transaction import token_transfer, ether_transfer, read_workspace_info, update_self_claims

from .key import add_key, delete_key, has_key_purpose

from .document import Document

from .claim import Claim

from .file import File
