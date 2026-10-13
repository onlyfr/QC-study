# %%

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
import numpy as np

def oracle(n, s):
    qy = QuantumRegister(1, 'y')
    qx = QuantumRegister(n, 'x')
    qc = QuantumCircuit(qy, qx)
    
    for i in range(n):
        if (s & (1 << i)) == 0:
            qc.x(qx[i])
    
    qc.mcx(list(qx), qy)
    
    for i in range(n):
        if (s & (1 << i)) == 0:
            qc.x(qx[i])
            
    qc.name = '$V_f$'
    return qc 

n = 5

np.random.seed()
s = np.random.randint(2**n) 
print(f"s = {bin(s)[2:].zfill(n)}")
# %%
def diffuser(n):
    qx = QuantumRegister(n, 'x')
    qc = QuantumCircuit(qx)
    
    qc.h(qx)
    qc.x(qx)
    qc.barrier()
    
    qc.h(qx[0])
    qc.mcx(qx[1:n], qx[0])
    qc.h(qx[0])
    qc.barrier()
    
    qc.x(qx)
    qc.h(qx)
    
    qc.name = "$D_s$"
    return qc

# %%
from math import floor, pi
n = 5 
iteration = floor(pi * 2**(n/2) / 4)

qy = QuantumRegister(1, 'y')
qx = QuantumRegister(n, 'x')
c = ClassicalRegister(n, 'c')
circuit = QuantumCircuit(qy, qx, c)

circuit.x(qy)
circuit.h(qy)
circuit.h(qx)
circuit.barrier()

for _ in range(iteration):
    circuit.append(oracle(n, s), range(n+1))
    circuit.barrier()
    
    circuit.append(diffuser(n), range(1,n+1))
    circuit.barrier() 
    
circuit.measure(qx, c)
circuit.draw(output="mpl", fold=-1)

# %%
from qiskit.visualization import plot_distribution
from qsim_utils import run_circuit

counts = run_circuit(circuit, "c", shots=10000)
plot_distribution(counts)
# %%
