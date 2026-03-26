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
# Oráculo Real para N=7, a=2
# -------------------------------------------------
def c_amod7(power: int):
    """
    Oráculo que multiplica por 2^power mod 7.
    Requiere 3 qubits objetivo. Multiplicar por 2 mod 7 en binario 
    es un desplazamiento circular a la izquierda sobre 3 bits.
    """
    U = QuantumCircuit(3)
    for _ in range(power):
        # Desplazamiento circular en Qiskit (little-endian)
        U.swap(1, 2)
        U.swap(0, 1)
    
    U_gate = U.to_gate()
    U_gate.name = f"2^{power} mod 7"
    return U_gate.control(1)

# -------------------------------------------------
# Construcción del Circuito de Shor (N=7)
# -------------------------------------------------
def build_shor_n7_circuit(t_qubits: int, m: int = 0) -> QuantumCircuit:
    n_target = 3 # 3 qubits para representar hasta el número 7
    n_total = t_qubits + n_target
    qc = QuantumCircuit(n_total, t_qubits)

    counting = list(range(t_qubits))
    target = list(range(t_qubits, n_total))

    # 1. Estado inicial del objetivo: |1> (001)
    qc.x(target[0]) 

    # 2. Superposición en el conteo
    for q in counting:
        qc.h(q)

    # 3. Exponenciación modular controlada
    for j, control in enumerate(counting):
        power = 2**j
        qc.append(c_amod7(power), [control] + target)

    qc.barrier()

    # 4. IQFT / AIQFT con bit-reversal
    counting_reversed = counting[::-1]
    iqft = build_iqft_circuit(t_qubits, approximation_degree=m)
    qc.append(iqft, counting_reversed)

    # 5. Medir
    qc.measure(counting, list(range(t_qubits)))
    return qc

def main():
    parser = argparse.ArgumentParser()
    root_dir = Path(__file__).resolve().parent.parent
    default_csv = root_dir / "experiments" / "results" / "shor_n7.csv"
    
    parser.add_argument("--t_qubits", type=int, default=5) # 5 qubits para ver bien los picos de tercios
    parser.add_argument("--shots", type=int, default=4096)
    parser.add_argument("--m_values", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    parser.add_argument("--out_csv", type=str, default=str(default_csv))
    args = parser.parse_args()

    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    rows: List[Dict[str, Any]] = []

    for m in args.m_values:
        print(f"Calculando Shor (N=7, a=2) con m={m}...")
        qc = build_shor_n7_circuit(args.t_qubits, m)
        backend = AerSimulator()
        tqc = transpile(qc, backend, optimization_level=0)
        counts = backend.run(tqc, shots=args.shots).result().get_counts()
        
        total = sum(counts.values())
        for bitstring, c in counts.items():
            rows.append({
                "t_qubits": args.t_qubits,
                "m": m,
                "probability": c / total,
                "bitstring": bitstring
            })

    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    print(f"✅ CSV guardado en: {out_csv.resolve()}")

if __name__ == "__main__":
    main()

