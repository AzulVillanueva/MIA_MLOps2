"""Recorrido de punta a punta por los 7 mini-TPs sobre el mismo modelo de stroke.

    python mini_tps/demo_todos/run_demo.py            # todo (streaming/federado ejecutan notebooks, ~1-3 min)
    python mini_tps/demo_todos/run_demo.py --rapido   # omite la ejecucion de notebooks (muestra resultados guardados)

Cada paso imprime un encabezado; si un servicio externo (MinIO) no esta, se informa y se sigue.
"""
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "common" / "inference.py").exists())
PY = sys.executable
RAPIDO = "--rapido" in sys.argv
procs: list[subprocess.Popen] = []


def titulo(t: str) -> None:
    print(f"\n{'=' * 70}\n{t}\n{'=' * 70}", flush=True)


def run(args: list[str], **kw) -> int:
    return subprocess.run([PY, *args], cwd=ROOT, **kw).returncode


def servidor(args: list[str], puerto: int) -> None:
    procs.append(subprocess.Popen([PY, *args], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
    for _ in range(60):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", puerto)) == 0:
                return
        time.sleep(0.5)
    raise RuntimeError(f"el servidor en el puerto {puerto} no arranco")


def _kernel_del_entorno() -> str:
    """Registra un kernel que usa ESTE interprete (el del venv).

    Los notebooks piden el kernel 'python3', que en algunas maquinas apunta a otra instalacion
    de Python (p. ej. Anaconda) con librerias distintas.
    """
    import json
    import os
    import tempfile

    base = Path(tempfile.mkdtemp(prefix="stroke_kernels_"))
    spec = base / "kernels" / "stroke_demo"
    spec.mkdir(parents=True)
    (spec / "kernel.json").write_text(
        json.dumps({
            "argv": [PY, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
            "display_name": "stroke_demo",
            "language": "python",
        })
    )
    os.environ["JUPYTER_PATH"] = str(base) + os.pathsep + os.environ.get("JUPYTER_PATH", "")
    return "stroke_demo"


def notebook(ruta: str) -> None:
    import nbformat
    from nbclient import NotebookClient

    nb = nbformat.read(ROOT / ruta, as_version=4)
    NotebookClient(
        nb,
        kernel_name=_kernel_del_entorno(),
        timeout=600,
        resources={"metadata": {"path": str(ROOT / Path(ruta).parent)}},
    ).execute()
    for cell in nb.cells:
        for out in cell.get("outputs", []):
            txt = out.get("text", "")
            if txt:
                print(txt[-600:])
    print(f"OK: {ruta}")


try:
    titulo("0. Modelo (common/): artefactos entrenados")
    if not (ROOT / "common/artifacts/model.pkl").exists():
        run(["common/train_model.py"])
    print("model.pkl y data_dict.json listos")

    titulo("1+7. REST seguro (TP1 + TP7): JWT, roles, validacion, rate limit, auditoria")
    notebook("mini_tps/tp7_seguridad/mini_tp7_rest_resuelto.ipynb")

    titulo("2. GraphQL (TP2): el cliente pide solo los campos que necesita")
    servidor(["-m", "uvicorn", "mini_tps.tp2_graphql.server:app", "--port", "8002"], 8002)
    run(["mini_tps/tp2_graphql/client.py"])

    titulo("3. gRPC (TP3): contrato tipado, unary + streaming")
    servidor(["mini_tps/tp3_grpc/server.py"], 50051)
    run(["mini_tps/tp3_grpc/client.py"])

    for t, nb in [
        ("4. Streaming (TP4): eventos, latencia p95, drift y alerta", "mini_tps/tp4_streaming/mini_tp4_resuelto.ipynb"),
        ("5. Federado (TP5): FedAvg IID vs non-IID", "mini_tps/tp5_federado/mini_tp5_federado_resuelto.ipynb"),
    ]:
        titulo(t)
        if RAPIDO:
            print(f"(omitido con --rapido; ver {nb})")
        else:
            notebook(nb)

    titulo("6. Data Lake (TP6): modelo versionado en MinIO/S3")
    with socket.socket() as s:
        minio_up = s.connect_ex(("127.0.0.1", 9000)) == 0
    if minio_up and not RAPIDO:
        notebook("mini_tps/tp6_datalake/mini_tp6_resuelto.ipynb")
    else:
        print("MinIO no esta en localhost:9000 (o --rapido): paso omitido. Levantarlo con el docker run del README del TP6.")

    titulo("Fin: el mismo modelo servido (REST/GraphQL/gRPC), streameado, federado, en el lake y asegurado")
finally:
    for p in procs:
        p.terminate()
