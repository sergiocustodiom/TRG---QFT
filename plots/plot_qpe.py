import argparse
import csv
import json
from pathlib import Path
import matplotlib.pyplot as plt

# ======================================================
# Helpers
# ======================================================
def load_data(csv_path):
    with open(csv_path, "r") as f:
        return list(csv.DictReader(f))

def label_from_m(m: int) -> str:
    return "QFT (Exacta)" if m == 0 else f"AQFT (m={m})"

def ensure_labels(rows):
    for r in rows:
        if "label" not in r or r["label"] == "":
            r["label"] = label_from_m(int(r["m"]))
    return rows

# ======================================================
# Plot 1: Leakage (SÍMBOLOS MÁS GRANDES Y LEGIBLES)
# ======================================================
def plot_leakage_histograms(counts_json, phase_str, out_dir):
    with open(counts_json, "r") as f:
        data = json.load(f)[phase_str]

    # Aumentamos el tamaño de la figura para que respire
    plt.figure(figsize=(14, 8))

    # Estilos con símbolos grandes y distintos
    styles = {
        0: {"color": "#1f77b4", "marker": "o", "ls": "-",  "ms": 10}, # Círculo grande
        1: {"color": "#ff7f0e", "marker": "s", "ls": "--", "ms": 9},  # Cuadrado
        2: {"color": "#2ca02c", "marker": "^", "ls": "-.", "ms": 11}, # Triángulo
        3: {"color": "#d62728", "marker": "*", "ls": ":",  "ms": 13}, # Estrella
    }

    # Dibujamos de mayor a menor m para que los picos no se tapen totalmente
    for m_str in sorted(data.keys(), key=int, reverse=True):
        m = int(m_str)
        counts = data[m_str]
        style = styles.get(m, {"color": None, "marker": ".", "ls": "-", "ms": 8})
        
        total = sum(counts.values())
        t_qubits = len(next(iter(counts.keys())))

        # Extraer datos
        sorted_phases = sorted([(int(b, 2) / (2 ** t_qubits), v / total) for b, v in counts.items()])
        x, y = zip(*sorted_phases)
        
        # Jitter (desplazamiento) para evitar solapamiento exacto
        offset = (m - 1.5) * 0.002 
        x_offset = [val + offset for val in x]

        plt.plot(
            x_offset,
            y,
            label=label_from_m(m),
            color=style["color"],
            marker=style["marker"],
            linestyle=style["ls"],
            markersize=style["ms"], # <--- Símbolos mucho más grandes
            markeredgecolor="white", # Borde blanco para resaltar si se solapan
            markeredgewidth=0.5,
            alpha=0.9,
            linewidth=2.5 # Líneas más gruesas
        )

        plt.fill_between(x_offset, y, alpha=0.07, color=style["color"])

    # Línea de fase real más visible
    plt.axvline(
        float(phase_str),
        color="black",
        linestyle="-",
        linewidth=2,
        alpha=0.6,
        label="Fase real esperada"
    )

    # Mejoras estéticas y de escala
    plt.xlabel("Fase estimada ($k / 2^n$)", fontsize=14, fontweight='bold')
    plt.ylabel("Probabilidad $P(k)$", fontsize=14, fontweight='bold')
    plt.title(f"Distribución de Probabilidad (Phase Leakage)\nFase Objetivo = {phase_str}", fontsize=16, pad=20)
    
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.legend(fontsize=12, frameon=True, loc='upper right', shadow=True)
    plt.grid(axis="y", linestyle="--", alpha=0.4)
    plt.xlim(-0.02, 1.02)
    plt.tight_layout()

    out_path = out_dir / f"leakage_phase_{phase_str.replace('.', 'p')}.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"✅ Histograma (símbolos grandes) guardado: {out_path.name}")


# ======================================================
# Plot 2: Dispersión
# ======================================================
def plot_dispersion(rows, phase_value, out_dir):
    phase_str = f"{phase_value:.4f}"
    filtered = sorted([r for r in rows if abs(float(r["phase_true"]) - phase_value) < 1e-9], key=lambda r: int(r["m"]))
    
    labels = [r["label"] for r in filtered]
    disp_vals = [float(r["dispersion"]) for r in filtered]

    plt.figure(figsize=(10, 6))
    bars = plt.bar(labels, disp_vals, color="#4682b4", alpha=0.85, edgecolor="black", linewidth=1)

    # Valores numéricos más grandes sobre las barras
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + (max(disp_vals)*0.02), 
                 f"{yval:.4f}", ha='center', va='bottom', fontsize=12, fontweight='bold')

    plt.xlabel("Algoritmo", fontsize=13)
    plt.ylabel("Incertidumbre (Desviación Típica)", fontsize=13)
    plt.title(f"Dispersión de la Medida vs Grado de Aproximación\n(Fase={phase_str})", fontsize=15, pad=15)
    plt.xticks(fontsize=11)
    plt.yticks(fontsize=11)
    plt.grid(axis="y", linestyle=":", alpha=0.6)
    plt.tight_layout()

    disp_path = out_dir / f"dispersion_ph_{phase_str.replace('.', 'p')}.png"
    plt.savefig(disp_path, dpi=300)
    plt.close()
    print(f"✅ Dispersión guardada: {disp_path.name}")


# ======================================================
# Main
# ======================================================
def main():
    parser = argparse.ArgumentParser()
    root_dir = Path(__file__).resolve().parent.parent
    
    default_csv = root_dir / "experiments" / "results" / "qpe_detailed.csv"
    default_json = root_dir / "experiments" / "results" / "qpe_counts.json"
    default_out = root_dir / "figures" / "qpe_analysis"

    parser.add_argument("--csv", type=str, default=str(default_csv))
    parser.add_argument("--json", type=str, default=str(default_json))
    parser.add_argument("--out_dir", type=str, default=str(default_out))
    args = parser.parse_args()

    csv_path, json_path, out_dir = Path(args.csv), Path(args.json), Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not csv_path.exists() or not json_path.exists():
        print("❌ Error: Ejecuta primero el experimento para generar los datos.")
        return

    rows = ensure_labels(load_data(csv_path))
    phases = sorted(list(set(float(r["phase_true"]) for r in rows)))

    for ph in phases:
        ph_str = f"{ph:.4f}"
        plot_leakage_histograms(json_path, ph_str, out_dir)
        plot_dispersion(rows, ph, out_dir)

if __name__ == "__main__":
    main()