import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import argparse
import csv
from pathlib import Path
from typing import Dict, Any, List

from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService
from qft_engine import build_qft_circuit

def summarize_logical_resources(qc: QuantumCircuit) -> Dict[str, Any]:
    """Extrae métricas lógicas (sin transpilar)."""
    ops = qc.count_ops()
    num_1q = 0
    num_2q = 0
    for inst in qc.data:
        nq = len(inst.qubits)
        if nq == 1: num_1q += 1
        elif nq == 2: num_2q += 1

    return {
        "depth_logical": qc.depth(),
        "size_logical": qc.size(),
        "num_1q_logical": num_1q,
        "num_2q_logical": num_2q,
        "num_h_logical": int(ops.get("h", 0)),
        "num_cp_logical": int(ops.get("cp", 0)),
    }

def summarize_transpiled_resources(qc: QuantumCircuit, backend) -> Dict[str, Any]:
    """Extrae métricas físicas tras transpilar para un hardware real."""
    # Añadimos medidas para que la transpilación sea realista
    qc_m = qc.copy()
    qc_m.measure_all()
    
    # Transpilación nivel 1 (estándar)
    tqc = transpile(qc_m, backend=backend, optimization_level=1, seed_transpiler=123)
    
    ops = tqc.count_ops()
    # En IBM las puertas de 2Q suelen ser 'cx', 'ecr' o 'cz'
    num_2q_phys = ops.get('cx', 0) + ops.get('ecr', 0) + ops.get('cz', 0)
    
    return {
        "depth_phys": tqc.depth(),
        "size_phys": tqc.size(),
        "num_2q_phys": num_2q_phys
    }

def build_rows(n_min: int, n_max: int, m_values: List[int], backend_name: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    
    print(f"🔄 Conectando a IBM para obtener el backend: {backend_name}...")
    service = QiskitRuntimeService()
    backend = service.backend(backend_name)

    for n in range(n_min, n_max + 1):
        print(f"  Analizando n={n} qubits...")
        
        # --- Caso QFT exacta (m=0) ---
        qc_qft = build_qft_circuit(n_qubits=n, approximation_degree=0)
        res_log = summarize_logical_resources(qc_qft)
        res_phys = summarize_transpiled_resources(qc_qft, backend)
        
        rows.append({
            "transform": "QFT", "n_qubits": n, "m": 0, "backend": backend_name,
            **res_log, **res_phys
        })

        # --- Casos AQFT(m) ---
        for m in m_values:
            qc_aqft = build_qft_circuit(n_qubits=n, approximation_degree=m)
            res_log_aq = summarize_logical_resources(qc_aqft)
            res_phys_aq = summarize_transpiled_resources(qc_aqft, backend)
            
            rows.append({
                "transform": "AQFT", "n_qubits": n, "m": m, "backend": backend_name,
                **res_log_aq, **res_phys_aq
            })

    return rows

def write_csv(rows: List[Dict[str, Any]], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with out_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def main():
    parser = argparse.ArgumentParser(description="Estudio Híbrido de Recursos (Lógico + Físico).")
    parser.add_argument("--backend", type=str, default="ibm_fez")
    parser.add_argument("--n_min", type=int, default=2)
    parser.add_argument("--n_max", type=int, default=8) # Reducimos a 8 para hardware real
    parser.add_argument("--m_values", type=int, nargs="+", default=[1, 2, 3, 4])
    
    base_dir = Path(__file__).resolve().parent.parent
    default_csv = base_dir / "experiments" / "results" / "resource_study_combined.csv"
    parser.add_argument("--out_csv", type=str, default=str(default_csv))
    args = parser.parse_args()

    rows = build_rows(args.n_min, args.n_max, args.m_values, args.backend)
    write_csv(rows, Path(args.out_csv))

    print(f"✅ CSV híbrido generado: {Path(args.out_csv).resolve()}")

if __name__ == "__main__":
    main()