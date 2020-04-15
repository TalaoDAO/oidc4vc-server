
from .identity import identity
from .Data import data

from .Talao_token_transaction import getEmail, destroyWorkspace
from .Talao_token_transaction import addclaim, readProfil, updateSelfclaims
from .Talao_token_transaction import contractsToOwners, isdid, deleteDocument, deleteClaim
from .Talao_token_transaction import partnershiprequest, authorizepartnership
from .Talao_token_transaction import ownersToContracts, createWorkspace
from .Talao_token_transaction import token_transfer, createVaultAccess, ether_transfer, getPrivatekey

from .nameservice import addName, address, deleteName, buildregister, getUsername,updateName
from .nameservice import namehash, load_register_from_file, canRegister_email

from .GETresolver import getresolver

from .ADDdocument import getdocument, createdocument

from .GETresume import getresume

from .GETdata import getdata

from .ADDcertificate import addcertificate
