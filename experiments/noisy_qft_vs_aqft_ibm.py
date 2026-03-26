import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import argparse
import csv
from pathlib import Path
from typing import Dict, List

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel
from qiskit_ibm_runtime import QiskitRuntimeService

from qft_engine import build_qft_circuit

# ======================================================
# Estados base
# ======================================================
def bitstring_all_ones(n: int) -> str:
    return "1" * n

def bitstring_pattern_1010(n: int) -> str:
    return "".join("1" if i % 2 == 0 else "0" for i in range(n))

def prepare_basis_state(qc: QuantumCircuit, bitstring: str) -> None:
    for i, b in enumerate(bitstring):
        if b == "1":
            qc.x(i)

# ======================================================
# Ruido Real de IBM
# ======================================================
def make_ibm_noise_model(backend_name: str) -> NoiseModel:
    """
    Descarga el perfil de ruido actual de un backend real de IBM.
    Requiere tener la cuenta de IBM Quantum guardada localmente.
    """
    print(f"🔄 Conectando a IBM Quantum para descargar calibración de {backend_name}...")
    service = QiskitRuntimeService()
    backend = service.backend(backend_name)
    noise_model = NoiseModel.from_backend(backend)
    print("✅ Perfil de ruido descargado.")
    return noise_model

# ======================================================
# Ejecución "Test del Eco" (Reversibilidad)
# ======================================================
def run_echo_experiment_ibm(
    bitstring: str,
    transform: str,
    m: int,
    shots: int,
    noise_model: NoiseModel,
    seed: int,
) -> float:
    n = len(bitstring)
    qc = QuantumCircuit(n, n)

    # 1. Preparamos estado
    prepare_basis_state(qc, bitstring)

    # 2. Aplicamos la transformación RUIDOSA a evaluar
    if transform == "QFT":
        forward_qft = build_qft_circuit(n, approximation_degree=0)
    else:
        forward_qft = build_qft_circuit(n, approximation_degree=m)
    qc.append(forward_qft, range(n))

    # 3. Aplicamos la Inversa (Exacta) para intentar recuperar el estado
    exact_qft = build_qft_circuit(n, approximation_degree=0)
    inv_qft = exact_qft.inverse()
    qc.append(inv_qft, range(n))

    qc.measure(range(n), range(n))

    # Simulamos con el ruido real de IBM
    backend = AerSimulator(noise_model=noise_model, seed_simulator=seed)
    
    # OJO: Nivel de optimización 1 o 2 suele ser mejor para ruido real, 
    # pero lo dejamos en 0 para no alterar tu circuito original
    tqc = transpile(qc, backend, optimization_level=0, seed_transpiler=seed)
    result = backend.run(tqc, shots=shots).result()
    counts = result.get_counts()

    # Qiskit invierte el string al medir (little-endian)
    expected_measurement = bitstring[::-1]
    
    successes = counts.get(expected_measurement, 0)
    return successes / shots

# ======================================================
# Experimento principal
# ======================================================
def build_rows(
    n_min: int, n_max: int, m_values: List[int], shots: int, seed: int, backend_name: str
) -> List[Dict]:

    rows = []
    # Descargamos el modelo de ruido una sola vez
    noise_model = make_ibm_noise_model(backend_name)

    for n in range(n_min, n_max + 1):
        states = [("all_ones", bitstring_all_ones(n)), ("pattern", bitstring_pattern_1010(n))]

        for state_label, bitstring in states:
            # Baseline: QFT completa (m=0) con ruido IBM
            succ_qft = run_echo_experiment_ibm(bitstring, "QFT", 0, shots, noise_model, seed)
            rows.append({
                "state_label": state_label,
                "bitstring": bitstring,
                "n_qubits": n,
                "m": 0,
                "shots": shots,
                "noise_regime": "ibm_real",
                "noise_label": backend_name,
                "success_prob": succ_qft,
            })

            # AQFT(m) con ruido IBM
            for m in m_values:
                succ_aqft = run_echo_experiment_ibm(bitstring, "AQFT", m, shots, noise_model, seed)
                rows.append({
                    "state_label": state_label,
                    "bitstring": bitstring,
                    "n_qubits": n,
                    "m": m,
                    "shots": shots,
                    "noise_regime": "ibm_real",
                    "noise_label": backend_name,
                    "success_prob": succ_aqft,
                })
    return rows

def write_csv(rows: List[Dict], out_csv: Path):
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with out_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def main():
    parser = argparse.ArgumentParser(description="Paso 4B: Reversibilidad QFT vs AQFT (IBM).")
    parser.add_argument("--backend", type=str, default="ibm_fez") # Asegúrate de que tienes acceso a ibm_fez
    parser.add_argument("--n_min", type=int, default=2)
    parser.add_argument("--n_max", type=int, default=8) # Lo dejamos en 8, el ruido de IBM es fuerte
    parser.add_argument("--m_values", type=int, nargs="+", default=[1, 2, 3, 4])
    parser.add_argument("--shots", type=int, default=2048)
    parser.add_argument("--seed", type=int, default=123)
    
    # Rutas absolutas
    base_dir = Path(__file__).resolve().parent.parent
    default_csv = base_dir / "experiments" / "results" / "noisy_fidelity_qft_vs_aqft_ibm.csv"
    parser.add_argument("--out_csv", type=str, default=str(default_csv))
    args = parser.parse_args()

    print(f"Iniciando simulación con ruido de {args.backend}...")
    rows = build_rows(args.n_min, args.n_max, args.m_values, args.shots, args.seed, args.backend)
    write_csv(rows, Path(args.out_csv))
    print(f"✅ CSV IBM generado: {Path(args.out_csv).resolve()}")

if __name__ == "__main__":
    main()