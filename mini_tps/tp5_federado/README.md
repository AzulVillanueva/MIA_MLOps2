# Mini-TP 5 — Aprendizaje federado y trade-off privacidad/performance (Sesión 5)

Simulación de **FedAvg** sobre el dataset de stroke, repartido entre K clientes, y análisis del costo de no mover el dato.

## Entregable

**[`mini_tp5_federado_resuelto.ipynb`](mini_tp5_federado_resuelto.ipynb)** — corre de punta a punta en local, sin servicios externos.

## Qué hace el notebook

1. **Datos y modelo:** mismo dataset y preprocesamiento (one-hot + SMOTE + escalado) que `common/`. Como los árboles del `RandomForest` original no tienen pesos promediables, se usa un clasificador **softmax** (regresión logística) entrenado con SGD. El RF queda como referencia.
2. **Línea de base centralizada:** entrena el softmax con todos los datos.
3. **FedAvg:** entrenamiento local por cliente + agregación ponderada por tamaño, con fracción de clientes por ronda.
4. **Particiones:** IID (aleatoria) y non-IID (shards ordenados por etiqueta, muy sesgados).
5. **Gráfico** de accuracy vs ronda: federado IID, non-IID y líneas de base centralizada.
6. **(Opcional) Ruido:** ruido gaussiano sobre los pesos agregados para ver el impacto en accuracy. Es didáctico, **no** es privacidad diferencial formal (falta clipping y privacy accounting).

## Resultados (ver reflexión en el notebook)

| Configuración | Accuracy |
|---|---|
| Softmax centralizado | 0.782 |
| FedAvg IID | 0.780 |
| FedAvg non-IID | 0.525 |
| RandomForest original (referencia) | 0.966 |

## Cómo correr

```bash
python common/train_model.py     # solo la primera vez (genera artefactos)
```

Abrir el notebook con el kernel `mlops2` y ejecutar todas las celdas. Requiere `matplotlib` (incluido en `requirements.txt`).
