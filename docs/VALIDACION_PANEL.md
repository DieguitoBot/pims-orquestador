# Validación del panel central — 09/11/2026

- 12 pruebas Python aprobadas: API existente, recursos del panel, contratos,
  catálogo sin secretos, comprobación GET de conectividad, flujos y fallos.
- Prueba DOM con jsdom aprobada: ocho tarjetas y ocho entradas del plan,
  navegación, formulario de Riesgos, contrato `descripcion_evento` de Incidentes,
  flujo secuencial, errores, modal, descarga habilitada y bloqueo de envíos duplicados.
- Se verifica que contenido como `<img ... onerror=...>` de una respuesta se
  presente como texto y no se interprete como HTML.
- JavaScript y diff sin errores de sintaxis/espacios.

Estas pruebas usan respuestas simuladas. No se volvió a contactar a las
computadoras de los grupos ni se inició un modelo de Ollama desde este entorno.
La ejecución real individual de Riesgos fue comprobada previamente por el usuario
con el orquestador; eso no acredita todavía la integración de los otros siete.

El entorno impidió iniciar Chromium, por lo que queda pendiente la inspección
visual real en Firefox, tanto en escritorio como en móvil. Las pruebas DOM
verifican interacciones, no renderizado o dimensiones de la página.

## Prueba de aceptación en Ubuntu

1. Conservar `.env` y dejar V3 activo en 8180.
2. Iniciar el orquestador y abrir `http://127.0.0.1:9000/`.
3. Comprobar conexiones: Riesgos debe mostrar HTTP responde; los seis adaptadores
   pendientes deben seguir mostrando Por integrar.
4. Nueva solicitud → Riesgos → ejemplo ficticio → Ejecutar. Verificar reporte,
   identificador guardado y consulta del historial desde el enlace de V3.
5. Descargar JSON y texto. Abrir las descargas y contrastarlas con la respuesta.
6. Con Incidentes apagado/no configurado, ejecutar su flujo y comprobar que no
   aparece un resultado de Riesgos inventado.
7. Revisar panel, formulario y modal con teclado y a 390 px de ancho.


## Rediseño editorial

Se reemplaza la barra lateral por cabecera y navegación horizontal. El directorio
usa filas en vez de tarjetas; la paleta es papel, carbón y rojo óxido. Newsreader
y Public Sans se sirven localmente, junto con sus licencias. El rediseño conserva
los identificadores DOM y los contratos del panel, y pasó nuevamente las mismas
12 pruebas Python y las pruebas DOM. No hay cambios de base de datos ni APIs.
