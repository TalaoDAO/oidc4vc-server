import requests

def company(SIREN):
    r = requests.get('https://entreprise.data.gouv.fr/api/sirene/v2/siren/'+SIREN+'')
    json_object = r.json()
    settings = dict()
    if json_object['sirene']['status'] == 404:
        return None
    if json_object['sirene']['data']['siege_social']['nom_raison_sociale'] != None :
        settings['name'] = json_object['sirene']['data']['siege_social']['nom_raison_sociale']
    else :
        settings['name'] = ''
    try :
        settings['address'] = json_object['sirene']['data']['siege_social']['numero_voie'] + ' ' + json_object['sirene']['data']['siege_social']['type_voie'] + ' ' + json_object['sirene']['data']['siege_social']['libelle_voie'] + ' ' + json_object['sirene']['data']['siege_social']['code_postal'] + ' ' + json_object['sirene']['data']['siege_social']['libelle_commune']
    except :
        settings['address'] = ''
    if json_object['sirene']['data']['total_results'] != None :
        settings['group'] = json_object['sirene']['data']['total_results']
    else :
        settings['group'] = ''

    Dictionnaire_effectifs = {'NN': "No staff members", '00': '0', '01': "1-2", '02': "3-5",
                              '03': "6-9", '11': "10-19", '12': "20-49", '21': "50-99", '22': "100-199",
                              '31': "200-249", '32': "250-499", '41': "500-999", '42': "1000-1999",
                              '51': "2000-4999", '52': "5000-9999", '53': "+10 000"}

    if json_object['sirene']['data']['siege_social']['tranche_effectif_salarie'] != None :
        settings['staff'] = Dictionnaire_effectifs[json_object['sirene']['data']['siege_social']['tranche_effectif_salarie']]
    else :
        settings['staff'] = ''
    if json_object['sirene']['data']['siege_social']['libelle_activite_principale_entreprise'] != None :
        settings['activity'] = json_object['sirene']['data']['siege_social']['libelle_activite_principale_entreprise']
    else :
        settings['activity'] = ''

    return settings
