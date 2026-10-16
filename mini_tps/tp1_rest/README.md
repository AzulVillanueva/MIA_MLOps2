# Mini-TP 1 — API REST productiva (Sesión 1)

Sirve el modelo de predicción de stroke con FastAPI.

## Cómo correr

Desde la raíz de `MLOPs2_UBA_Tps/` (con el entorno activado y `common/artifacts/` ya generado):

```bash
python -m uvicorn mini_tps.tp1_rest.api:app --port 8001
```

- Docs interactivas: http://localhost:8001/docs

En otra terminal, el cliente de prueba:

```bash
python mini_tps/tp1_rest/client.py
```

## Qué expone

- **Contrato Pydantic** (`StrokeFeatures`) con las 10 features reales del modelo (género, edad, hipertensión, enfermedad cardíaca, estado civil, tipo de trabajo, residencia, glucosa, BMI, tabaquismo), con `Literal` y rangos (`ge`/`le`) para que la validación rechace entradas inválidas.
- `POST /v1/predict` → predicción + probabilidad + **nombre y versión del modelo**.
- `GET /health` → estado del servicio + versión del modelo cargado + uptime.
- `GET /v1/model` → metadatos completos del modelo (se usa para comparar contra GraphQL en el Mini-TP 2).

## Resultado del cliente

```
--- GET /health ---
200 {'status': 'ok', 'model_name': 'stroke_prediction_model_prod', 'model_version': 1, ...}

--- POST /v1/predict (caso válido) ---
200 {'stroke_predicted': False, 'label': 'Not likely to have a stroke', 'probability': 0.15, ...}

--- POST /v1/predict (caso inválido -> se espera 422) ---
422 {'detail': [{'loc': ['body', 'gender'], 'msg': "Input should be 'Male', 'Female' or 'Other'", ...},
               {'loc': ['body', 'age'], 'msg': 'Input should be greater than or equal to 0', ...}]}
```

El caso inválido usa un `gender` fuera del `Literal` permitido y una `age` negativa; FastAPI/Pydantic devuelven **422** con el detalle de cada campo que falló, sin llegar a ejecutar el modelo.
