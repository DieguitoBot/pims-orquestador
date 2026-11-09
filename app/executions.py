"""Ejecuciones en memoria, con progreso real de cada llamada. Un solo worker."""
import asyncio
import logging
from copy import deepcopy
from time import time
from uuid import uuid4
from .cooperation import coordinar, etapas_iniciales

REGISTRO = {}
TAREAS = set()
MAX_EJECUCIONES = 30
TTL = 3600


def obtener(id_):
    r=REGISTRO.get(id_)
    return deepcopy(r) if r else None


def limpiar():
    for id_,r in list(REGISTRO.items()):
        if r['estado'] not in ('en_curso','en_cola') and time()-r['actualizado']>TTL:
            del REGISTRO[id_]


async def iniciar(data):
    limpiar()
    if len(REGISTRO)>=MAX_EJECUCIONES:
        raise ValueError('Hay 30 ejecuciones conservadas. Espera a que expire su retención (una hora) o reinicia el servicio cuando no haya tareas activas.')
    # Una sola ejecución coordinada a la vez evita saturar los equipos de los grupos.
    if any(r['estado'] in ('en_curso','en_cola') for r in REGISTRO.values()):
        raise ValueError('Hay un flujo coordinado en curso. Espera a que termine antes de iniciar otro.')
    id_=str(uuid4());REGISTRO[id_]={'solicitud_id':id_,'estado':'en_curso','pasos':etapas_iniciales(),'actualizado':time()}
    async def avisar(pasos):
        REGISTRO[id_]['pasos']=deepcopy(pasos);REGISTRO[id_]['actualizado']=time()
    async def correr():
        try:
            resultado=await coordinar(data,notificar=avisar)
            REGISTRO[id_]={**resultado,'solicitud_id':id_,'actualizado':time()}
        except asyncio.CancelledError:
            REGISTRO[id_]['estado']='interrumpido';REGISTRO[id_]['mensaje']='El servidor se detuvo. Revisa el historial de los agentes antes de repetir.'
            raise
        except Exception:
            logging.getLogger(__name__).exception("Fallo al coordinar una ejecución PIMS")
            REGISTRO[id_]['estado']='error';REGISTRO[id_]['mensaje']='Error interno de coordinación. Revisa la terminal y los resultados ya recibidos antes de repetir.'
        finally:
            REGISTRO[id_]['actualizado']=time()
    task=asyncio.create_task(correr());TAREAS.add(task);task.add_done_callback(TAREAS.discard)
    return obtener(id_)


async def cerrar():
    for t in list(TAREAS): t.cancel()
    if TAREAS: await asyncio.gather(*list(TAREAS),return_exceptions=True)
