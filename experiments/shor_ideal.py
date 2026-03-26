import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import argparse
import csv
from pathlib import Path
from typing import Dict, Any, List

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qft_engine import build_iqft_circuit

# -------------------------------------------------
# Oráculo Real para N=15, a=2
# -------------------------------------------------
def c_amod15(power: int):
    """
    Oráculo controlado que multiplica por 2^power mod 15.
    Requiere 4 qubits objetivo. Multiplicar por 2 mod 15 en binario 
    es simplemente un desplazamiento circular a la izquierda.
    """
    U = QuantumCircuit(4)
    # Aplicamos el desplazamiento circular 'power' veces
    for _ in range(power):
        U.swap(0, 1)
        U.swap(1, 2)
        U.swap(2, 3)
    
    U_gate = U.to_gate()
    U_gate.name = f"2^{power} mod 15"
    return U_gate.control(1) # Añadimos 1 qubit de control

# -------------------------------------------------
# Construcción del Circuito de Shor
# -------------------------------------------------
def build_shor_circuit(
    t_qubits: int,
    approximation_degree: int = 0,
) -> QuantumCircuit:
    
    n_target = 4 # 4 qubits para representar números hasta el 15
    n_total = t_qubits + n_target
    qc = QuantumCircuit(n_total, t_qubits)

    counting = list(range(t_qubits))
    target = list(range(t_qubits, n_total))

    # 1. Estado inicial del registro objetivo: |1> (0001 en binario)
    qc.x(target[0]) 

    # 2. Superposición en el registro de conteo
    for q in counting:
        qc.h(q)

    # 3. Exponenciación modular controlada
    for j, control in enumerate(counting):
        # Aplicamos la multiplicación por 2^(2^j)
        power = 2**j
        # Nota matemática: como 2^4 = 16 = 1 mod 15, las potencias de 4 en adelante son la identidad,
        # pero dejamos que el algoritmo haga los SWAPs para que sea genérico.
        qc.append(c_amod15(power), [control] + target)

    qc.barrier()

    # 4. IQFT / AIQFT (Reversión de bits para Qiskit)
    counting_reversed = counting[::-1]
    iqft = build_iqft_circuit(t_qubits, approximation_degree=approximation_degree)
    qc.append(iqft, counting_reversed)

    # 5. Medir solo el registro de conteo
    qc.measure(counting, list(range(t_qubits)))

    return qc

# -------------------------------------------------
# Ejecución
# -------------------------------------------------
def run_shor(t_qubits: int, approximation_degree: int, shots: int, seed: int) -> Dict[str, int]:
    qc = build_shor_circuit(t_qubits, approximation_degree)
    backend = AerSimulator(seed_simulator=seed)
    tqc = transpile(qc, backend, optimization_level=0, seed_transpiler=seed)
    result = backend.run(tqc, shots=shots).result()
    return result.get_counts()

def main():
    parser = argparse.ArgumentParser(description="Shor ideal (N=15, a=2).")
    
    root_dir = Path(__file__).resolve().parent.parent
    default_csv = root_dir / "experiments" / "results" / "shor_ideal.csv"
    
    parser.add_argument("--t_qubits", type=int, default=4) # 4 qubits de conteo
    parser.add_argument("--shots", type=int, default=4096)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--m_values", type=int, nargs="+", default=[0, 1, 2, 3])
    parser.add_argument("--out_csv", type=str, default=str(default_csv))
    args = parser.parse_args()

    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    rows: List[Dict[str, Any]] = []

    for m in args.m_values:
        print(f"Calculando Shor (N=15, a=2) con m={m}...")
        counts = run_shor(args.t_qubits, m, args.shots, args.seed)
        total = sum(counts.values())
        for bitstring, c in counts.items():
            rows.append({
                "t_qubits": args.t_qubits,
                "m": m,
                "shots": args.shots,
                "bitstring": bitstring,
                "probability": c / total,
            })

    fieldnames = ["t_qubits", "m", "shots", "bitstring", "probability"]
    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    print(f"✅ CSV generado en: {out_csv.resolve()}")

if __name__ == "__main__":
    main()