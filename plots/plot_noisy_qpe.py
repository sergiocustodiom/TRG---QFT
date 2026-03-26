import argparse
import json
import csv
from pathlib import Path
import matplotlib.pyplot as plt

def label_from_m(m: int) -> str:
    return "QFT (Exacta)" if m == 0 else f"AQFT (m={m})"

def plot_leakage_noise(all_data, phase_str, out_dir):
    m_dict = all_data[phase_str]
    plt.figure(figsize=(14, 8))
    
    styles = {
        "0": {"color": "#1f77b4", "marker": "o", "ms": 10, "ls": "-"},
        "1": {"color": "#ff7f0e", "marker": "s", "ms": 9,  "ls": "--"},
        "2": {"color": "#2ca02c", "marker": "^", "ms": 11, "ls": "-."},
        "3": {"color": "#d62728", "marker": "*", "ms": 13, "ls": ":"}
    }

    for m_str in sorted(m_dict.keys(), key=int):
        counts = m_dict[m_str]
        total = sum(counts.values())
        t_qubits = len(next(iter(counts.keys())))
        
        sorted_data = sorted([(int(b, 2)/(2**t_qubits), v/total) for b, v in counts.items()])
        x, y = zip(*sorted_data)
        
        st = styles.get(m_str, {"color": None, "marker": "x", "ms": 8, "ls": "-"})
        # Añadimos un pequeño offset visual
        offset = (int(m_str) - 1.5) * 0.002
        x_off = [val + offset for val in x]

        plt.plot(x_off, y, label=label_from_m(int(m_str)), 
                 color=st["color"], marker=st["marker"], markersize=st["ms"], 
                 linestyle=st["ls"], linewidth=2.5, markeredgecolor="white")
        plt.fill_between(x_off, y, alpha=0.07, color=st["color"])

    plt.axvline(float(phase_str), color="black", linestyle="-", linewidth=2, alpha=0.6, label="Fase Real")
    plt.title(f"Impacto del Ruido Hardware (IBM Fez)\nPhase Leakage - Fase Objetivo = {phase_str}", fontsize=16, pad=20)
    plt.xlabel("Fase estimada ($k / 2^n$)", fontsize=14)
    plt.ylabel("Probabilidad $P(k)$", fontsize=14)
    plt.legend(fontsize=12, shadow=True)
    plt.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    
    save_path = out_dir / f"noise_leakage_{phase_str.replace('.','p')}.png"
    plt.savefig(save_path, dpi=300)
    plt.close()

def plot_dispersion_noise(csv_rows, phase_val, out_dir):
    phase_str = f"{phase_val:.4f}"
    filtered = sorted([r for r in csv_rows if abs(float(r["phase_true"]) - phase_val) < 1e-6], key=lambda x: int(x["m"]))
    
    labels = [label_from_m(int(r["m"])) for r in filtered]
    disp_vals = [float(r["dispersion"]) for r in filtered]

    plt.figure(figsize=(10, 6))
    bars = plt.bar(labels, disp_vals, color="#cd5c5c", alpha=0.8, edgecolor="black")

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + (max(disp_vals)*0.02), 
                 f"{yval:.4f}", ha='center', va='bottom', fontsize=12, fontweight='bold')

    plt.ylabel("Incertidumbre (Desviación Típica)", fontsize=13)
    plt.title(f"Dispersión con Ruido Hardware vs Aproximación\n(Fase={phase_str})", fontsize=15, pad=15)
    plt.grid(axis="y", linestyle=":", alpha=0.6)
    plt.tight_layout()

    save_path = out_dir / f"noise_dispersion_{phase_str.replace('.','p')}.png"
    plt.savefig(save_path, dpi=300)
    plt.close()

def main():
    parser = argparse.ArgumentParser()
    root_dir = Path(__file__).resolve().parent.parent
    parser.add_argument("--csv", type=str, default=str(root_dir / "experiments/results/qpe_noise.csv"))
    parser.add_argument("--json", type=str, default=str(root_dir / "experiments/results/qpe_noise_counts.json"))
    parser.add_argument("--out_dir", type=str, default=str(root_dir / "figures/qpe_noise"))
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(args.json, "r") as f:
        all_counts = json.load(f)
    
    csv_rows = []
    with open(args.csv, "r") as f:
        csv_rows = list(csv.DictReader(f))

    phases = sorted([float(ph) for ph in all_counts.keys()])
    for ph in phases:
        ph_str = f"{ph:.4f}"
        plot_leakage_noise(all_counts, ph_str, out_dir)
        plot_dispersion_noise(csv_rows, ph, out_dir)
    
    print(f"✅ Todas las gráficas (Histogramas + Dispersión) generadas en {out_dir}")

if __name__ == "__main__":
    main()