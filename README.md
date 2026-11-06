# Lots y comandes

Aplicación Flask para gestionar productos, existencias, pedidos y documentos. Escucha en el puerto `5017` y utiliza SQLite y LibreOffice para generar documentos.

## Docker Compose

Los dos archivos siguen el mismo esquema: proyecto con nombre, servicio `app`, construcción desde el Dockerfile, variables de entorno explícitas, montaje de datos y reinicio automático.

| Archivo | Entorno | HOME y servicios internos | Datos del anfitrión | Navbar |
| --- | --- | --- | --- | --- |
| `docker-compose.yaml` | Producción | `http://172.16.83.23` | `/home/gencardio/Desktop/apps_db/lots_db` | Azul original |
| `docker-compose-alex.yaml` | Desarrollo | `http://172.16.82.45` | `/home/gencardio/Escriptori/lots_db` | Roja |

El directorio de datos se monta completo en `/lots/DB`: debe contener la base `lots.db`, los documentos y las plantillas del subdirectorio `docs`. `create_host_path: false` impide que una ruta equivocada cree un directorio vacío. Revisa las rutas directamente en el Compose correspondiente; no hace falta un archivo `.env`.

Producción:

```bash
docker compose config --quiet
docker compose up -d --build
```

Desarrollo:

```bash
docker compose -f docker-compose-alex.yaml config --quiet
docker compose -f docker-compose-alex.yaml up -d --build
```

La aplicación estará disponible en `http://localhost:5017` o mediante la IP del anfitrión. Ambos archivos publican el mismo puerto; para ejecutarlos a la vez en una máquina, cambia el puerto del anfitrión en uno de ellos.

Para ver los logs o detener desarrollo, utiliza el mismo archivo:

```bash
docker compose -f docker-compose-alex.yaml logs -f --tail=100
docker compose -f docker-compose-alex.yaml down
```

En producción, utiliza las mismas órdenes sin `-f docker-compose-alex.yaml`. Las bases de datos y los documentos permanecen en el anfitrión al recrear el contenedor.

## Configuración

`config.py` conserva comentadas las configuraciones anteriores y permite estas variables:

| Variable | Uso |
| --- | --- |
| `LOTS_ENV` | `production` (por defecto) o `development` |
| `LOTS_IP_ADDRESS` | URL base de HOME y servicios compartidos, sin puerto |
| `LOTS_DATA_DIR` | Directorio de la base de datos y archivos auxiliares |
| `LOTS_DOCS_DIR` | Directorio de documentos; por defecto, `docs` dentro del directorio de datos |
| `LOTS_DEBUG` | Debug desactivado en producción y activado en desarrollo |

Los dos Compose fijan el perfil y sus rutas. El entorno también determina el color de la navbar. Testing permanece desactivado al arrancar la aplicación.

Para ejecutar desarrollo directamente con Python y las rutas locales:

```bash
python3 -m pip install -r requirements.txt
LOTS_ENV=development python3 lots.py
```

El Dockerfile incluye LibreOffice, necesario para convertir documentos a PDF. Las funciones de autenticación e integración requieren conectividad con los servicios internos configurados. La aplicación conserva la actualización existente de columnas de precios al arrancar sobre una base de datos anterior.

## Fechas de Primers

Selecciona una o dos filas y pulsa el botón azul de actualización de una de ellas. Con un primer, el modal muestra dos fechas obligatorias: `buydate` y `hydrodate`. Con dos primers, muestra `buydate_1`, `hydrodate_1`, `buydate_2` y `hydrodate_2`. Cada par aparece junto al nombre y la secuencia de su primer, en el mismo orden que el array `primers`, con inputs de fecha y etiquetas flotantes.

**Enviar** envía directamente las fechas en formato `YYYY-MM-DD` y el array `primers` (con `id`, `sequence_name` y la secuencia original `sequence`) al endpoint autenticado de Lots `/update_primer_dates`. Las dos fechas de cada primer seleccionado son obligatorias y se validan tanto en el navegador como en el servidor. Lots hace el POST JSON a `http://172.16.83.23:5005/api/primers/update-dates-by-sequence`, con un tiempo de espera de 15 segundos. La conexión desde el servidor evita depender de CORS en el navegador.

El JSON enviado a la API incluye únicamente la secuencia y las dos fechas de cada primer seleccionado. Para el primero se envían `sequence1`, `buydate_sequence1` y `hidrodate_sequence1`. Solo si hay un segundo primer se añaden `sequence2`, `buydate_sequence2` y `hidrodate_sequence2`. La API requiere `hidrodate` con i; el campo interno del modal `hydrodate` se convierte al enviar. Cada secuencia se recoge automáticamente de la tabla y conserva las fechas de su grupo en el modal; no se envían campos de primers no seleccionados. Los únicos campos que debe rellenar el usuario son las dos fechas obligatorias por primer.

Si la API confirma la operación, las filas enviadas se retiran de la tabla actual y de la selección, y se muestra un flash de éxito en la cabecera de Primers. Ante un error HTTP, de conexión o indicado por la API, las filas se conservan y se muestra el motivo en un flash. El modal se cierra al finalizar el envío, tanto si funciona como si falla; Cancel·lar y la cruz también lo cierran. Se bloquean los envíos duplicados mientras hay una petición en curso. Esta acción no modifica el estado de recepción de las compras en la base de datos de Lots.
