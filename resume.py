from protocol import Identity

def get(workspace_contract, mode) :
    user = Identity(workspace_contract, mode, authenticated=False)
    # clean up for resume
    resume = user.__dict__.copy()
    del resume['synchronous']
    del resume['authenticated']
    del resume['address']
    del resume['workspace_contract']
    del resume['did']
    del resume['other_list']
    del resume['education_list']
    del resume['experience_list']
    del resume['kbis_list']
    del resume['kyc_list']
    del resume['certificate_list']
    del resume['skills_list']
    del resume['file_list']
    return resume
