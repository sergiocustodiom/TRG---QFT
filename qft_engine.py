# qft_engine.py

from __future__ import annotations

from math import pi
from qiskit import QuantumCircuit
from qiskit.circuit.library import PhaseGate


def _controlled_rotation(k: int, inverse: bool = False):
    """
    Devuelve una puerta CR_k (rotación de fase controlada)
    con etiqueta explícita para visualización.

    Parámetros
    ----------
    k : int
        Índice de la rotación (R_k).

    inverse : bool
        Si True, devuelve la rotación inversa (-angle).

    Devuelve
    --------
    Gate
        Puerta CR_k o CR_k^\dagger con etiqueta.
    """
    angle = pi / (2 ** (k - 1))
    if inverse:
        angle = -angle

    gate = PhaseGate(angle)
    controlled_gate = gate.control(1)

    # Etiqueta visual
    controlled_gate.label = f"CR_{k}" if not inverse else f"CR_{k}†"

    return controlled_gate

# Construcción de circuitos QFT y AQFT direcotos
def build_qft_circuit(
    n_qubits: int, # Número de qubits que queremos en el circuito 
    approximation_degree: int = 0, # Grado de aproximación (0 para QFT exacta) (> 0 para AQFT)
) -> QuantumCircuit:
    """
    Construye un circuito de QFT exacta o aproximada (AQFT).
    """
    if n_qubits < 1:
        raise ValueError("n_qubits debe ser >= 1.")
    if approximation_degree < 0:
        raise ValueError("approximation_degree debe ser >= 0.")

    name = "QFT" if approximation_degree == 0 else f"AQFT(m={approximation_degree})"
    qc = QuantumCircuit(n_qubits, name=name)

    # Construcción de la QFT
    for target in range(n_qubits):
        qc.h(target) # Aplicar la puerta Hadamard al qubit objetivo

        for control in range(target + 1, n_qubits): # Aplicar las rotaciones controladas
            k = control - target + 1
            if approximation_degree > 0 and k > approximation_degree:
                continue

            crk = _controlled_rotation(k)
            qc.append(crk, [control, target])

    # SWAPs finales
    for i in range(n_qubits // 2):
        qc.swap(i, n_qubits - 1 - i)

    return qc

# Construcción de circuitos IQFT y AIQFT inversos
def build_iqft_circuit(
    n_qubits: int, # Número de qubits que queremos en el circuito
    approximation_degree: int = 0, # Grado de aproximación (0 para IQFT exacta) (> 0 para AIQFT)
) -> QuantumCircuit:
    """
    Construye el circuito inverso de la QFT (IQFT) o AQFT inversa.
    """
    if n_qubits < 1:
        raise ValueError("n_qubits debe ser >= 1.")
    if approximation_degree < 0:
        raise ValueError("approximation_degree debe ser >= 0.")

    name = "IQFT" if approximation_degree == 0 else f"AIQFT(m={approximation_degree})"
    qc = QuantumCircuit(n_qubits, name=name)

    # SWAPs iniciales
    for i in range(n_qubits // 2):
        qc.swap(i, n_qubits - 1 - i)

    # Construcción inversa
    for target in reversed(range(n_qubits)):
        for control in reversed(range(target + 1, n_qubits)):
            k = control - target + 1
            if approximation_degree > 0 and k > approximation_degree:
                continue

            crk_inv = _controlled_rotation(k, inverse=True)
            qc.append(crk_inv, [control, target])

        qc.h(target)

    return qc
