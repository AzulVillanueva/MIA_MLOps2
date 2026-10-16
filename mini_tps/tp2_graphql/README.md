# Mini-TP 2 — Metadatos del modelo por GraphQL (Sesión 2)

Expone los metadatos del mismo modelo del Mini-TP 1 con un esquema GraphQL (Strawberry).

## Entregable

**[`mini_tp2_actividad.ipynb`](mini_tp2_actividad.ipynb)** es el notebook a entregar: corre de punta a punta (levanta GraphQL y REST en hilos, ejecuta la query y la comparación) sin depender de servicios externos ya corriendo. `server.py`, `client.py` y `compare_rest_vs_graphql.py` son la misma lógica separada en scripts, útiles para levantar el servicio de forma independiente.

## Cómo correr

Con el Mini-TP 1 corriendo en el puerto 8001 (para la comparación), levantar este servicio en otro puerto:

```bash
python -m uvicorn mini_tps.tp2_graphql.server:app --port 8002
```

- GraphiQL: http://localhost:8002/graphql

Cliente Python:

```bash
python mini_tps/tp2_graphql/client.py
```

## Esquema

```graphql
type Metrics {
  accuracy: Float!
  precision: Float!
  recall: Float!
  f1Score: Float!
  trainObservations: Int!
  testObservations: Int!
}

type Model {
  name: String!
  version: Int!
  modelType: String!
  metrics: Metrics!
}

type Query {
  model: Model!
}
```

Query de ejemplo (pide solo lo necesario, no todo el recurso):

```graphql
{
  model {
    name
    version
    metrics { f1Score }
  }
}
```

```json
{"data": {"model": {"name": "stroke_prediction_model_prod", "version": 1, "metrics": {"f1Score": 0.9656964656964657}}}}
```

## Comparación REST vs GraphQL

```bash
python mini_tps/tp2_graphql/compare_rest_vs_graphql.py
```

Pidiendo la misma vista ("nombre, versión y F1 del modelo"):

| Protocolo | Llamadas | Bytes de respuesta |
|---|---|---|
| REST (`GET /v1/model`) | 1 | 271 |
| GraphQL (`{ model { name version metrics { f1Score } } }`) | 1 | 111 |

En el notebook la vista incluye también `accuracy`, y la diferencia es 141 vs 271 bytes (−48 %): cuantos más campos del recurso necesita el cliente, menos se ahorra.

**Diferencia observada:** en este caso ambos necesitan una sola llamada (no hay relaciones anidadas que generen N+1), pero **REST siempre devuelve el recurso completo** (`accuracy`, `precision`, `recall`, conteos de train/test) aunque el cliente solo quiera el F1 — es *over-fetching* por diseño, ya que el endpoint no sabe qué necesita el consumidor. **GraphQL** permite que el cliente declare exactamente los campos que quiere, y en este ejemplo trajo ~59% menos bytes. La ventaja de GraphQL crece con la cantidad de metadatos del modelo (hiperparámetros, historial de runs, linaje) y con clientes distintos que necesitan vistas distintas del mismo modelo; para un endpoint chico y estable como este, la diferencia es modesta y el costo de mantener un esquema adicional puede no justificarse.
