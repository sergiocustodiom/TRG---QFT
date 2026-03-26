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
            r["t_qubits"] = int(r["t_qubits"])
            r["m"] = int(r["m"])
            r["shots"] = int(r["shots"])
            r["probability"] = float(r["probability"])
            rows.append(r)
    return rows

def plot_distribution(rows, m, out_path, title):
    dist = {r["bitstring"]: r["probability"] for r in rows if r["m"] == m}
    
    # Rellenamos los estados vacíos con 0 para que el eje X sea igual en todas las gráficas
    t_qubits = next(iter(dist.keys()), "0000")
    t_len = len(t_qubits)
    for i in range(2**t_len):
        b_str = format(i, f'0{t_len}b')
        if b_str not in dist:
            dist[b_str] = 0.0

    # Ordenar por valor binario
    xs = sorted(dist.keys(), key=lambda b: int(b, 2))
    ys = [dist[b] for b in xs]

    # Paleta de colores para diferenciar las gráficas de un vistazo
    color_map = {0: "#1f77b4", 1: "#ff7f0e", 2: "#2ca02c", 3: "#d62728"}
    color = color_map.get(m, "teal")

    plt.figure(figsize=(10, 5))
    bars = plt.bar(xs, ys, color=color, alpha=0.8, edgecolor="black")

    # Añadir valores sobre las barras principales
    for bar in bars:
        yval = bar.get_height()
        if yval > 0.05: # Solo pintamos el número si el pico es visible
            plt.text(bar.get_x() + bar.get_width()/2, yval + 0.02, f"{yval:.2f}", ha='center', va='bottom', fontsize=9)

    plt.xlabel("Resultado medido (Registro de Conteo)", fontsize=12)
    plt.ylabel("Probabilidad", fontsize=12)
    plt.title(title, fontsize=14, pad=15)
    plt.xticks(rotation=90, fontsize=10)
    plt.ylim(0, 1.05)
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"✅ Gráfica guardada: {out_path.name}")

def main():
    parser = argparse.ArgumentParser()
    
    root_dir = Path(__file__).resolve().parent.parent
    default_csv = root_dir / "experiments" / "results" / "shor_ideal.csv"
    default_out = root_dir / "figures" / "shor_ideal"
    
    parser.add_argument("--csv", type=str, default=str(default_csv))
    parser.add_argument("--out_dir", type=str, default=str(default_out))
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"❌ ERROR: Ejecuta el experimento de Shor primero. No encuentro {csv_path.name}")
        return

    rows = load_rows(csv_path)
    out_dir = Path(args.out_dir)

    ms = sorted(set(r["m"] for r in rows))

    for m in ms:
        label = "QFT exacta (m=0)" if m == 0 else f"AQFT (m={m})"
        plot_distribution(
            rows, m,
            out_path=out_dir / f"shor_distribution_m{m}.png",
            title=f"Shor Ideal (N=15, a=2) — {label}",
        )

if __name__ == "__main__":
    main()