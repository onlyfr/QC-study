# %% 
import numpy as np
from numpy.random import randint
from math import gcd, lcm, floor, log2
from fractions import Fraction

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.circuit.library import QFTGate, UnitaryGate

from qsim_utils import run_circuit, transpile_circuit

class ShorAlgorithm:
    def __init__(self, N):
        self.N = N
        self.a = randint(2, N)
        self.n = self._count_binary_digits(N)
        self.t = 2*self.n + 1 
        
        self.circuit = None   # 회로는 run()에서 필요할 때 (a가 확정된 뒤) 한 번만 빌드한다
        self._isa_circuit = None  # 트랜스파일된 회로 (반복 실행용 캐시)
        self.factors = None
        print(f"[Shor] N={self.N}, a={self.a}, phase register: t={self.t} qubits")
        
    def set_a(self, a):
        self.a = a
        self.circuit = None  # 회로 게이트에 a가 내장되므로 다시 빌드해야 실제로 반영됨
    
    def _count_binary_digits(self, n):
        
        if n <= 0:
            return 0
        return floor(log2(n)) + 1
   
    def _shor_U(self, a, N, n):
        dim = 1 << n
        U = np.zeros((dim, dim))

        for j in range(dim):
            if j < N:
                i = (a * j) % N
            else:
                i = j
            U[i, j] = 1

        return U
    
    @staticmethod
    def _controlled_U(U, name):
        # 제어 큐비트가 첫 번째 큐비트인 controlled-U 행렬을 직접 구성 (U.control(1) 합성은 매우 느림)
        dim = U.shape[0]
        CU = np.eye(2 * dim)
        CU[1::2, 1::2] = U
        return UnitaryGate(CU, label=name)
    
    def _build_circuit(self):
        a = self.a
        t = self.t
        N = self.N
        n = self.n
        
        qx = QuantumRegister(t, 'x')
        qy = QuantumRegister(n, 'y')
        c = ClassicalRegister(t, 'c')
        qc = QuantumCircuit(qx, qy, c)
        qcU = QuantumCircuit(n)
        
        qc.x(qy[0]) # 입력 상태 |1>
        qc.h(qx)

        U = self._shor_U(a, N, n)
        for i in range(t):
            gateU = self._controlled_U(U, f"({a} mod {N})^2^{i}")
            qc.append(gateU, [qx[i]]+qy[:])
            U = U @ U 
            
        qc.append(QFTGate(t).inverse(), qx)
        qc.measure(qx, c)
        
        self.circuit = qc 
        self._isa_circuit = None
        
    def _estimate_order(self):
        if self._isa_circuit is None:
            self._isa_circuit = transpile_circuit(self.circuit)
        count = run_circuit(self._isa_circuit, "c", shots=10000, transpiled=True)
        candidates = sorted(count.items(), key=lambda x: -x[1])
        
        print(f"[QPE] {sum(count.values())} shots, {len(candidates)} distinct outcomes")
        return candidates 

    def _order_verification(self, a, r, N):
        return pow(a, r, N) == 1

    def _minimal_order(self, a, r, N):
        # a^r = 1 (mod N)을 만족하는 r이 위수의 배수일 수 있으므로, r의 약수 중 가장 작은 위수로 줄인다
        for d in range(1, r + 1):
            if r % d == 0 and pow(a, d, N) == 1:
                return d
        return r

    def _order_estimate(self,
                    max_qpe_runs=5,
                    max_phases_per_run=20):
        a = self.a 
        N = self.N 
        t = self.t
        circuit = self.circuit
        R = 1 
    
        seen_phases = set()
        
        for _ in range(max_qpe_runs):
            candidates = self._estimate_order()
            n_phases = min(len(candidates), max_phases_per_run)
                
            for phase, _ in candidates[:n_phases]:
                if phase in seen_phases:
                    continue 
                
                seen_phases.add(phase)
                
                s = int(phase, 2)
                if s == 0: continue 

                r = 1 << t 
                print(f"[QPE] measured {phase} -> phase {s}/{r}")
                
                limit = N - 1  # 위수는 N보다 작다
                f = Fraction(s, r).limit_denominator(limit)
                r, s = f.denominator, f.numerator
                print(f"      estimated phase {s}/{r} -> order candidate r = {r}")
                
                if self._order_verification(a, r, N):
                    return self._minimal_order(a, r, N)
                
                R = lcm(R, r)
                if R < N and self._order_verification(a, R, N):
                    return self._minimal_order(a, R, N)
            
        return -1
    
    def run(self):
        a, N = self.a, self.N
        g = gcd(a, N)
        if g != 1:
            # gcd(a, N) != 1이면 U_a가 순열(유니터리)이 아니므로 회로를 만들 수 없다. 고전적으로 이미 인수를 찾은 경우.
            print(f"[Shor] gcd({a}, {N}) = {g} > 1: factor found classically, {N} = {g} x {N // g}")
            self.factors = (g, N // g)
            return False
        
        if self.circuit is None:
            self._build_circuit()
        r = self._order_estimate()
        print(f"[Shor] estimated order of {a} mod {N}: r = {r}")
        
        if r == -1:
            print(f"[Shor] order finding failed for a={a}, N={N}")
            return False
        elif r % 2 == 1:
            print(f"[Shor] r = {r} is odd, so a={a} cannot be used; try another a")
            return False
        
        print(f"[Shor] r = {r} is even, computing gcd(a^(r/2) +/- 1, N)")
        
        x = pow(a, r//2, N)
        p = gcd(x + 1, N)

        if p == N:
            print(f"[Shor] a^(r/2) = -1 (mod {N}) for a={a}: trivial factor, try another a")
            return False 
        elif p == 1:
            print(f"[Shor] r = {r} gives no nontrivial factor for a={a}, try another a")
            return False 
        else:
            self.factors = (p, N // p)
            print(f"[Shor] success: {N} = {p} x {N // p}")
            return True
        
shor = ShorAlgorithm(21)
shor.set_a(2)
shor.run()
# %%
