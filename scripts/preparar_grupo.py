"""Configura el puente en la laptop de un grupo, sin modificar su agente."""
import argparse
import getpass
import json
import os
from pathlib import Path
import secrets
from urllib.parse import urlsplit
from dotenv import dotenv_values,set_key

RAIZ=Path(__file__).resolve().parents[1]
GRUPOS=('riesgos','incidentes','terceros','evidencias','dsar','consentimientos','privacy_coach','soa_studio')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('agente',choices=GRUPOS,nargs='?')
    parser.add_argument('--puerto',type=int)
    parser.add_argument('--credenciales',action='store_true',help='Pide credenciales internas sin mostrarlas; se quedan en esta laptop')
    parser.add_argument('--url-publicada',help='Exporta la ficha privada para Diego tras publicar con Tailscale')
    args=parser.parse_args();archivo=RAIZ/'.env.grupo'
    if args.agente is None:
        args.agente=dotenv_values(archivo).get('PIMS_GROUP_AGENT') if archivo.exists() else None
    if args.agente not in GRUPOS: parser.error('Indica el agente al preparar la conexión por primera vez.')
    os.umask(0o077)
    if not archivo.exists():
        if args.puerto is None or not 1<=args.puerto<=65535:
            parser.error('Indica --puerto con el puerto local real del agente.')
        fd=os.open(archivo,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w') as f:
            f.write('PIMS_GROUP_AGENT='+args.agente+'\n')
            f.write('PIMS_GROUP_TARGET=http://127.0.0.1:'+str(args.puerto)+'\n')
            f.write('PIMS_GROUP_TOKEN='+secrets.token_urlsafe(32)+'\n')
    config=dotenv_values(archivo)
    if config.get('PIMS_GROUP_AGENT')!=args.agente:
        parser.error('Ya existe un puente para otro agente en esta carpeta; usa otra copia del repositorio.')
    if args.credenciales:
        if args.agente=='evidencias':
            set_key(str(archivo),'PIMS_EVIDENCIAS_USUARIO',input('Usuario de servicio de Evidencias: ').strip())
            set_key(str(archivo),'PIMS_EVIDENCIAS_CLAVE',getpass.getpass('Contraseña (no se muestra): '))
        elif args.agente=='dsar':
            set_key(str(archivo),'PIMS_UPSTREAM_API_KEY',getpass.getpass('Clave X-API-Key del servicio DSAR (no se muestra): '))
        elif args.agente=='soa_studio':
            set_key(str(archivo),'PIMS_UPSTREAM_BEARER',getpass.getpass('JWT de servicio SoA (no se muestra): '))
        else: parser.error('Este agente no tiene credenciales internas configurables en esta utilidad.')
    if args.url_publicada:
        u=urlsplit(args.url_publicada)
        if u.scheme!='https' or not u.hostname or u.username or u.password or u.path not in ('','/') or u.query or u.fragment:
            parser.error('Usa solo la URL HTTPS de Tailscale, sin rutas ni credenciales.')
        config=dotenv_values(archivo)
        ficha=RAIZ/'.conexion-grupo.json'
        fd=os.open(ficha,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
        with os.fdopen(fd,'w') as f:
            json.dump({'agente':args.agente,'url':args.url_publicada.rstrip('/'),'token':config['PIMS_GROUP_TOKEN']},f,indent=2)
        print('Ficha privada creada en .conexion-grupo.json. Entregar solo a Diego por un canal privado; no subir a GitHub.')
    print('Puente configurado. Conserva .env.grupo y arranca uvicorn scripts.puente_grupo:app en 127.0.0.1:9100.')


if __name__=='__main__':main()
