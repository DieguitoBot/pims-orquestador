"""Diego importa una ficha privada; no necesita las credenciales internas del grupo."""
import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
from dotenv import set_key

VARIABLES={'riesgos':'RIESGOS','incidentes':'INCIDENTES','terceros':'TERCEROS','evidencias':'EVIDENCIAS','dsar':'DSAR','consentimientos':'CONSENTIMIENTOS','privacy_coach':'PRIVACY_COACH','soa_studio':'SOA_STUDIO'}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('ficha',type=Path);args=parser.parse_args()
    d=json.loads(args.ficha.read_text());nombre=VARIABLES.get(d.get('agente'));url=d.get('url','');u=urlsplit(url)
    if not nombre or u.scheme!='https' or not u.hostname or u.username or u.password or u.path not in ('','/') or u.query or u.fragment or not isinstance(d.get('token'),str) or len(d['token'])<20:
        parser.error('Ficha de conexión no válida.')
    archivo=Path(__file__).resolve().parents[1]/'.env'
    if not archivo.exists():
        fd=os.open(archivo,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.close(fd)
    set_key(str(archivo),nombre+'_URL',url.rstrip('/'));set_key(str(archivo),nombre+'_TOKEN',d['token'])
    print('Conexión de '+d['agente']+' guardada. Reinicia el orquestador y comprueba conexiones. No se mostró ni compartió la clave.')


if __name__=='__main__':main()
