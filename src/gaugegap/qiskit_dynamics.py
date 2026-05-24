from __future__ import annotations

from collections.abc import Mapping

from gaugegap.qiskit_backend import pauli_label


def build_tfim_trotter_circuit(
    n_sites: int,
    exchange_coupling: float,
    transverse_field: float,
    time: float,
    steps: int,
    initial_state: str = "zeros",
    periodic: bool = False,
    measure: bool = False,
):
    if n_sites <= 1:
        raise ValueError("n_sites must be greater than 1")
    if steps <= 0:
        raise ValueError("steps must be positive")

    try:
        from qiskit import QuantumCircuit
    except ImportError as exc:
        raise RuntimeError("Install Qiskit extras with: python -m pip install -e '.[quantum]'") from exc

    circuit = QuantumCircuit(n_sites, n_sites if measure else 0)
    _apply_initial_state(circuit, n_sites, initial_state)

    dt = time / steps
    last_bond = n_sites if periodic else n_sites - 1
    for _ in range(steps):
        for site in range(last_bond):
            circuit.rzz(-2.0 * exchange_coupling * dt, site, (site + 1) % n_sites)
        for site in range(n_sites):
            circuit.rx(-2.0 * transverse_field * dt, site)

    if measure:
        circuit.measure(range(n_sites), range(n_sites))
    return circuit


def statevector_z_observables(circuit, n_sites: int, periodic: bool = False) -> dict[str, object]:
    try:
        from qiskit.quantum_info import SparsePauliOp, Statevector
    except ImportError as exc:
        raise RuntimeError("Install Qiskit extras with: python -m pip install -e '.[quantum]'") from exc

    bare = circuit.remove_final_measurements(inplace=False)
    state = Statevector.from_instruction(bare)
    z_values = [
        float(state.expectation_value(SparsePauliOp.from_list([(pauli_label(n_sites, {site: "Z"}), 1.0)])).real)
        for site in range(n_sites)
    ]
    zz_values = [
        float(
            state.expectation_value(
                SparsePauliOp.from_list([(pauli_label(n_sites, {site: "Z", (site + 1) % n_sites: "Z"}), 1.0)])
            ).real
        )
        for site in range(n_sites if periodic else n_sites - 1)
    ]
    return {"z": z_values, "zz": zz_values}


def aer_sample_z_observables(
    circuit,
    n_sites: int,
    shots: int,
    periodic: bool = False,
    seed: int = 1234,
    noise: str = "none",
) -> dict[str, object]:
    if shots <= 0:
        raise ValueError("shots must be positive")

    try:
        from qiskit import transpile
        from qiskit_aer import AerSimulator
    except ImportError as exc:
        raise RuntimeError("Install Qiskit extras with: python -m pip install -e '.[quantum]'") from exc

    measured = circuit.copy()
    if measured.num_clbits < n_sites:
        measured.measure_all()

    simulator = AerSimulator(seed_simulator=seed, noise_model=_noise_model(noise))
    compiled = transpile(measured, simulator, seed_transpiler=seed)
    counts = simulator.run(compiled, shots=shots).result().get_counts()
    observables = counts_z_observables(counts, n_sites=n_sites, periodic=periodic)
    observables["counts"] = dict(counts)
    return observables


def counts_z_observables(counts: Mapping[str, int], n_sites: int, periodic: bool = False) -> dict[str, object]:
    total = sum(counts.values())
    if total <= 0:
        raise ValueError("counts must contain at least one shot")

    z_sums = [0.0] * n_sites
    zz_sums = [0.0] * (n_sites if periodic else n_sites - 1)

    for raw_key, count in counts.items():
        key = raw_key.replace(" ", "")
        bits = list(reversed(key[-n_sites:]))
        z_values = [1.0 if bits[site] == "0" else -1.0 for site in range(n_sites)]
        for site, value in enumerate(z_values):
            z_sums[site] += count * value
        for site in range(len(zz_sums)):
            zz_sums[site] += count * z_values[site] * z_values[(site + 1) % n_sites]

    return {
        "z": [value / total for value in z_sums],
        "zz": [value / total for value in zz_sums],
        "shots": total,
    }


def _apply_initial_state(circuit, n_sites: int, initial_state: str) -> None:
    if initial_state == "zeros":
        return
    if initial_state == "ones":
        for site in range(n_sites):
            circuit.x(site)
        return
    if initial_state == "domain_wall":
        for site in range(n_sites // 2, n_sites):
            circuit.x(site)
        return
    raise ValueError(f"unsupported initial_state: {initial_state}")


def _noise_model(noise: str):
    if noise == "none":
        return None
    if noise != "depolarizing":
        raise ValueError(f"unsupported noise model: {noise}")

    from qiskit_aer.noise import NoiseModel, depolarizing_error

    model = NoiseModel()
    model.add_all_qubit_quantum_error(depolarizing_error(0.001, 1), ["rx", "x"])
    model.add_all_qubit_quantum_error(depolarizing_error(0.005, 2), ["rzz"])
    return model
