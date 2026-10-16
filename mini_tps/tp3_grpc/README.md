# Mini-TP 3 — Servicio gRPC (Sesión 3)

Expone el mismo modelo por gRPC: contrato tipado (`scoring.proto`), unary y server-streaming.

## Entregable

**[`mini_tp3_actividad.ipynb`](mini_tp3_actividad.ipynb)** es el notebook a entregar: escribe el `.proto`, genera los stubs, levanta el servidor gRPC y el REST de la Sesión 1 en hilos, prueba unary y streaming, y corre la comparación de latencia — todo de punta a punta sin depender de procesos externos. `server.py`, `client.py` y `compare_latency.py` son la misma lógica en scripts independientes.

## Cómo correr

Generar los stubs (ya generados en este repo; regenerar solo si se edita el `.proto`):

```bash
cd mini_tps/tp3_grpc
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. scoring.proto
```

Levantar el servidor (carga el modelo una sola vez, puerto 50051):

```bash
python mini_tps/tp3_grpc/server.py
```

Cliente (unary + streaming):

```bash
python mini_tps/tp3_grpc/client.py
```

## Contrato (`scoring.proto`)

```protobuf
message StrokeFeatures {
  string gender = 1;
  double age = 2;
  int32 hypertension = 3;
  int32 heart_disease = 4;
  string ever_married = 5;
  string work_type = 6;
  string residence_type = 7;
  double avg_glucose_level = 8;
  double bmi = 9;
  string smoking_status = 10;
}

message StrokeBatch { repeated StrokeFeatures items = 1; }

message Prediction {
  bool stroke_predicted = 1;
  string label = 2;
  double probability = 3;
  string model_name = 4;
  int32 model_version = 5;
}

service Scoring {
  rpc Predict(StrokeFeatures) returns (Prediction);         // unary
  rpc PredictBatch(StrokeBatch) returns (stream Prediction); // server-streaming
}
```

## Resultado del cliente

```
--- Predict (unary) ---
label: "Not likely to have a stroke"
probability: 0.15
model_name: "stroke_prediction_model_prod"
model_version: 1

--- PredictBatch (server-streaming) ---
Not likely to have a stroke | probabilidad: 0.15
Not likely to have a stroke | probabilidad: 0.0
Not likely to have a stroke | probabilidad: 0.45
```

## Comparación de latencia gRPC vs REST

Con el servidor gRPC (puerto 50051) y el REST del Mini-TP 1 (puerto 8001) corriendo:

```bash
python mini_tps/tp3_grpc/compare_latency.py
```

```
gRPC: 9.26 ms/llamada  (N=200)
REST: 10.58 ms/llamada  (N=200)
gRPC fue 1.14x más rápido que REST en este caso.
```

(Nota: la primera medición, con `requests.post` abriendo una conexión TCP nueva por llamada, daba ~2000 ms/llamada en REST — no es un número real de "REST vs gRPC", es el costo del handshake. Con una sesión HTTP con keep-alive para ambos protocolos, la diferencia real es mucho más chica y comparable a la reportada arriba.)

### Reflexión

Con un solo modelo chico y llamadas locales, gRPC y REST rinden parecido una vez que ambos reusan la conexión: la diferencia está dominada por el tiempo de inferencia del modelo, no por el protocolo. La ventaja real de gRPC aparece en **comunicación interna entre microservicios** de alta frecuencia (HTTP/2 multiplexado, payload binario más chico que JSON, contrato `.proto` estricto que evita bugs de serialización) y en el **streaming nativo** para puntuar lotes sin reabrir conexión por cada item. Elegiría **REST/GraphQL** para el borde público de la plataforma (lo habla cualquier navegador o cliente sin tooling extra) y **gRPC** para la comunicación interna entre el servicio de scoring y otros microservicios de la plataforma (por ejemplo, el orquestador de Aprendizaje Federado hablando con cada nodo). El costo de gRPC es el tooling (generar y versionar stubs, `.proto` como fuente de verdad) y que no lo consume directamente un navegador sin un proxy (grpc-web).
