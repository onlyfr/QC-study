# %%
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from numpy import random 

def deutsch_oracle_circuit():
    qy = QuantumRegister(1, 'y')
    qx = QuantumRegister(1, 'x')
    qc = QuantumCircuit(qy, qx)
    
    random.seed()
    f = random.randint(4)
    if f == 0:
        print("f(x) = 0")
        pass 
    elif f == 1:
        print("f(x) = 1")
        qc.x(qy)
    elif f == 2:
        print("f(0) = 0, f(1) = 1")
        qc.cx(qx, qy)
    elif f == 3:
        print("f(0) = 1, f(1) = 0")    
        qc.x(qx)
        qc.cx(qx, qy)
        qc.x(qx)
        
    qc.name = "$D_f$"
    return qc 

qy = QuantumRegister(1, 'y')
qx = QuantumRegister(1, 'x')
c = ClassicalRegister(1, 'c')
circuit = QuantumCircuit(qy, qx, c)

circuit.h(qx)
circuit.x(qy)
circuit.h(qy)
circuit.append(deutsch_oracle_circuit(), [qy, qx])
circuit.h(qx)
circuit.measure(qx, c)

from qiskit.visualization import plot_histogram
from qsim_utils import run_circuit

counts = run_circuit(circuit, "c", shots=1000)
print(counts)

answer = ""
if '0' in counts:
    answer = "constant"
else:
    answer = "balanced"
print(f"f(x) is a {answer} function!")
    
plot_histogram(counts)
# %%
