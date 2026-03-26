import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import argparse
import csv
import json
import math
import numpy as np
from pathlib import Path
from typing import Dict, Any, List

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qft_engine import build_iqft_circuit

def normalize_counts(counts: Dict[str, int]) -> Dict[str, float]:
    total = sum(counts.values())
    return {k: v / total for k, v in counts.items()}

def bitstring_to_phase(bitstring: str) -> float:
    t = len(bitstring)
    return int(bitstring, 2) / (2 ** t)

def calculate_dispersion(counts: Dict[str, int], true_phase: float) -> float:
    """Calcula la desviación típica de las fases medidas respecto a la real."""
    total_shots = sum(counts.values())
    variance = 0
    for b, count in counts.items():
        phase_measured = bitstring_to_phase(b)
        # Manejo de circularidad (la fase 0.99 está cerca de 0.0)
        diff = abs(phase_measured - true_phase)
        diff = min(diff, 1 - diff) 
        variance += count * (diff ** 2)
    return math.sqrt(variance / total_shots)

def build_qpe_circuit(t_qubits: int, phase: float, approximation_degree: int = 0) -> QuantumCircuit:
    n_total = t_qubits + 1
    qc = QuantumCircuit(n_total, t_qubits)
    counting = list(range(t_qubits))
    target = t_qubits

    # 1. Preparación del estado
    qc.x(target) # Estado |1>
    for q in counting: qc.h(q)

    # 2. Oracle (Control-U potencias)
    theta = 2 * math.pi * phase
    for j, control in enumerate(counting):
        qc.cp(theta * (2 ** j), control, target)

    qc.barrier()

    # 3. IQFT con REVERSAL (Crucial para Qiskit)
    # Invertimos el orden para que el bit más significativo sea el de la rotación más grande
    counting_reversed = counting[::-1]
    iqft = build_iqft_circuit(t_qubits, approximation_degree=approximation_degree)
    qc.append(iqft, counting_reversed)

    # 4. Medida
    qc.measure(counting, list(range(t_qubits)))
    return qc

def main():
    parser = argparse.ArgumentParser()
    
    # Rutas automáticas basadas en la ubicación del script
    root_dir = Path(__file__).resolve().parent.parent
    default_csv = root_dir / "experiments" / "results" / "qpe_detailed.csv"
    default_json = root_dir / "experiments" / "results" / "qpe_counts.json"

    parser.add_argument("--t_qubits", type=int, default=6) 
    parser.add_argument("--phases", type=float, nargs="+", default=[0.25, 0.333333])
    parser.add_argument("--m_values", type=int, nargs="+", default=[0, 1, 2, 3])
    parser.add_argument("--out_csv", type=str, default=str(default_csv))
    parser.add_argument("--out_counts", type=str, default=str(default_json))
    args = parser.parse_args()

    # Asegurar que la carpeta results existe
    Path(args.out_csv).parent.mkdir(parents=True, exist_ok=True)

    rows = []
    all_counts = {}

    for phase in args.phases:
        phase_key = f"{phase:.4f}"
        all_counts[phase_key] = {}
        for m in args.m_values:
            print(f"Simulando Fase={phase:.4f}, m={m}...")
            qc = build_qpe_circuit(args.t_qubits, phase, m)
            backend = AerSimulator()
            counts = backend.run(transpile(qc, backend), shots=4096).result().get_counts()
            
            probs = normalize_counts(counts)
            ml_string = max(counts, key=counts.get)
            phase_est = bitstring_to_phase(ml_string)
            
            rows.append({
                "phase_true": phase,
                "m": m,
                "phase_est": phase_est,
                "abs_error": abs(phase_est - phase),
                "prob_peak": probs[ml_string],
                "dispersion": calculate_dispersion(counts, phase)
            })
            all_counts[phase_key][str(m)] = counts

    # Guardar resultados con modos correctos
    with open(args.out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
        
    with open(args.out_counts, "w") as f: 
        json.dump(all_counts, f, indent=2)
        
    print(f"✅ Archivos generados en experiments/results/")

if __name__ == "__main__":
    main()