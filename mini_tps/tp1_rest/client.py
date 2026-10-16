"""Cliente de prueba del Mini-TP 1: un caso valido y uno invalido (422)."""
import requests

BASE_URL = "http://localhost:8001"

VALID_CASE = {
    "gender": "Male",
    "age": 67,
    "hypertension": 0,
    "heart_disease": 1,
    "ever_married": "Yes",
    "work_type": "Private",
    "Residence_type": "Urban",
    "avg_glucose_level": 228.69,
    "bmi": 36.6,
    "smoking_status": "smokes",
}

INVALID_CASE = {
    **VALID_CASE,
    "gender": "Not-a-gender",  # valor fuera del Literal permitido
    "age": -5,  # viola ge=0
}


def main() -> None:
    print("--- GET /health ---")
    r = requests.get(f"{BASE_URL}/health")
    print(r.status_code, r.json())

    print("\n--- POST /v1/predict (caso valido) ---")
    r = requests.post(f"{BASE_URL}/v1/predict", json=VALID_CASE)
    print(r.status_code, r.json())

    print("\n--- POST /v1/predict (caso invalido -> se espera 422) ---")
    r = requests.post(f"{BASE_URL}/v1/predict", json=INVALID_CASE)
    print(r.status_code, r.json())


if __name__ == "__main__":
    main()
