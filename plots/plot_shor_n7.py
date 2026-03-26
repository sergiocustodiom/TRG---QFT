import argparse
import csv
from pathlib import Path
from typing import Dict, Any, List
import matplotlib.pyplot as plt

def load_rows(csv_path: Path) -> List[Dict[str, Any]]:
    rows = []
    with csv_path.open("r", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            r["m"] = int(r["m"])
            r["probability"] = float(r["probability"])
            rows.append(r)
    return rows

def plot_distribution(rows, m, out_path, title):
    dist = {r["bitstring"]: r["probability"] for r in rows if r["m"] == m}
    
    t_qubits = next(iter(dist.keys()), "00000")
    t_len = len(t_qubits)
    for i in range(2**t_len):
        b_str = format(i, f'0{t_len}b')
        if b_str not in dist:
            dist[b_str] = 0.0

    xs = sorted(dist.keys(), key=lambda b: int(b, 2))
    ys = [dist[b] for b in xs]

    color_map = {0: "#1f77b4", 1: "#ff7f0e", 2: "#2ca02c", 3: "#d62728", 4: "#9467bd"}
    
    plt.figure(figsize=(12, 5))
    bars = plt.bar(xs, ys, color=color_map.get(m, "teal"), alpha=0.8, edgecolor="black")

    for bar in bars:
        yval = bar.get_height()
        if yval > 0.05:
            plt.text(bar.get_x() + bar.get_width()/2, yval + 0.01, f"{yval:.2f}", ha='center', va='bottom', fontsize=8)

    plt.xlabel("Resultado medido (Registro de Conteo)", fontsize=12)
    plt.ylabel("Probabilidad", fontsize=12)
    plt.title(title, fontsize=14, pad=15)
    plt.xticks(rotation=90, fontsize=9)
    plt.ylim(0, max(ys) + 0.1)
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=300)
    plt.close()

def main():
    parser = argparse.ArgumentParser()
    root_dir = Path(__file__).resolve().parent.parent
    default_csv = root_dir / "experiments" / "results" / "shor_n7.csv"
    default_out = root_dir / "figures" / "shor_n7"
    
    parser.add_argument("--csv", type=str, default=str(default_csv))
    parser.add_argument("--out_dir", type=str, default=str(default_out))
    args = parser.parse_args()

    rows = load_rows(Path(args.csv))
    out_dir = Path(args.out_dir)

    for m in sorted(set(r["m"] for r in rows)):
        label = "QFT exacta (m=0)" if m == 0 else f"AQFT (m={m})"
        plot_distribution(rows, m, out_dir / f"shor_n7_m{m}.png", f"Shor 'Fallo' (N=7, a=2) — {label}")
        print(f"✅ Gráfica generada para m={m}")

if __name__ == "__main__":
    main()