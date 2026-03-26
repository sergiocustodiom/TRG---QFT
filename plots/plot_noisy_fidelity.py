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
            r["success_prob"] = float(r["success_prob"]) # Carga la nueva métrica
            rows.append(r)
    return rows

def plot_state(rows: List[Dict[str, Any]], state_label: str, out_path: Path, title: str):
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
            marker="o",
            linestyle="--",
            label=f"QFT Exacta (m=0)" if m == 0 else f"AQFT (m={m})",
            alpha=0.7
        )

    plt.xlabel("Número de qubits (n)")
    plt.ylabel("Probabilidad de éxito (Test Reversibilidad) [con ruido]")
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
    parser = argparse.ArgumentParser()
    base_dir = Path(__file__).resolve().parent.parent
    default_csv = base_dir / "experiments" / "results" / "noisy_fidelity_qft_vs_aqft.csv"
    default_out = base_dir / "figures" / "noisy_fidelity"
    
    parser.add_argument("--csv", type=str, default=str(default_csv))
    parser.add_argument("--out_dir", type=str, default=str(default_out))
    args = parser.parse_args()

    rows = load_rows(Path(args.csv))
    out_dir = Path(args.out_dir)

    plot_state(rows, "all_ones", out_dir / "prob_exito_noisy_vs_n_all_ones.png", "Reversibilidad con ruido — estado |11…1⟩")
    plot_state(rows, "pattern", out_dir / "prob_exito_noisy_vs_n_pattern_1010.png", "Reversibilidad con ruido — estado patrón |1010…⟩")

if __name__ == "__main__":
    main()