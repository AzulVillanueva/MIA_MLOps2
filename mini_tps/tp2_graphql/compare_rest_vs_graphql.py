"""Compara REST vs GraphQL para la misma lectura: 'nombre, version y f1_score del modelo'.

REST no tiene forma de pedir un subconjunto de campos: siempre devuelve el
recurso completo (over-fetching). GraphQL permite pedir solo lo necesario.
Corre con el Mini-TP 1 (puerto 8001) y el Mini-TP 2 (puerto 8002) levantados.
"""
import requests

REST_URL = "http://localhost:8001/v1/model"
GRAPHQL_URL = "http://localhost:8002/graphql"

GRAPHQL_QUERY = """
{
  model {
    name
    version
    metrics {
      f1Score
    }
  }
}
"""


def main() -> None:
    rest_response = requests.get(REST_URL)
    graphql_response = requests.post(GRAPHQL_URL, json={"query": GRAPHQL_QUERY})

    rest_bytes = len(rest_response.content)
    graphql_bytes = len(graphql_response.content)

    print("=== REST /v1/model (1 llamada) ===")
    print(rest_response.json())
    print(f"bytes de respuesta: {rest_bytes}")

    print("\n=== GraphQL (1 llamada, solo name/version/f1Score) ===")
    print(graphql_response.json())
    print(f"bytes de respuesta: {graphql_bytes}")

    ahorro_pct = 100 * (1 - graphql_bytes / rest_bytes)
    print(f"\nAmbos protocolos necesitan 1 sola llamada aqui (no hay N+1).")
    print(f"GraphQL trajo {ahorro_pct:.0f}% menos bytes que REST para la misma vista"
          f" (REST siempre trae accuracy/precision/recall aunque no se pidan; over-fetching).")


if __name__ == "__main__":
    main()
