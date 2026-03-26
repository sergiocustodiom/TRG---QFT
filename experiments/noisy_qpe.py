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
from qiskit_ibm_runtime import QiskitRuntimeService
from qft_engine import build_iqft_circuit

def normalize_counts(counts: Dict[str, int]) -> Dict[str, float]:
    total = sum(counts.values())
    return {k: v / total for k, v in counts.items()}

def bitstring_to_phase(bitstring: str) -> float:
    t = len(bitstring)
    return int(bitstring, 2) / (2 ** t)

def calculate_dispersion(counts: Dict[str, int], true_phase: float) -> float:
    """Calcula la desviación típica de las fases medidas con ruido respecto a la real."""
    total_shots = sum(counts.values())
    variance = 0
    for b, count in counts.items():
        phase_measured = bitstring_to_phase(b)
        # Manejo de circularidad (la fase 0.99 está cerca de 0.0)
        diff = abs(phase_measured - true_phase)
        diff = min(diff, 1 - diff) 
        variance += count * (diff ** 2)
    return math.sqrt(variance / total_shots)

def build_qpe_circuit(t_qubits: int, phase: float, m: int = 0) -> QuantumCircuit:
    n_total = t_qubits + 1
    qc = QuantumCircuit(n_total, t_qubits)
    counting = list(range(t_qubits))
    target = t_qubits

    qc.x(target)
    for q in counting: qc.h(q)

    theta = 2 * math.pi * phase
    for j, control in enumerate(counting):
        qc.cp(theta * (2 ** j), control, target)

    qc.barrier()
    # Bit-reversal para Qiskit
    counting_reversed = counting[::-1]
    iqft = build_iqft_circuit(t_qubits, approximation_degree=m)
    qc.append(iqft, counting_reversed)

    qc.measure(counting, list(range(t_qubits)))
    return qc

def main():
    parser = argparse.ArgumentParser()
    root_dir = Path(__file__).resolve().parent.parent
    
    parser.add_argument("--t_qubits", type=int, default=5)
    parser.add_argument("--backend_name", type=str, default="ibm_fez")
    parser.add_argument("--phases", type=float, nargs="+", default=[0.25, 0.3333])
    parser.add_argument("--m_values", type=int, nargs="+", default=[0, 1, 2, 3])
    parser.add_argument("--out_csv", type=str, default=str(root_dir / "experiments/results/qpe_noise.csv"))
    parser.add_argument("--out_json", type=str, default=str(root_dir / "experiments/results/qpe_noise_counts.json"))
    args = parser.parse_args()

    print(f"📡 Conectando con IBM para obtener modelo de ruido de {args.backend_name}...")
    service = QiskitRuntimeService()
    real_backend = service.backend(args.backend_name)
    noise_model = AerSimulator.from_backend(real_backend)

    results = []
    all_counts = {}

    for phase in args.phases:
        ph_key = f"{phase:.4f}"
        all_counts[ph_key] = {}
        for m in args.m_values:
            print(f"🧪 Simulando con RUIDO: Fase={ph_key}, m={m}...")
            qc = build_qpe_circuit(args.t_qubits, phase, m)
            
            # Transpilar para hardware real (añade SWAPs según conectividad)
            tqc = transpile(qc, real_backend, optimization_level=1)
            
            job = noise_model.run(tqc, shots=4096)
            counts = job.result().get_counts()
            
            probs = normalize_counts(counts)
            ml_string = max(counts, key=counts.get)
            
            results.append({
                "phase_true": phase,
                "m": m,
                "prob_peak": probs[ml_string],
                "phase_est": bitstring_to_phase(ml_string),
                "dispersion": calculate_dispersion(counts, phase),
                "backend": args.backend_name
            })
            all_counts[ph_key][str(m)] = counts

    Path(args.out_csv).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader()
        w.writerows(results)
    with open(args.out_json, "w") as f:
        json.dump(all_counts, f, indent=2)
    print("✅ Experimento con ruido completado.")

if __name__ == "__main__":
    main()