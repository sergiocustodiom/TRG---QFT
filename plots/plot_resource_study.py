import argparse
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


# ======================================================
# Helpers
# ======================================================
def label_from_row(transform: str, m: int) -> str:
    if transform == "QFT":
        return "QFT"
    return f"AQFT (m={m})"


def build_series_labels(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["label"] = df.apply(lambda row: label_from_row(row["transform"], row["m"]), axis=1)
    return df


def get_style_map():
    """
    Estilo visual para cada curva:
    - marker
    - linestyle
    - linewidth
    """
    return {
        "QFT":         {"marker": "o", "linestyle": "-",  "linewidth": 2},
        "AQFT (m=1)":  {"marker": "s", "linestyle": "--", "linewidth": 2},
        "AQFT (m=2)":  {"marker": "^", "linestyle": "-.", "linewidth": 2},
        "AQFT (m=3)":  {"marker": "D", "linestyle": ":",  "linewidth": 2.2},
        "AQFT (m=4)":  {"marker": "v", "linestyle": "-",  "linewidth": 2},
    }


# ======================================================
# Plots
# ======================================================
def plot_gate_count(df: pd.DataFrame, out_path: Path) -> None:
    plt.figure(figsize=(10, 6))

    ordered_labels = ["QFT", "AQFT (m=1)", "AQFT (m=2)", "AQFT (m=3)", "AQFT (m=4)"]
    style_map = get_style_map()

    for label in ordered_labels:
        # Filtramos por etiqueta
        subset = df[df["label"] == label].sort_values("n_qubits")
        
        # Si no hay datos para esta etiqueta, saltamos
        if subset.empty:
            continue
            
        style = style_map[label]

        plt.plot(
            subset["n_qubits"],
            subset["size_logical"], # <--- ACTUALIZADO a la nueva columna
            label=label,
            marker=style["marker"],
            linestyle=style["linestyle"],
            linewidth=style["linewidth"],
            markersize=8,
            alpha=0.7
        )

    plt.xlabel("Número de qubits")
    plt.ylabel("Número total de puertas lógicas")
    plt.title("Número de puertas vs número de qubits")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()


def plot_depth(df: pd.DataFrame, out_path: Path) -> None:
    plt.figure(figsize=(10, 6))

    ordered_labels = ["QFT", "AQFT (m=1)", "AQFT (m=2)", "AQFT (m=3)", "AQFT (m=4)"]
    style_map = get_style_map()

    for label in ordered_labels:
        subset = df[df["label"] == label].sort_values("n_qubits")
        
        if subset.empty:
            continue
            
        style = style_map[label]

        plt.plot(
            subset["n_qubits"],
            subset["depth_logical"], # <--- ACTUALIZADO a la nueva columna
            label=label,
            marker=style["marker"],
            linestyle=style["linestyle"],
            linewidth=style["linewidth"],
            markersize=8,
            alpha=0.7
        )

    plt.xlabel("Número de qubits")
    plt.ylabel("Profundidad lógica del circuito")
    plt.title("Profundidad vs número de qubits")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()


# ======================================================
# Main
# ======================================================
def main():
    parser = argparse.ArgumentParser(
        description="Plots de recursos ideales para QFT y AQFT."
    )

    base_dir = Path(__file__).resolve().parent.parent
    # <--- ACTUALIZADO: Nombre correcto del archivo CSV que generamos ahora
    default_csv = base_dir / "experiments" / "results" / "resource_study_combined.csv" 
    default_fig_dir = base_dir / "figures" / "resource_usage_qft_aqft"

    parser.add_argument("--in_csv", type=str, default=str(default_csv))
    parser.add_argument("--out_dir", type=str, default=str(default_fig_dir))

    args = parser.parse_args()

    in_csv = Path(args.in_csv)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    if not in_csv.exists():
        print(f"❌ ERROR: No se encuentra el archivo en {in_csv}")
        print("Asegúrate de haber ejecutado primero 'python resource_study_qft.py'")
        return

    df = pd.read_csv(in_csv)
    df = build_series_labels(df)

    plot_gate_count(df, out_dir / "gate_count_vs_n_qubits.png")
    plot_depth(df, out_dir / "depth_vs_n_qubits.png")

    print(f"✅ Figuras generadas en: {out_dir.resolve()}")
    print(f" - {out_dir / 'gate_count_vs_n_qubits.png'}")
    print(f" - {out_dir / 'depth_vs_n_qubits.png'}")


if __name__ == "__main__":
    main()