import json
import ns
from protocol import document


def update_user(session, bool):
    username = session['username']
    name = session['name']
    profillist = []
    with open('./static/username.json', 'r') as json_file:
        data = json.load(json_file)
        for id in data:
            if id['username'] != username:
                profillist.append(id)

    if bool:
        profillist.append({"username" : username, "name" : name})

    with open('./static/username.json', 'w') as outfile:
        json.dump(profillist, outfile)

def add_user(session, name, username):
    profillist = []
    with open('./static/username.json', 'r') as json_file:
        data = json.load(json_file)
        for id in data:
            if id['username'] != username:
                profillist.append(id)

    if bool:
        profillist.append({"username" : username, "name" : name})

    with open('./static/username.json', 'w') as outfile:
        json.dump(profillist, outfile)

def search_user(session):
    username = session['username']
    name = session['name']
    profillist = []
    with open('./static/username.json', 'r') as json_file:
        data = json.load(json_file)
        for id in data:
            if id['username'] == username:
                return True
    return False

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
