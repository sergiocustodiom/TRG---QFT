import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import argparse
import csv
from pathlib import Path
from typing import Dict, List

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error, ReadoutError

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
# Modelos de ruido sintético
# ======================================================
def make_synthetic_noise_model() -> NoiseModel:
    p1 = 1e-3  
    p2 = 1e-2  
    pread = 2e-2 

    noise = NoiseModel()
    noise.add_all_qubit_quantum_error(depolarizing_error(p1, 1), ["h", "x"])
    noise.add_all_qubit_quantum_error(depolarizing_error(p2, 2), ["cp", "swap"])

    ro = ReadoutError([[1 - pread, pread], [pread, 1 - pread]])
    noise.add_all_qubit_readout_error(ro)

    return noise

# ======================================================
# Ejecución "Test del Eco" (Forward + Inverse)
# ======================================================
def run_echo_experiment(
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

    # 3. Aplicamos la Inversa para intentar recuperar el estado
    exact_qft = build_qft_circuit(n, approximation_degree=0)
    inv_qft = exact_qft.inverse()
    qc.append(inv_qft, range(n))

    qc.measure(range(n), range(n))

    # Simulamos
    backend = AerSimulator(noise_model=noise_model, seed_simulator=seed)
    tqc = transpile(qc, backend, optimization_level=0, seed_transpiler=seed)
    result = backend.run(tqc, shots=shots).result()
    counts = result.get_counts()

    # IMPORTANTE: Qiskit invierte el string al medir (little-endian)
    expected_measurement = bitstring[::-1]
    
    # Calculamos la probabilidad de recuperar el estado original intacto
    successes = counts.get(expected_measurement, 0)
    return successes / shots

# ======================================================
# Experimento principal
# ======================================================
def build_rows(n_min: int, n_max: int, m_values: List[int], shots: int, seed: int) -> List[Dict]:
    rows = []
    noise_model = make_synthetic_noise_model()

    for n in range(n_min, n_max + 1):
        states = [("all_ones", bitstring_all_ones(n)), ("pattern", bitstring_pattern_1010(n))]

        for state_label, bitstring in states:
            # Línea base: QFT completa (m=0) sufriendo el ruido
            succ_qft = run_echo_experiment(bitstring, "QFT", 0, shots, noise_model, seed)
            rows.append({
                "state_label": state_label,
                "bitstring": bitstring,
                "n_qubits": n,
                "m": 0,
                "shots": shots,
                "noise_regime": "synthetic",
                "success_prob": succ_qft,
            })

            # AQFT(m): ¿Ahorrar puertas compensa el error teórico?
            for m in m_values:
                succ_aqft = run_echo_experiment(bitstring, "AQFT", m, shots, noise_model, seed)
                rows.append({
                    "state_label": state_label,
                    "bitstring": bitstring,
                    "n_qubits": n,
                    "m": m,
                    "shots": shots,
                    "noise_regime": "synthetic",
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--n_min", type=int, default=2)
    parser.add_argument("--n_max", type=int, default=10)
    parser.add_argument("--m_values", type=int, nargs="+", default=[1, 2, 3, 4])
    parser.add_argument("--shots", type=int, default=2048)
    parser.add_argument("--seed", type=int, default=123)
    
    base_dir = Path(__file__).resolve().parent.parent
    default_csv = base_dir / "experiments" / "results" / "noisy_fidelity_qft_vs_aqft.csv"
    parser.add_argument("--out_csv", type=str, default=str(default_csv))
    args = parser.parse_args()

    print("Iniciando Test de Reversibilidad con ruido...")
    rows = build_rows(args.n_min, args.n_max, args.m_values, args.shots, args.seed)
    write_csv(rows, Path(args.out_csv))
    print(f"✅ CSV generado: {Path(args.out_csv).resolve()}")

if __name__ == "__main__":
    main()