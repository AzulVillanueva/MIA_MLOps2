> **Ubicación en este repo:** esta carpeta (`tp_integrador/stack/`) es el stack de producción del TP integrador. Todos los comandos de este README se ejecutan desde acá. El contexto general (champion/challenger, API segura, data lake) está en [../README.md](../README.md), y para registrar el champion inicial se puede usar `airflow/register_champion.py` en lugar del notebook (comandos en ese README).
>
> El resto de este archivo es el README original del trabajo final de *Aprendizaje de Máquina II*.

# Aprendizaje de Máquina II

# Trabajo Práctico Final

Integrantes:

- Araujo, Diego
- Charaf, Christopher
- Cid, Maria Fabiana
- Fernández, Gonzalo
- Villanueva, Azul

## Objetivos
**Nivel medio:** Implementar en local usando Metaflow el ciclo de desarrollo del modelo que desarrollaron
en Aprendizaje de Máquina I y generar un archivo para predicción en bache (un csv o un archivo de SQLite). La nota puede
llegar a 10 si implementan una base de datos (ya sea KVS u otro tipo) con los datos de la predicción en bache.

**Nivel alto:** Implementar el modelo que desarrollaron en Aprendizaje de Máquina I en este ambiente
productivo. Para ello, pueden usar los recursos que consideren apropiado. Los servicios disponibles de base son Apache
Airflow, MLflow, PostgresSQL, MinIO, FastAPI. Todo está montado en Docker, por lo que además deben instalado Docker.

## Setup del entorno de trabajo local
Crear entorno virtual de Python para el proyecto:

```bash
python -m venv .venv
```

Activar el entorno virtual:
```bash
source .venv/bin/activate
```

Instalar las dependencias del proyecto:
```bash
pip install -r requirements.txt
```
Descargar el dataset de Kaggle:
```bash
./download_dataset.sh
```

## Levantar servicios con Docker compose

1. Para poder levantar todos los servicios, primero instala [Docker](https://docs.docker.com/engine/install/) en tu 
computadora (o en el servidor que desees usar).

2. Clona este repositorio.

3. Crea las carpetas `airflow/config`, `airflow/dags`, `airflow/logs`, `airflow/plugins`, 
`airflow/logs`.

4. Si estás en Linux o MacOS, en el archivo `.env`, reemplaza `AIRFLOW_UID` por el de tu 
usuario o alguno que consideres oportuno (para encontrar el UID, usa el comando 
`id -u <username>`). De lo contrario, Airflow dejará sus carpetas internas como root y no 
podrás subir DAGs (en `airflow/dags`) o plugins, etc.

5. En la carpeta raíz de este repositorio, ejecuta:

```bash
docker compose --profile all up
```

6. Una vez que todos los servicios estén funcionando (verifica con el comando `docker ps -a` 
que todos los servicios estén healthy o revisa en Docker Desktop), podrás acceder a los 
diferentes servicios mediante:
   - Apache Airflow: http://localhost:8080
   - MLflow: http://localhost:5000
   - MinIO: http://localhost:9001 (ventana de administración de Buckets)
   - API: http://localhost:8800/
   - Documentación de la API: http://localhost:8800/docs

Si estás usando un servidor externo a tu computadora de trabajo, reemplaza `localhost` por su IP 
(puede ser una privada si tu servidor está en tu LAN o una IP pública si no; revisa firewalls 
u otras reglas que eviten las conexiones).

Todos los puertos u otras configuraciones se pueden modificar en el archivo `.env`. Se invita 
a jugar y romper para aprender; siempre puedes volver a clonar este repositorio.

## Bajar servicios con Docker compose

Estos servicios ocupan cierta cantidad de memoria RAM y procesamiento, por lo que cuando no 
se están utilizando, se recomienda detenerlos. Para hacerlo, ejecuta el siguiente comando:

```bash
docker compose --profile all down
```

Si deseas no solo detenerlos, sino también eliminar toda la infraestructura (liberando espacio en disco), 
utiliza el siguiente comando:

```bash
docker compose down --rmi all --volumes
```

Nota: Si haces esto, perderás todo en los buckets y bases de datos.

## Simulación de servidor externo con dataset
Una de las tareas del servicio de airflow es realizar un fetch del datset.
Para eso simulamos un servidor externo que contiene el archivo zip con el dataset.

Para obterner el archivo ZIP con el proyecto:
```sh
kaggle datasets download -d fedesoriano/stroke-prediction-dataset
```

Una forma de simularlo es mediante un servidor http con python:

```sh
python -m http.server 12000 -d data/
```

Se elije el puerto 12000 para no asegurar que no es uno ya utilizado por otro proceso.

En este caso el puerto utilizado es el 12000 y se sirve la carpeta `data/`.
Luego, se debe actualizar la URL al archivo zip en la configuración del DAG (tener en cuenta que se debe utilizar la
dirección IP del sistema en la red local para que los servicios de docker puedan direccionarlo, localhost no funcionará).

IMPORTANTE: Es necesario actualizar en el archivo `etl_process.py` la dirección IP para descarga del ZIP con
la correspondiente a la máquina simulando el servidor.

La dirección IP de la máquina simulando el servidor externo se puede obtener mediante el comando `ip ad`.

Para chequear el funcionamiento del servidors se puede acceder al siguiente link: http://{YOUR_IP_ADDRESS}:12000/

## Ejecución de la pipeline completa

1. Simular servidor externo que contiene el ZIP del dataset
2. Levantar servicios con docker como se describió previamente
3. Chequear en navegador que tando el servidor con el dataset como todos los servicios involucrados (ver URLs descriptas previamente) se encuentran disponibles.
    - Tener en cuenta que la primera vez la REST API arrojará error por no tener ningun modelo en producción.
3. Ejecutar el proceso ETL en Airflow (credenciales airflow: airflow)
    - Se puede observar tanto en la UI de MLflow como en el bucket de minio los resultados del proceso.
4. Ejecutar el notebook [mlflow_model.ipynb](notebook/mlflow_model.ipynb) para poner el primer modelo en producción.
    - De ya haber un modelo en producción, el notebook arrojará un error (no se puede sobrescribir). Se puede eliminar el modelo en mlflow o cambiar el nombre del modelo a registrar.
    - Se puede ver los resultados del proceso reflejados en la UI de MLflow.
5. En airflow, ejecutar el pipeline para re-entrenar el modelo y competir con el actual en producción.
    - Se puede observar los resultados del entrenamiento y la competición entre el nuevo modelo y el en producción en la UI de MLflow.
6. Comprobar el funcionamiento de la REST API:
    - Una vez realizado el paso 5, el servicio de REST API debería reestablecerse luego de unos minutos. De lo contrario se puede realizar manualmente bajando y levantando los servicios.
    - Se puede ver la documentación de la API en el siguiente link: http://localhost:8800/docs
    - Se puede interactuar con la API con `curl`.

Ejemplo de predicción mediante la REST API:

```bash
curl -X 'POST'   'http://localhost:8800/predict/'   -H 'accept: application/json'   -H 'Content-Type: application/json'   -d '{
  "features": {
        "age": 67,
        "gender": "Male",
        "hypertension": 0,
        "heart_disease": 1,
        "ever_married": "Yes",
        "work_type": "Private",
        "Residence_type": "Urban",
        "avg_glucose_level": 228.69,
        "bmi": 36.6,
        "smoking_status": "smokes"
    }
}'
```
