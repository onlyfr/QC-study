# %%
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
import numpy as np

def oracle(n):
    qy = QuantumRegister(1, 'y')
    qx = QuantumRegister(n, 'x')
    qc = QuantumCircuit(qy, qx) # n+1 큐비트 회로
    
    np.random.seed()
    s = np.random.randint(2**n) 
    print(f"s = {bin(s)[2:].zfill(n)}")
    
    for i in range(n):
        if s & (1 << i):
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

circuit.append(oracle(n), range(n+1)) 
circuit.barrier()

circuit.h(qx)

# Qiskit 기본 컨벤션(qx[0]이 최하위/오른쪽 비트) 그대로 사용 -- s의 bin() 표기와 그대로 대응됨
circuit.measure(qx, c)
circuit.draw(output='mpl')
# %%
from qiskit.visualization import plot_histogram
from qsim_utils import run_circuit

counts = run_circuit(circuit, "c", shots=10000)
plot_histogram(counts)
# %%
