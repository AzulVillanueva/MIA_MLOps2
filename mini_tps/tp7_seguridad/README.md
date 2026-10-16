# Mini-TP 7 — Seguridad con SAIF sobre REST (Sesión 7)

Asegura la API REST del modelo de riesgo de ACV siguiendo el marco SAIF (Secure AI Framework).

## Entregable

**[`mini_tp7_rest_resuelto.ipynb`](mini_tp7_rest_resuelto.ipynb)** corre de punta a punta sin servicios externos: usa `TestClient` de FastAPI sobre el modelo de `common/`.

## Marco SAIF en esta capa

- **Riesgo:** abuso, inyección, DoS y *scraping* para robar el modelo.
- **Controles:** autenticación (API key y JWT), validación de entrada y rate limiting.
- **Elementos SAIF:** bases de seguridad sólidas y automatizar defensas.
- **Gobernanza agregada:** log de auditoría y model card.

## Qué hace el notebook

1. **Versión vulnerable:** sin autenticación, sin validación y sin límites; acepta 1.000 consultas seguidas.
2. **Control guiado:** API key, validación y rate limiting.
3. **Entrega:** JWT con roles (`analista`, `admin`), validación Pydantic con las features reales del modelo (`Literal` y rangos), auditoría con hash de la entrada y endpoint `/v1/model-card`.

## Resultados

| Prueba | Resultado |
| --- | --- |
| Sin token / token expirado / token manipulado | 401 |
| Rol no permitido | 403 |
| Entrada inválida | 422 |
| Usuario válido | 200 |
| Ráfaga de consultas (límite 5 por minuto) | 200, 200, 200, 429, 429, 429 |

La auditoría guarda usuario, hash de la entrada (no el dato clínico) y predicción. La model card informa nombre, versión, métricas, uso previsto y limitaciones.

## Rate limiting y robo del modelo

Quien puede consultar sin límite reúne miles de pares entrada/salida y entrena una copia del modelo (extracción o robo del modelo), además de poder saturar el servicio. Limitar las consultas por usuario encarece ese ataque. Validar la entrada también es seguridad: rechaza datos malformados o absurdos antes de que lleguen al modelo.

## Límites del notebook

El rate limiting es en memoria (un solo proceso), no hay TLS, `crear_token` es solo de demo y la auditoría vive en memoria. En producción, el límite iría en un gateway o en Redis, los tokens los emitiría un proveedor de identidad y la auditoría iría a almacenamiento persistente e inmutable.

## El servicio

La versión que corre como servicio persistente, con Swagger, auditoría en archivo, rate limit opcional en Redis y HTTPS, vive en [`tp_integrador/api_segura/`](../../tp_integrador/api_segura/) y se integra al TP integrador: sirve el champion de MLflow. Ver [../../tp_integrador/README.md](../../tp_integrador/README.md).
