import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, Any, List

import matplotlib.pyplot as plt


def load_rows(csv_path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with csv_path.open("r", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            r["n_qubits"] = int(r["n_qubits"])
            r["m"] = int(r["m"])
            r["shots"] = int(r["shots"])
            r["fidelity_ideal"] = float(r["fidelity_ideal"])
            rows.append(r)
    return rows


def plot_state(rows: List[Dict[str, Any]], state_label: str, out_path: Path, title: str):
    # m -> list of (n, fid)
    series = defaultdict(list)
    for r in rows:
        if r["state_label"] != state_label:
            continue
        series[r["m"]].append((r["n_qubits"], r["fidelity_ideal"]))

    for m in series:
        series[m].sort(key=lambda x: x[0])

    plt.figure()
    for m in sorted(series.keys()):
        pts = series[m]
        # === AÑADIDO ALPHA=0.6 PARA VER LÍNEAS SOLAPADAS ===
        plt.plot(
            [n for n, _ in pts], 
            [f for _, f in pts], 
            marker="o", 
            linestyle="--", 
            label=f"AQFT (m={m})",
            alpha=0.6  
        )

    plt.xlabel("Número de qubits (n)")
    plt.ylabel("Fidelidad cuántica (Statevector) [ideal]")
    plt.title(title)
    plt.grid(True)
    plt.ylim(0.0, 1.02)
    plt.legend()
    plt.tight_layout()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Guardada: {out_path.resolve()}")


def main():
    parser = argparse.ArgumentParser(description="Plots Paso 3: fidelidad ideal QFT vs AQFT.")
    
    # === RUTAS ABSOLUTAS AUTOMÁTICAS ===
    # Path(__file__) es este script. .parent es 'plots'. .parent.parent es 'Codigo'.
    base_dir = Path(__file__).resolve().parent.parent
    
    # Buscamos el CSV en la carpeta experiments/results
    default_csv = base_dir / "experiments" / "results" / "ideal_fidelity_qft_vs_aqft.csv"
    
    # Guardamos las imágenes en la carpeta figures de la raíz
    default_out = base_dir / "figures" / "ideal_fidelity"
    # ===================================

    parser.add_argument("--csv", type=str, default=str(default_csv))
    parser.add_argument("--out_dir", type=str, default=str(default_out))
    args = parser.parse_args()

    csv_path = Path(args.csv)
    out_dir = Path(args.out_dir)

    # Chivato por si no encuentra el archivo CSV
    if not csv_path.exists():
        print(f"❌ ERROR: No encuentro el archivo CSV en:\n   {csv_path}")
        return

    rows = load_rows(csv_path)

    plot_state(
        rows,
        state_label="all_ones",
        out_path=out_dir / "fidelity_vs_n_all_ones.png",
        title="Fidelidad ideal (AQFT vs QFT) — estado |11…1⟩",
    )

    plot_state(
        rows,
        state_label="pattern",
        out_path=out_dir / "fidelity_vs_n_pattern_1010.png",
        title="Fidelidad ideal (AQFT vs QFT) — estado patrón |1010…⟩",
    )


if __name__ == "__main__":
    main()