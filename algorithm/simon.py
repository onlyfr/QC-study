# %%
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
import random

def oracle(n):
    qr1 = QuantumRegister(n, 'q1')
    qr2 = QuantumRegister(n, 'q2')
    qc = QuantumCircuit(qr1, qr2)
    
    random.seed()
    s = random.randrange(1, 2**n)
    s = bin(s)[2:].zfill(n) # s_{n-1} s_{n-2} ... s_{0}
    pivot = n-s.index('1')-1
    print(f"s = {s} (pivot index = {pivot})") 
    
    for i in range(n):
        if i == pivot:
            continue 
        qc.cx(qr1[i], qr2[i])
        
        if s[n-i-1] == '1':
            qc.cx(qr1[pivot], qr2[i])
    
    qc.name = "$U_f$"
    return qc, s

oracle(5)[0].draw(output='mpl')
# %%
n = 5
qr1 = QuantumRegister(n, 'q1')
qr2 = QuantumRegister(n, 'q2')
c1 = ClassicalRegister(n, 'c1')
c2 = ClassicalRegister(n, 'c2')
circuit = QuantumCircuit(qr1, qr2, c1, c2)

circuit.h(qr1)
circuit.barrier()

oracle_u, s = oracle(n)
print(f"임의로 생성한 주기: {s}")
circuit.append(oracle_u, range(2*n))
circuit.barrier()

circuit.measure(qr2, c2)
circuit.barrier()

circuit.h(qr1)
circuit.barrier() 

circuit.measure(qr1, c1)

from qiskit.visualization import plot_histogram
from qsim_utils import run_circuit

# Sampler는 레지스터 이름으로 바로 marginalize된 counts를 주므로 수동으로 잘라 합칠 필요가 없음
c1_counts = run_circuit(circuit, "c1", shots=n+20)
plot_histogram(c1_counts)

# %%
from qiskit_aer import AerSimulator
import numpy as np

from qsim_utils import run_circuit, transpile_circuit

class SimonAlgorithm:
    def __init__(self, n):
        self.n = n
        self.basis = [[0] * n for _ in range(n)]
        self.rank = 0          # 현재 랭크
        self.count = 0         # 시도 횟수
        self.s = 0             # 정답 주기 (검증용)
        self.circuit = None    # 회로 객체
        self._isa_circuit = None  # 트랜스파일된 회로 (반복 측정용 캐시)
        # Simon 오라클은 H, X, CX만 사용하는 Clifford 회로이므로 stabilizer 시뮬레이터로 가속
        self.backend = AerSimulator(method="stabilizer")

        self._build_circuit()
        
    def _oracle(self):
        qr1 = QuantumRegister(self.n, 'q1')
        qr2 = QuantumRegister(self.n, 'q2')
        qc = QuantumCircuit(qr1, qr2)
        
        random.seed()
        s = random.randrange(1, 2**self.n)
        s = bin(s)[2:].zfill(self.n) # s_{n-1} s_{n-2} ... s_{0}
        pivot = self.n-s.index('1')-1
        print(f"s = {s} (pivot index = {pivot})") 
        
        for i in range(self.n):
            if i == pivot:
                continue 
            qc.cx(qr1[i], qr2[i])
            
            if s[self.n-i-1] == '1':
                qc.cx(qr1[pivot], qr2[i])
        
        qc.name = "$U_f$"
        return qc, s
    
    def _build_circuit(self):
        n = self.n
        qr1 = QuantumRegister(n, 'q1')
        qr2 = QuantumRegister(n, 'q2')
        c1 = ClassicalRegister(n, 'c1')
        c2 = ClassicalRegister(n, 'c2')
        circuit = QuantumCircuit(qr1, qr2, c1, c2)

        circuit.h(qr1)
        circuit.barrier()

        oracle_u, s = self._oracle() 
        self.s = s  # 정답 s 저장
        circuit.append(oracle_u, range(2*n))
        circuit.barrier()

        circuit.measure(qr2, c2)
        circuit.barrier()

        circuit.h(qr1)
        circuit.barrier() 

        circuit.measure(qr1, c1)
        
        self.circuit = circuit

    def measurement(self):
        # run_circuit(..., "c1", ...)이 c1 레지스터만 이미 marginalize해서 주므로
        # 예전처럼 결합된 비트스트링을 잘라 c1을 분리하는 과정이 필요 없음
        if self._isa_circuit is None:
            self._isa_circuit = transpile_circuit(self.circuit, self.backend)
        counts = run_circuit(self._isa_circuit, "c1", shots=1, backend=self.backend, transpiled=True)
        bitstring = next(iter(counts))

        self.count += 1
        return bitstring
    
    def add_and_check_indep(self, x_str):
        x = list(map(int, x_str[::-1]))
        
        # 0이 들어오면 무시 (종속)
        if not any(x):
            return False

        # 기저 확인 및 소거
        for i in range(self.n):
        
            # i번째 비트가 1인지 확인
            if x[i] == 1:
                # i번째 기저가 존재하는 경우
                if self.basis[i][i] == 1:
                    x = [a ^ b for a, b in zip(x, self.basis[i])] # 성분별 XOR 수행
                else:
                    # i번째 기저가 없는 경우 새로운 pivot을 확보함
                    self.basis[i] = x.copy()
                    self.rank += 1
                    return True 
                
        return False


    def is_found(self):
        # n-1개의 기저를 찾았는지 확인
        return self.rank == self.n - 1
    
    def recover_period(self):
        s_bits = [0] * self.n

        for i in range(self.n-1, -1, -1):
            
            # basis[i]가 없다면 이 위치는 자유 변수 → 비자명 해를 위해 1로 설정
            if self.basis[i][i] == 0:
                s_bits[i] = 1
                
            else:
                # basis[i] · s = 0 을 만족해야 함
                tmp = 0
                for j in range(i+1, self.n):
                    if self.basis[i][j] == 1:
                        tmp ^= s_bits[j]
                        
                s_bits[i] = tmp
                
        return "".join('1' if b else '0' for b in s_bits[::-1])


# %%

simon = SimonAlgorithm(20)
while not simon.is_found():
    z = simon.measurement()
    print(f"Adding {z}: {simon.add_and_check_indep(z)}")


recover_s = simon.recover_period()
print(f"회로 작동 횟수: {simon.count}")
print(f"찾은 주기: {recover_s}")
print(f"임의로 생성한 주기: {simon.s}")

# %%
