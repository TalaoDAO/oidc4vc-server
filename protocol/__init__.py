
from .identity import Identity

from .Talao_token_transaction import destroy_workspace, createVaultAccess
from .Talao_token_transaction import get_data_from_token, read_profil
from .Talao_token_transaction import contractsToOwners, token_balance, is_partner, get_partner_status
from .Talao_token_transaction import partnershiprequest, authorize_partnership, remove_partnership, reject_partnership
from .Talao_token_transaction import ownersToContracts, createWorkspace, save_image, get_image
from .Talao_token_transaction import token_transfer, ether_transfer, read_workspace_info

from .key import add_key, delete_key, has_key_purpose

from .document import Document

from .claim import Claim

from .file import File
