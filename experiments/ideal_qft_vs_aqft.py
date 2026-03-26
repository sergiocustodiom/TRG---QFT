import sys
import os
# Añadimos la raíz al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import argparse
import csv
from pathlib import Path
from typing import Dict, List, Tuple

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, state_fidelity

from qft_engine import build_qft_circuit


# -----------------------------
# Helpers: estados base
# -----------------------------
def bitstring_all_ones(n: int) -> str:
    return "1" * n

def bitstring_pattern_1010(n: int) -> str:
    # "1010..." empezando por 1 en el qubit 0 (LSB)
    return "".join("1" if i % 2 == 0 else "0" for i in range(n))

def prepare_basis_state(qc: QuantumCircuit, bitstring: str) -> None:
    """Prepara |bitstring> aplicando X en los qubits correspondientes."""
    if len(bitstring) != qc.num_qubits:
        raise ValueError("Longitud de bitstring != número de qubits.")
    for i, b in enumerate(bitstring):
        if b == "1":
            qc.x(i)


# -----------------------------
# Ejecución Ideal Cuántica (Statevector)
# -----------------------------
def get_transform_statevector(
    bitstring: str,
    transform: str,
    m: int
) -> Statevector:
    """
    Obtiene el vector de estado cuántico puro tras aplicar QFT o AQFT.
    No hay mediciones, solo matemática exacta.
    """
    n = len(bitstring)
    qc = QuantumCircuit(n, name="main")

    prepare_basis_state(qc, bitstring)

    if transform == "QFT":
        qft = build_qft_circuit(n_qubits=n, approximation_degree=0)
    elif transform == "AQFT":
        qft = build_qft_circuit(n_qubits=n, approximation_degree=m)
    else:
        raise ValueError("transform debe ser 'QFT' o 'AQFT'.")

    qc.append(qft, range(n))
    
    # Extraemos el vector de estado exacto del circuito
    return Statevector(qc)


def build_rows(
    n_min: int,
    n_max: int,
    m_values: List[int],
) -> List[Dict]:
    """
    Calcula la fidelidad cuántica pura entre los estados generados por QFT y AQFT(m).
    """
    rows: List[Dict] = []

    for n in range(n_min, n_max + 1):
        states: List[Tuple[str, str]] = [
            ("all_ones", bitstring_all_ones(n)),
            ("pattern", bitstring_pattern_1010(n)),
        ]

        for state_label, bitstring in states:
            # Baseline: Statevector de la QFT exacta
            sv_qft = get_transform_statevector(
                bitstring=bitstring,
                transform="QFT",
                m=0
            )

            # AQFT(m): Fidelidad cuántica vs QFT
            for m in m_values:
                sv_aqft = get_transform_statevector(
                    bitstring=bitstring,
                    transform="AQFT",
                    m=m
                )

                # Calculamos la fidelidad de estado pura (overlap real)
                fid = state_fidelity(sv_qft, sv_aqft)

                rows.append({
                    "state_label": state_label,
                    "bitstring": bitstring,
                    "n_qubits": n,
                    "m": m,
                    "shots": 0,  # Ya no hay shots porque es matemático
                    "fidelity_ideal": fid,
                })

    return rows


def write_csv(rows: List[Dict], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "state_label",
        "bitstring",
        "n_qubits",
        "m",
        "shots",
        "fidelity_ideal",
    ]
    with out_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="Paso 3: fidelidad cuántica ideal QFT vs AQFT.")
    parser.add_argument("--n_min", type=int, default=2)
    parser.add_argument("--n_max", type=int, default=12)
    parser.add_argument("--m_values", type=int, nargs="+", default=[1, 2, 3, 4])
    
    # Resolutor dinámico de rutas absolutas
    base_dir = Path(__file__).resolve().parent.parent
    default_csv = base_dir / "experiments" / "results" / "ideal_fidelity_qft_vs_aqft.csv"
    
    parser.add_argument("--out_csv", type=str, default=str(default_csv))
    args = parser.parse_args()

    # Generamos los datos
    rows = build_rows(
        n_min=args.n_min,
        n_max=args.n_max,
        m_values=args.m_values,
    )

    out_csv = Path(args.out_csv)
    write_csv(rows, out_csv)

    print(f"✅ CSV generado usando Estado Cuántico Puro: {out_csv.resolve()}")
    print(f"Filas generadas: {len(rows)}")


if __name__ == "__main__":
    main()