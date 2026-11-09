# Conectar las máquinas de los ocho grupos al PIMS

Cada grupo mantiene **su agente y recursos en su propia PC**. Diego ejecuta
únicamente el orquestador y su Agente de Riesgos. Los equipos deben estar
encendidos y en la misma red privada durante la demostración.

## Lo que se conecta ahora

El objetivo **Analizar incidente con proveedor** usa cuatro servicios:
Incidentes → Terceros → Evidencias (consulta) → Riesgos. Los tres primeros envían
contexto atribuido a Riesgos. Se reúnen los resultados y pendientes en una sola pantalla.
No se aprueban contratos, registran evidencias ni ejecutan medidas automáticamente.

DSAR, Consentimientos, Privacy Coach y SoA pueden preparar su conexión de red,
pero **todavía no participan en este objetivo**. Publicar su puente no implementa
por sí solo su adaptador de colaboración.

## A. Preparar la red una sola vez

1. Diego crea una red Tailscale e invita a los responsables. Cada compañero acepta
   la invitación con su propia cuenta y elige esa misma red al iniciar sesión.
   No compartir la contraseña de una cuenta. Verificar los límites de usuarios
   del plan antes de reunir a los ocho; no se garantiza un plan gratuito para ese tamaño.
2. Las reglas de acceso deben permitir que el equipo de Diego contacte al puerto
   8443 de las máquinas de los grupos. Si existe una política restrictiva, el
   administrador debe autorizar esas conexiones. No abrir la red indiscriminadamente.
3. En cada Ubuntu, incluido el de Diego:

```bash
curl -fsSL https://tailscale.com/install.sh -o /tmp/pims-instalar-tailscale.sh
sh /tmp/pims-instalar-tailscale.sh
sudo tailscale up
tailscale status
```

En Windows: instalar [Tailscale](https://tailscale.com/download/windows), abrirlo,
iniciar sesión en la red acordada y comprobar en PowerShell:

```powershell
tailscale status
```

Tailscale Serve usa HTTPS y acceso privado a la red; **no usar Funnel**. Si Serve
pide habilitar HTTPS, seguir el enlace de configuración que muestra el comando.
La VPN no instala Ollama ni las bases: cada grupo conserva su configuración.

## B. Cada compañero prepara el puente (una vez)

Mantener el agente original instalado y funcionando como ya lo usa su grupo.
En otra carpeta clonar **solo el conector**; no hay modelos ni bases en esta copia.
Los comandos usan la rama del PR para poder ensayar antes de fusionarlo. Una vez
fusionada, también puede clonarse `main`.

Ubuntu:

```bash
cd ~
git clone --branch feature/flujo-incidente-proveedor --single-branch https://github.com/DieguitoBot/pims-orquestador.git pims-conexion
cd ~/pims-conexion
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Windows (PowerShell):

```powershell
cd $HOME
git clone --branch feature/flujo-incidente-proveedor --single-branch https://github.com/DieguitoBot/pims-orquestador.git pims-conexion
cd pims-conexion
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Comando específico por grupo

Arrancar el **agente nativo** desde su propio repositorio y entorno, no desde
`pims-conexion`. La tabla recoge los arranques documentados; si el grupo ya cambió
su puerto, usar el puerto real en el comando de preparación del puente.

| Grupo / repositorio | Arranque nativo, con dependencias y datos ya preparados | Preparar puente desde `pims-conexion` (Ubuntu) |
|---|---|---|
| Riesgos — `DieguitoBot/agente-riesgos-pims` | Desde `agente_riesgos_pims_v3`: `bash iniciar.sh --port 8180 --sin-navegador` | `.venv/bin/python scripts/preparar_grupo.py riesgos --puerto 8180` |
| Incidentes — `jherson2024/agente_privacidad` | Desde su raíz y entorno: `python app.py` (5000) | `.venv/bin/python scripts/preparar_grupo.py incidentes --puerto 5000` |
| Terceros — `S-kkipie/agente-terceros-dpa` | Desde su raíz: `uv run agente-terceros web` (5000) | `.venv/bin/python scripts/preparar_grupo.py terceros --puerto 5000` |
| Evidencias — `jhuamaniCond/auditoria-agente-tif-2` | Desde `Entregable-2/agente`, con login y PostgreSQL configurados: `python servidor_web.py` (5000) | `.venv/bin/python scripts/preparar_grupo.py evidencias --puerto 5000 --credenciales` |
| DSAR — `JeremyCruzGallegos/agente-dsar-iso27701` | Arranque documentado en Windows, desde su raíz: `docker compose up -d postgres` y luego `py -3.12 iniciar.py --demo` (5000) | `.venv/bin/python scripts/preparar_grupo.py dsar --puerto 5000 --credenciales` |
| Consentimientos — `Dan-Ar5/Auditoria` | Desde su raíz y entorno: `python dashboard.py --conservar --no-abrir` (8765) | `.venv/bin/python scripts/preparar_grupo.py consentimientos --puerto 8765` |
| Privacy Coach — `DrN25/Privacy-Coach-Agent-ISO-27701` | Desde su raíz y entorno: `python src/run.py` (8000) | `.venv/bin/python scripts/preparar_grupo.py privacy_coach --puerto 8000` |
| SoA — `gcarrillov/SOA_estudio_agente_AUDITORIA` | Desde `backend` y su entorno: `uvicorn app.main:app --host 127.0.0.1 --port 8000` | `.venv/bin/python scripts/preparar_grupo.py soa_studio --puerto 8000 --credenciales` |

**En Windows**, sustituir `.venv/bin/python` por `.\.venv\Scripts\python.exe`
en el comando de preparación. Ejemplo exacto para Incidentes:

```powershell
.\.venv\Scripts\python.exe scripts\preparar_grupo.py incidentes --puerto 5000
```

Con `--credenciales`, el programa pregunta sin mostrar la contraseña o clave.
Esas credenciales **se quedan en la laptop del grupo**: Evidencias conserva su
login, DSAR su X-API-Key y SoA su JWT. El JWT de SoA debe renovarse cuando expire.
No desactivar el login de Evidencias para publicar su servicio.

La configuración vive en `.env.grupo`, ignorado por Git. Si ya existe, se conserva;
para preparar otro agente en la misma PC, usar otra copia del conector y otro
puerto de puente/publicación. No reutilizar una ficha de un grupo distinto.

## C. Dejar el puente encendido (cada sesión)

Con el agente nativo ya activo, en una terminal dentro de `pims-conexion`:

Ubuntu:

```bash
.venv/bin/python -m uvicorn scripts.puente_grupo:app --host 127.0.0.1 --port 9100
```

PowerShell:

```powershell
.\.venv\Scripts\python.exe -m uvicorn scripts.puente_grupo:app --host 127.0.0.1 --port 9100
```

El puente escucha únicamente en localhost, exige una clave propia y permite solo
las operaciones específicas del grupo. No expone Ollama, PostgreSQL, pgAdmin,
resets, aprobación de contratos, registro de archivos ni aplicación de parches.
El puente no arranca ni instala el agente nativo.

## D. Publicar el puente en la red privada

En otra terminal de Ubuntu, desde `pims-conexion`:

```bash
sudo tailscale serve status
sudo tailscale serve --bg --https=8443 http://127.0.0.1:9100
sudo tailscale serve status
PIMS_URL_PRIVADA="$(tailscale status --json | .venv/bin/python -c 'import sys,json; print("https://"+json.load(sys.stdin)["Self"]["DNSName"].rstrip(".")+":8443")')"
.venv/bin/python scripts/preparar_grupo.py --url-publicada "$PIMS_URL_PRIVADA"
```

Si el puerto HTTPS 8443 ya sirve otra aplicación, no reemplazarla: acordar otro
puerto antes. No ejecutar `tailscale serve reset` para resolverlo.

En Windows, desde PowerShell en `pims-conexion`:

```powershell
tailscale serve status
tailscale serve --bg --https=8443 http://127.0.0.1:9100
tailscale serve status
$estado = tailscale status --json | ConvertFrom-Json
$url = "https://$($estado.Self.DNSName.TrimEnd('.')):8443"
.\.venv\Scripts\python.exe scripts\preparar_grupo.py --url-publicada $url
```

El programa crea **`.conexion-grupo.json`**, con identificador, URL y clave del
puente. Entregar esa ficha a Diego por un canal privado; no subirla al repositorio
ni publicar su contenido en capturas. No hace falta enviar `.env`, bases o claves
internas del agente.

Para retirar solo esta publicación:

```bash
sudo tailscale serve --https=8443 off
```

En Windows se usa el mismo comando sin `sudo`. No apagar la máquina mientras
Diego esté realizando una prueba.

## E. Diego conecta las fichas recibidas

En su `pims-orquestador`, con entorno activo:

```bash
python scripts/conectar_grupo.py /ruta/privada/ficha-incidentes.json
python scripts/conectar_grupo.py /ruta/privada/ficha-terceros.json
python scripts/conectar_grupo.py /ruta/privada/ficha-evidencias.json
```

Sustituir esas rutas por los archivos realmente recibidos. No renombrar su campo
`agente`. Las claves se guardan en el `.env` local sin mostrarse. También pueden
importarse fichas de los otros grupos, pero sus adaptadores especializados siguen
pendientes y el catálogo lo indica.

Riesgos puede seguir local en tu laptop:

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 9000
```

Antes, conservar `RIESGOS_URL=http://127.0.0.1:8180` en `.env` si tu V3 corre allí.
Reiniciar Uvicorn tras importar fichas. **No usar varios workers**: los flujos en
curso se conservan en memoria del proceso, por un máximo de una hora al finalizar.

## F. Ensayo conjunto

1. Todos mantienen agente nativo + puente + Tailscale activos.
2. Diego abre http://127.0.0.1:9000/ y pulsa **Comprobar conexiones**.
3. Nueva solicitud → **Analizar incidente con proveedor**.
4. Pulsa **Consultar catálogo** y elige el proveedor ficticio acordado con Terceros.
5. Describe un incidente que involucre a ese proveedor; no elegir uno al azar.
6. Ejecuta una sola vez. La pantalla muestra estados reales de las cuatro llamadas.
7. Revisa **Información compartida**, **Acciones pendientes** y el informe integrado.
8. Abre el historial de V3 para verificar el ID de evaluación guardada.

Un informe parcial con Riesgos funcionando no es una prueba de colaboración de
cuatro agentes. Para demostrarla deben responder los cuatro y aparecer tres
intercambios de contexto hacia Riesgos. La cobertura del expediente es general de
UNSA: no equivale a evidencias nuevas registradas para este incidente.

## Fuentes de red

- https://tailscale.com/docs/install/linux
- https://tailscale.com/docs/reference/tailscale-cli/serve
- https://tailscale.com/docs/use-cases/application-testing/share-local-dev-server-with-team

Si todos están en una LAN institucional y no pueden usar Tailscale, acordar con
su administrador una VPN o proxy privado equivalente; no publicar puertos de
bases o modelos directamente. Los comandos de Tailscale no se han ejecutado sobre
las laptops reales: requieren sus cuentas, autorizaciones y permisos de red.
