"""
공용 시뮬레이션 헬퍼.

이 레포의 스크립트들이 제각각 AerSimulator + Sampler를 조립하던 걸 하나로 통일한다.
전부 이 run_circuit() 하나로 "트랜스파일 -> 실행 -> counts 추출"을 처리한다.
"""
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_aer import AerSimulator
from qiskit_aer.primitives import SamplerV2


def transpile_circuit(circuit, backend=None):
    """같은 회로를 여러 번 돌릴 때 트랜스파일을 한 번만 하기 위한 헬퍼."""
    backend = backend or AerSimulator()
    return generate_preset_pass_manager(backend=backend).run(circuit)


def run_circuit(circuit, creg_name, shots=10000, backend=None, transpiled=False):
    """
    회로를 트랜스파일 후 시뮬레이터에서 실행하고,
    creg_name으로 지정한 classical register의 측정 결과(counts)만 반환한다.

    여러 개의 classical register가 있는 회로(Simon 등)에서도
    creg_name만 지정하면 해당 레지스터에 대해 이미 marginalize된
    counts를 바로 받을 수 있다 (Sampler primitive의 이점).

    backend를 지정하지 않으면 기본 AerSimulator()를 사용한다.
    Clifford 전용 회로(Simon 등)는 backend=AerSimulator(method="stabilizer")를
    넘겨서 속도를 높일 수 있다.

    transpiled=True면 circuit이 이미 transpile_circuit()으로 트랜스파일된 회로라고 보고
    트랜스파일을 건너뛴다 (같은 회로를 반복 실행할 때 사용).
    """
    backend = backend or AerSimulator()
    isa_circuit = circuit if transpiled else transpile_circuit(circuit, backend)
    sampler = SamplerV2.from_backend(backend)
    job = sampler.run([isa_circuit], shots=shots)
    result = job.result()
    return result[0].data[creg_name].get_counts()
