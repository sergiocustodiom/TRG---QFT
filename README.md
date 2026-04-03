# Análisis de Rendimiento de la Transformada de Fourier Cuántica Aproximada (AQFT)

Este repositorio contiene el código fuente, los resultados experimentales y las figuras generadas para el Trabajo de Fin de Grado (TFG) sobre la viabilidad de la Transformada de Fourier Cuántica Aproximada (AQFT) en entornos ideales y ruidosos (NISQ).

El objetivo principal es cuantificar el equilibrio entre la reducción de recursos físicos (número de puertas y profundidad) y la pérdida de fidelidad o precisión matemática al aplicar la aproximación a diferentes algoritmos.

---

## 📂 Estructura del Proyecto

El código está dividido en módulos según el experimento realizado. Todos los resultados y gráficas se generan automáticamente en las carpetas `experiments/results/` y `figures/`.

### 1. Motor Cuántico (Core)
* `qft_engine.py`: Módulo principal que contiene la lógica para construir dinámicamente los circuitos de la QFT exacta y la AQFT (con parámetro de aproximación $m$), así como sus respectivas inversas (IQFT).

### 2. Análisis de Fidelidad Cuántica
* `ideal_qft_vs_aqft.py` / `plot_ideal_fidelity.py`: Análisis de la pérdida de precisión matemática pura (mediante *Statevector*) al aplicar distintos grados de aproximación sobre estados de alta y baja energía.
* `noisy_qft_vs_aqft.py` / `plot_noisy_fidelity.py`: Test del eco (reversibilidad) aplicando modelos de ruido sintético (despolarización y *readout*).
* `noisy_qft_vs_aqft_ibm.py` / `plot_noisy_ibm_fidelity.py`: Validación del Test del Eco utilizando el perfil de ruido real del hardware de IBM (`ibm_fez`).

### 3. Análisis de Recursos Físicos
* `resource_study_qft.py` / `plot_resource_study.py`: Estudio híbrido que cuantifica la reducción teórica y real en el conteo de puertas lógicas y la profundidad del circuito transpilado.

### 4. Estimación de Fase Cuántica (QPE)
* `qpe2.py`: Ejecución de la QPE en simulador ideal para medir el *Phase Leakage* (Fuga de fase) y la dispersión en fases binarias exactas (0.2500) y periódicas infinitas (0.3333).
* `noisy_qpe.py`: Ejecución de la QPE sometida al ruido real de `ibm_fez` para demostrar la compensación de errores entre la mitigación física y el error algorítmico.

### 5. Algoritmo de Shor
* `shor_ideal.py` / `plot_shor_ideal.py`: Caso de éxito. Factorización de $N=15$ ($a=2$), demostrando la "truncación sin pérdida" de la AQFT al buscar periodos compatibles en binario ($r=4$).
* `shor_n7.py` / `plot_shor_n7.py`: Caso de degradación. Factorización de $N=7$ ($a=2$), demostrando el colapso del algoritmo ante periodos no finitos en binario ($r=3$).

---

## ⚙️ Requisitos y Ejecución

Los scripts están desarrollados en Python. Las simulaciones cuánticas y la conexión con el hardware real se realizan a través del SDK de IBM.

### Dependencias principales:
Para ejecutar los experimentos y generar las gráficas, es necesario instalar las siguientes librerías:

- `qiskit`
- `qiskit-aer`
- `qiskit-ibm-runtime` (Requiere configuración previa del token de IBM Quantum)
- `matplotlib`
- `pandas`
- `numpy`

### Ejecución
Cada experimento está diseñado para ejecutarse de forma independiente. Por ejemplo, para ejecutar el análisis de recursos y generar sus gráficas:

```bash
python resource_study_qft.py
python plots/plot_resource_study.py
