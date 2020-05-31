
from .identity import Identity
from .data import Data

from .Talao_token_transaction import destroyWorkspace, ether_transfer, token_transfer, createVaultAccess
from .Talao_token_transaction import addclaim, readProfil, updateSelfclaims
from .Talao_token_transaction import contractsToOwners, isdid, deleteDocument, deleteClaim, createDocument
from .Talao_token_transaction import partnershiprequest, authorizepartnership, remove_partnership
from .Talao_token_transaction import ownersToContracts, createWorkspace, savepictureProfile, getpicture
from .Talao_token_transaction import token_transfer, createVaultAccess, ether_transfer, getPrivatekey

from .nameservice import addName, address, deleteName,  getUsername,updateName
from .nameservice import namehash, load_register_from_file, canRegister_email, workspaceFromPublickeyhex, data_from_publickey, username_and_email_list, username_to_data

from .GETresolver import getresolver

from .ADDdocument import getdocument, createdocument

from .GETresume import getresume, getlanguage, setlanguage, getexperience,  get_education, get_certificate

from .GETdata import getdata

from .ADDcertificate import addcertificate

from .ADDkey import addkey, delete_key

from .document import Education, Experience, read_profil

from .claim import Claim

from .file import File
