# %%
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
import numpy as np

def oracle(n):
    qy = QuantumRegister(1, 'y')
    qx = QuantumRegister(n, 'x')
    qc = QuantumCircuit(qy, qx) # n+1 큐비트 회로
    
    np.random.seed()
    cond = np.random.choice(["constant", "balanced"])
    
    if cond == "constant":
        val = np.random.randint(2) # 0 또는 1
        print(f"f(x) = {val} (constant)")
        
        if val == 1:
            qc.x(qy)
    else:
        val = np.random.randint(1, 2**n) # 1이상 2^n - 1 이하의 어떤 정수
        print(f"val = {bin(val)[2:].zfill(n)} (balanced)")
        for i in range(n):
            if val & (1 << i):
                qc.cx(qx[i], qy)
                
    qc.name = "$U_f$"
    return qc 

# %%
n = 5
qy = QuantumRegister(1, 'y')
qx = QuantumRegister(n, 'x')
c = ClassicalRegister(n, 'c')

circuit = QuantumCircuit(qy, qx, c)
circuit.x(qy)
circuit.h(qy)
circuit.h(qx)
circuit.barrier()

circuit.compose(oracle(n), range(n+1), inplace=True)
circuit.barrier()

circuit.h(qx)
circuit.measure(qx, c)  # Qiskit 기본 컨벤션 그대로 사용 (전부 0이면 constant, 아니면 balanced 판정만 하므로 비트 순서 무관)
circuit.draw(output='mpl')

# %%
from qiskit.visualization import plot_histogram
from qsim_utils import run_circuit

counts = run_circuit(circuit, "c", shots=10000)
plot_histogram(counts)
# %%
