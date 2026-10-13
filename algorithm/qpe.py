# %%
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.circuit.library import QFTGate
from qiskit.visualization import plot_distribution
import numpy as np

from qsim_utils import run_circuit

t = 3
n = 1
qx = QuantumRegister(t, 'qx')
qy = QuantumRegister(n, 'qy')
c = ClassicalRegister(t, 'c')
qc = QuantumCircuit(qx, qy, c)

theta = 1/8
u = 1
qc.x(qy)
qc.barrier()

qc.h(qx)
for qx_t in range(t):
    for _ in range(u):
        qc.cp(2 * np.pi * theta, qx[qx_t], qy)
    u <<= 1 

qc.compose(QFTGate(t).inverse(), qx[:], inplace=True)
qc.measure(qx, c)
qc.draw(fold=-1, output='mpl')

counts = run_circuit(qc, "c", shots=10000)
plot_distribution(counts)

# %%
import numpy as np 
v = [np.exp(2j*np.pi*x/8) for x in range(1,5)]
v = np.diag(v)

U = QuantumCircuit(2)
U.unitary(v, [0,1])

U = U.to_gate() # 양자 게이트 객체 (qiskit.circuit.gate) 변환
U.name = "$U$"
CU = U.control(1) # 1개의 제어 큐비트 추가

t = 3
n = 2
u = 1
qx = QuantumRegister(t, 'qx')
qy = QuantumRegister(n , 'qy')
c = ClassicalRegister(t, 'c')
qc = QuantumCircuit(qx, qy, c)

qc.x(qy[0]) # 고유벡터 |01>

qc.barrier()

qc.h(qx)
for qx_t in range(t):
    for _ in range(u):
        qc.append(CU, [qx[qx_t], qy[0], qy[1]]) 
    u <<= 1 
    
qc.compose(QFTGate(t).inverse(), qx[:], inplace=True)
qc.measure(qx, c)
qc.draw(fold=-1, output='mpl')

count = run_circuit(qc, "c", shots=10000)
plot_distribution(count)

# %%
from qiskit.circuit.library import QFTGate

def library_qpe(t, U):
    # 라이브러리 QPE를 위에서 직접 만든 회로와 같은 비트 순서로 맞춰 주는 래퍼.
    # Qiskit 2.1부터 PhaseEstimation 클래스는 deprecated이고 phase_estimation() 함수로 대체되었는데,
    # 이 함수는 평가 레지스터를 뒤집어서(big-endian) 내놓으므로 swap으로 되돌린다.
    total = t + U.num_qubits
    circ = QuantumCircuit(total)
    try:
        from qiskit.circuit.library import phase_estimation
        circ.append(phase_estimation(t, U), range(total))
        for i in range(t // 2):
            circ.swap(i, t - 1 - i)
    except ImportError:
        from qiskit.circuit.library import PhaseEstimation
        circ.append(PhaseEstimation(t, U), range(total))
    return circ

t = 3
n = 2
qx = QuantumRegister(t, 'qx')
qy = QuantumRegister(n, 'qy')
c = ClassicalRegister(t, 'c')
qc = QuantumCircuit(qx, qy, c)

qc.x(qy) # |11>
qc.append(library_qpe(t, U), qx[:]+qy[:])
qc.measure(qx, c)
count = run_circuit(qc, "c", shots=10000)
plot_distribution(count)
# %%
