import json
import ns
from protocol import document




def get_names(mode):
    usernameslist = ns.identity_list(mode)
    idlist = []
    for username in usernameslist:
        idlist.append(ns.get_data_from_username(username, mode))

    profillist = []
    for id in idlist:
        name = document.read_profil(id['workspace_contract'], mode, "fast")
        if name[1] == 1001:
            profil = {"username" : id["username"], "name" : name[0]['firstname'] + " " + name[0]['lastname']}
        else:
            profil = {"username" : id["username"], "name" : name[0]['name']}
        profillist.append(profil)

    print(profillist)
    with open('./static/username.json', 'w') as outfile:
        json.dump(profillist, outfile)
