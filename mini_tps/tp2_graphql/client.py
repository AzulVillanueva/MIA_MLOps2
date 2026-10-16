"""Cliente Python del Mini-TP 2: consulta el modelo por GraphQL (GraphiQL: /graphql)."""
import requests

GRAPHQL_URL = "http://localhost:8002/graphql"

QUERY = """
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
    r = requests.post(GRAPHQL_URL, json={"query": QUERY})
    print(r.status_code, r.json())


if __name__ == "__main__":
    main()
