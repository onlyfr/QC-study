# %%
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
import numpy as np
from qiskit.circuit.library import QFTGate

# %%
n = 3
qc = QuantumCircuit(n)
qc.x([1,2]) 
qc.compose(QFTGate(n), range(n), inplace=True)
qc.compose(QFTGate(n).inverse(), range(n), inplace=True)
qc.measure_all()
qc.draw(output='mpl')


from qiskit.visualization import plot_histogram
from qsim_utils import run_circuit

count = run_circuit(qc, "meas", shots=1000)
plot_histogram(count)

# %%
def qft(n):
    qc = QuantumCircuit(n)
    for j in range(n-1, -1, -1):
        qc.h(j)
        for k in range(j-1, -1, -1):
            qc.cp(np.pi / (2 ** (j - k)), k, j)
        qc.barrier()
            
    for i in range(n // 2):
        qc.swap(i, n - i - 1)
        
    qc.name = "$qft$"
    return qc

def iqft(n):
    qc = QuantumCircuit(n)
    for i in range(n // 2):
        qc.swap(i, n - i - 1)    
        
    for j in range(n):
        for k in range(j):
            qc.cp(-np.pi / (2 ** (j - k)), k, j)
        qc.h(j)
        qc.barrier()
            
    qc.name = "$iqft$"
    return qc
 
n = 3
qc = QuantumCircuit(n)
qc.x([1,2])
qc.barrier() 

qc.append(qft(n), range(n))
qc.compose(iqft(n), range(n), inplace=True)
qc.measure_all()
qc.draw(output='mpl')

count = run_circuit(qc, "meas", shots=1000)
print(count)

from qiskit.quantum_info import Operator
print("qft == QFTGate:", Operator(qft(n)).equiv(Operator(QFTGate(n))))
print("iqft == QFTGate^-1:", Operator(iqft(n)).equiv(Operator(QFTGate(n).inverse())))
# %%
