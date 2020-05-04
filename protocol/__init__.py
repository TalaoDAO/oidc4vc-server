
from .identity import Identity
from .data import Data

from .Talao_token_transaction import getEmail, destroyWorkspace, ether_transfer, token_transfer, createVaultAccess
from .Talao_token_transaction import addclaim, readProfil, updateSelfclaims
from .Talao_token_transaction import contractsToOwners, isdid, deleteDocument, deleteClaim, createDocument
from .Talao_token_transaction import partnershiprequest, authorizepartnership
from .Talao_token_transaction import ownersToContracts, createWorkspace, savepictureProfile, getpicture
from .Talao_token_transaction import token_transfer, createVaultAccess, ether_transfer, getPrivatekey

from .nameservice import addName, address, deleteName, buildregister, getUsername,updateName
from .nameservice import namehash, load_register_from_file, canRegister_email, workspaceFromPublickeyhex

from .GETresolver import getresolver

from .ADDdocument import getdocument, createdocument

from .GETresume import getresume, getlanguage, setlanguage, getexperience, getpersonal, getcontact, get_education

from .GETdata import getdata

from .ADDcertificate import addcertificate

from .ADDkey import addkey
