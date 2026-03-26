import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, Any, List
import matplotlib.pyplot as plt

def load_rows(csv_path: Path) -> List[Dict[str, Any]]:
    rows = []
    with csv_path.open("r", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            r["n_qubits"] = int(r["n_qubits"])
            r["m"] = int(r["m"])
            r["shots"] = int(r["shots"])
            r["success_prob"] = float(r["success_prob"])
            r["noise_label"] = r["noise_label"]
            rows.append(r)
    return rows

def plot_state(rows: List[Dict[str, Any]], state_label: str, out_path: Path, title: str, backend_name: str):
    series = defaultdict(list)
    for r in rows:
        if r["state_label"] != state_label:
            continue
        series[r["m"]].append((r["n_qubits"], r["success_prob"]))

    for m in series:
        series[m].sort(key=lambda x: x[0])

    plt.figure()
    for m in sorted(series.keys()):
        pts = series[m]
        plt.plot(
            [n for n, _ in pts],
            [f for _, f in pts],
            marker="s", # Usamos cuadrados (s=square) para diferenciar de las otras gráficas
            linestyle="-", 
            label=f"QFT Exacta (m=0)" if m == 0 else f"AQFT (m={m})",
            alpha=0.7
        )

    plt.xlabel("Número de qubits (n)")
    plt.ylabel(f"Probabilidad de éxito [{backend_name}]")
    plt.title(title)
    plt.grid(True, linestyle=":", alpha=0.6) # Rejilla más suave
    plt.ylim(0.0, 1.02)
    plt.legend()
    plt.tight_layout()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Guardada: {out_path.resolve()}")

def main():
    parser = argparse.ArgumentParser()
    base_dir = Path(__file__).resolve().parent.parent
    default_csv = base_dir / "experiments" / "results" / "noisy_fidelity_qft_vs_aqft_ibm.csv"
    default_out = base_dir / "figures" / "noisy_ibm" # Carpeta separada para IBM
    
    parser.add_argument("--csv", type=str, default=str(default_csv))
    parser.add_argument("--out_dir", type=str, default=str(default_out))
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"❌ ERROR: No encuentro el CSV en: {csv_path}")
        return

    rows = load_rows(csv_path)
    out_dir = Path(args.out_dir)

    # Extraemos el nombre del backend para ponerlo en el título
    backend_name = rows[0]["noise_label"] if rows else "ibm_hardware"

    plot_state(
        rows, 
        "all_ones", 
        out_dir / f"prob_exito_{backend_name}_all_ones.png", 
        f"Reversibilidad Hardware IBM ({backend_name}) — |11…1⟩",
        backend_name
    )
    plot_state(
        rows, 
        "pattern", 
        out_dir / f"prob_exito_{backend_name}_pattern_1010.png", 
        f"Reversibilidad Hardware IBM ({backend_name}) — |1010…⟩",
        backend_name
    )

if __name__ == "__main__":
    main()