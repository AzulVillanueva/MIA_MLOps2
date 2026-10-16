# Guion de la demo — TP integrador MLOps II

Cecilia Villanueva · duración: unos 11 minutos (slides 4 min · demo 6 min · cierre 1 min).

---

## 1. Preparación (10 minutos antes)

**a) Abrir Docker Desktop** y esperar a que esté corriendo.

**b) Levantar el stack** (PowerShell):

```
cd tp_integrador\stack
docker compose --profile all up -d
docker ps
```

Repetir `docker ps` hasta que los 6 contenedores (postgres, minio, mlflow, airflow_webserver, airflow_scheduler, fastapi) digan *healthy*.

**c) Levantar la API segura con el champion** (otra terminal, desde la raíz del repo):

```
tp_integrador\servir.bat
```

**d) Publicar el champion en el data lake:**

```
.venv\Scripts\python.exe tp_integrador\datalake\publicar_champion.py
```

**e) Abrir estas pestañas, en este orden:**

| # | URL | Credenciales |
|---|---|---|
| 1 | http://localhost:8080 | Airflow: `airflow` / `airflow` |
| 2 | http://localhost:5000 | MLflow: vista **Model training** |
| 3 | http://localhost:8009/docs | API REST segura (champion) |
| 4 | http://localhost:9001 | MinIO: `minio` / `minio123` |

**f) Comprobación rápida:** en la pestaña 3, `POST /v1/predict` sin autenticarse debe dar 401. Después, **esperar 60 segundos** para que el límite de consultas se reinicie.

---

## 2. Slides

**Slide 1 · Portada (40 s)**
"Hola, soy Cecilia. Mi TP integrador es una plataforma de predicción de riesgo de ACV, accidente cerebrovascular. Parte del modelo que hice en Aprendizaje de Máquina: un RandomForest entrenado con unos 5.100 pacientes de un dataset de Kaggle. En esta materia el foco no es el modelo, sino cómo se opera en producción. Por eso el objetivo fue ese: un modelo en producción, orquestado, versionado, seguro y con datos trazables."

**Slide 2 · Arquitectura (1 min 30 s)**
"El corazón del TP es el stack de producción. Corre todo en Docker y se levanta con un solo comando. Airflow tiene dos flujos. El primero descarga los datos, los limpia, convierte las variables categóricas, los separa en entrenamiento y test, balancea las clases solo en entrenamiento, y los normaliza. Todo queda guardado en MinIO. El segundo reentrena el modelo y lo compara con el que está en producción. En MLflow, el alias *champion* marca qué versión está en producción. El modelo nuevo toma su lugar solo si tiene mejor F1, y para volver atrás alcanza con mover esa etiqueta.

De los mini-TPs, elegí integrar dos: la API REST con seguridad, que combina el TP1 y el TP7, y el data lake del TP6. Los elegí porque no son alternativas, sino cosas que cualquier sistema en producción necesita. Un modelo con datos de salud no puede estar expuesto sin autenticación, y los datos y los modelos tienen que guardarse versionados para poder auditar y volver atrás."

**Slide 3 · Qué aprendí de los mini-TPs (1 min 30 s)**
"Como todos los mini-TPs usan el mismo modelo y el mismo preprocesamiento, los resultados se pueden comparar. No es para usarlos todos juntos, sino para entender en qué caso conviene cada uno.

Seguridad: sin token, la API responde 401; con un rol sin permiso, 403; si alguien consulta en ráfaga, 429. Ese límite frena el robo del modelo, porque quien consulta sin freno puede entrenar una copia. Y como son datos de salud, la auditoría guarda un hash, no el dato clínico.

Data lake: los datos se guardan en tres etapas: como llegaron, ya limpios, y los modelos entrenados. Cada versión del modelo se guarda aparte y nunca se pisa.

Los demás los usé para comparar alternativas. GraphQL devuelve solo lo que pido: 59 % menos bytes que REST. gRPC suma un contrato tipado, pensado para microservicios. En federado, el entrenamiento es didáctico: usé un modelo softmax, porque FedAvg promedia pesos y un RandomForest no tiene pesos que se puedan promediar. Con datos parejos entre nodos, la precisión es 0.78; con datos sesgados, cae a 0.52. Y en streaming procesé 800 eventos con un p95 de unos 24 milisegundos, con una alerta de drift que avisa si cambia el perfil de los pacientes que llegan. A eso vuelvo al final.

Ahora lo vemos funcionando."

---

## 3. Demo (6 min)

**Pantalla 1 · Airflow (1 min 30 s).** Los dos DAGs en verde; entrar a uno y abrir Grid o Graph.
"Acá están los dos flujos. El primero prepara los datos y los deja en MinIO. El segundo entrena un modelo nuevo con los mismos hiperparámetros que el actual y los compara sobre el mismo set de test. Estas corridas ya están hechas, porque el ETL tarda unos minutos."

**Pantalla 2 · MLflow (1 min).** Models → `stroke_prediction_model_prod` → alias `champion`.
"Acá se versionan los modelos. El alias champion marca cuál está en producción. Para promover un modelo o volver atrás, solo muevo esa etiqueta."

**Pantalla 3 · API REST segura (2 min).**

| Paso | Acción | Resultado | Decir |
|---|---|---|---|
| 1 | `POST /v1/predict` sin autenticarse | **401** | "Sin token, no pasa." |
| 2 | *Authorize* con `analista` / `analista123` y ejecutar | **200** | "Con un token JWT, sí. Y sirve el mismo champion de MLflow." |
| 3 | Ejecutar 5 o 6 veces más | **429** | "Un límite por usuario frena el robo del modelo." |
| 4 | *Authorize* con `invitado` / `invitado123` | **403** | "Autentica, pero su rol no tiene permiso." |
| 5 | *Authorize* con `admin` / `admin123`, `GET /v1/auditoria` | registros | "Se audita cada predicción, pero guardando un hash, no el dato del paciente." |

**Pantalla 4 · Data lake en MinIO (1 min 30 s).** Bucket `datalake-tp6`.
"Acá está el data lake. Los datos están separados por etapa: crudos, limpios y modelos. Cada versión del modelo tiene su carpeta y nunca se sobrescribe. Este archivo, `champion.json`, apunta a la versión en producción. Así las piezas quedan conectadas: Airflow entrena, MLflow decide cuál es el champion, la API segura lo sirve y el data lake guarda cada versión."

---

## 4. Cierre (1 min)

"Para cerrar, lo que quedó pendiente. El streaming quedó simulado con una cola en memoria, no con Kafka, y por eso no lo integré. Pero es lo siguiente que sumaría, por el monitoreo: la alerta de drift detecta cuándo los pacientes que llegan ya no se parecen a los del entrenamiento. Conectada al stack, podría disparar el reentrenamiento en Airflow, y el ciclo quedaría cerrado: detectar el cambio, reentrenar y promover el modelo solo si mejora.

En resumen: un modelo en producción, orquestado, versionado, servido de forma segura y con cada versión guardada y trazable. Gracias."

---

## Si preguntan

- **¿Por qué no integraste todos los mini-TPs?** "Porque un sistema real no los necesita todos. Integré los que completan el sistema productivo; los demás me sirvieron para comparar alternativas con el mismo modelo."
- **¿Qué F1 tiene el modelo?** "11 por ciento sobre el test real: precision 0.19 y recall 0.08. Antes el pipeline daba 0.97, pero estaba inflado: el SMOTE se aplicaba antes de separar entrenamiento y test, así que el test tenía casos sintéticos. Lo corregí: ahora el test conserva la distribución real. El resultado dice que el modelo detecta pocos casos de ACV, y mejorarlo es el siguiente paso de modelado; lo que muestro hoy es la plataforma que lo opera."
- **¿El split es 70/30?** "No, es 80/20, y la descripción del DAG ya está alineada con el código."

## Si algo falla

- **Un contenedor "unhealthy":** esperar 1 minuto y repetir `docker ps`.
- **La API en :8009 no carga:** revisar que el stack esté arriba. Plan B: `MODEL_SOURCE=local` y el puerto 8007.
- **Aparece 429 antes de tiempo:** el límite es de 5 consultas por minuto; esperar 60 segundos.
- **Plan B general:** capturas en `tp_integrador/docs/img/`.

## Al terminar

```
tp_integrador\parar.bat
cd tp_integrador\stack
docker compose --profile all down
```
