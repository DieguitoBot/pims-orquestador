"""Puente local del grupo: operaciones permitidas + token; nunca publica Ollama/SQL."""
import os
import secrets
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response

load_dotenv(Path(__file__).resolve().parents[1]/'.env.grupo',override=False)
app=FastAPI(title='Puente privado PIMS',docs_url=None,redoc_url=None,openapi_url=None)


def permitido(grupo, method, ruta):
    if method=='GET':
        exactos={
            'riesgos':{'/api/status','/api/documentos'},
            'incidentes':{'/'},
            'terceros':{'/api/estado','/api/proveedores'},
            'evidencias':{'/api/sesion','/api/agente/resumen'},
            'dsar':{'/api/knowledge/status'},
            'consentimientos':{'/api/estado'},
            'privacy_coach':{'/'},
            'soa_studio':{'/api/agent/catalog'},
        }
        if ruta in exactos.get(grupo,set()): return True
        if grupo=='terceros' and ruta.startswith('/api/proveedores/'):
            return ruta.removeprefix('/api/proveedores/').isdigit()
    if method=='POST':
        return ruta in {
            'riesgos':{'/api/evaluar'},'incidentes':{'/api/analizar'},
            'dsar':{'/api/case-analysis'},'consentimientos':{'/api/auditar'},
            'soa_studio':set(),
        }.get(grupo,set())
    return False


@app.get('/health')
def health():
    return {'puente':'pims','agente':os.getenv('PIMS_GROUP_AGENT'),'estado':'activo','nota':'No comprueba el agente nativo.'}


@app.api_route('/{ruta:path}',methods=['GET','POST','PUT','DELETE','PATCH'])
async def reenviar(ruta:str, request:Request):
    token=os.getenv('PIMS_GROUP_TOKEN','')
    enviado=request.headers.get('authorization','')
    if not token or not secrets.compare_digest(enviado.encode(),('Bearer '+token).encode()):
        raise HTTPException(401,'Clave del puente incorrecta o ausente.')
    grupo=os.getenv('PIMS_GROUP_AGENT','');path='/'+ruta
    if not permitido(grupo,request.method,path):
        raise HTTPException(403,'Esta operación no está habilitada para la orquestación.')
    target=os.getenv('PIMS_GROUP_TARGET','').rstrip('/')
    try:
        parsed=urlsplit(target)
        if parsed.scheme!='http' or parsed.hostname not in ('127.0.0.1','localhost','::1') or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment:
            raise ValueError()
    except ValueError:
        raise HTTPException(503,'El puente debe apuntar al agente en localhost, sin ruta ni credenciales.')
    payload=b''
    async for chunk in request.stream():
        payload+=chunk
        if len(payload)>65536: raise HTTPException(413,'Solicitud demasiado grande para este puente.')
    headers={}
    if payload: headers['Content-Type']=request.headers.get('content-type','application/json')
    # No se reenvía al agente nativo la clave del puente.
    if os.getenv('PIMS_UPSTREAM_API_KEY'): headers['X-API-Key']=os.environ['PIMS_UPSTREAM_API_KEY']
    if os.getenv('PIMS_UPSTREAM_BEARER'): headers['Authorization']='Bearer '+os.environ['PIMS_UPSTREAM_BEARER']
    try:
        async with httpx.AsyncClient(timeout=300,follow_redirects=False) as client:
            if grupo=='evidencias':
                usuario,clave=os.getenv('PIMS_EVIDENCIAS_USUARIO'),os.getenv('PIMS_EVIDENCIAS_CLAVE')
                if usuario and clave:
                    login=await client.post(target+'/login',data={'usuario':usuario,'clave':clave})
                    if login.status_code not in (302,303):
                        raise HTTPException(502,'Revisa el acceso de servicio a Evidencias en el equipo del grupo.')
            r=await client.request(request.method,target+path,content=payload,headers=headers)
            if len(r.content)>2_000_000: raise HTTPException(502,'La respuesta supera el límite del puente.')
            return Response(r.content,status_code=r.status_code,media_type=r.headers.get('content-type','application/json'),headers={'Cache-Control':'no-store'})
    except httpx.RequestError:
        raise HTTPException(502,'El agente nativo no responde. Su grupo debe iniciarlo en el puerto configurado.')
