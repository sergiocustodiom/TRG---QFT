# validate_qft_iqft.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from qiskit import QuantumCircuit, transpile 
from qiskit_aer import AerSimulator
from qiskit import QuantumCircuit, transpile # QuantumCircuit construir circuitos, transpile adpata el circuito al backend (ideal)
from qiskit_aer import AerSimulator # Simulador ideal de Qiskit Aer

from qft_engine import (
    build_qft_circuit,
    build_iqft_circuit,
)

# Funciones auxiliares

def prepare_basis_state(qc: QuantumCircuit, bitstring: str):
    """
    Prepara el estado base |bitstring> en el circuito.

    Convención Qiskit (little-endian):
    - bitstring[0] se aplica al qubit 0 (LSB).
    """
    if len(bitstring) != qc.num_qubits:
        raise ValueError(
            "La longitud del bitstring no coincide con el número de qubits."
        )

    # Si es '1', aplicar una puerta X para poner el qubit en |1>
    for i, b in enumerate(bitstring):
        if b == "1":
            qc.x(i)


def run_validation(
    bitstring: str,
    shots: int = 2048,
):
    """
    Ejecuta la validación QFT -> IQFT sobre |bitstring>.

    Devuelve el diccionario de counts.
    """
    n_qubits = len(bitstring)

    # Circuito completo
    qc = QuantumCircuit(n_qubits, n_qubits)

    # 1) Preparar |x>
    prepare_basis_state(qc, bitstring)

    # 2) Aplicar QFT
    qc.append(
        build_qft_circuit(n_qubits),
        range(n_qubits),
    )

    # 3) Aplicar IQFT
    qc.append(
        build_iqft_circuit(n_qubits),
        range(n_qubits),
    )

    # 4) Medición
    qc.measure(range(n_qubits), range(n_qubits))

    # Simulación ideal
    backend = AerSimulator()
    tqc = transpile(qc, backend)
    result = backend.run(tqc, shots=shots).result()
    counts = result.get_counts()

    return counts


if __name__ == "__main__":
    # ==========================
    # Parámetros del experimento
    # ==========================
    BITSTRING = "00101011"   # estado lógico inicial |x> se puede cambiar para comprobar otros casos.
    SHOTS = 2048

    counts = run_validation(BITSTRING, shots=SHOTS)

    print(f"=== Validación QFT → IQFT para |{BITSTRING}> ===\n")

    print("Distribución de resultados:")
    for k, v in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {k} : {v}")

    most_likely = max(counts, key=counts.get)
    prob = counts[most_likely] / SHOTS

    # En Qiskit, el bitstring medido está en orden little-endian
    expected = BITSTRING[::-1]

    print("\nResultado más probable:")
    print(f"  bitstring medido (little-endian) : {most_likely}")
    print(f"  probabilidad                     : {prob:.4f}")

    print("\nComparación:")
    print(f"  estado lógico inicial : |{BITSTRING}>")
    print(f"  estado esperado      : {expected}")

    if most_likely == expected:
        print("\n✅ VALIDACIÓN CORRECTA: QFT seguida de IQFT recupera el estado original "
              "(teniendo en cuenta el orden little-endian de Qiskit).")
    else:
        print("\n❌ ERROR: la validación ha fallado.")
