# Contributing to GaugeGap Foundry

Thank you for your interest in contributing to GaugeGap Foundry! This project aims to build verification-first infrastructure for Millennium Prize-adjacent problems through rigorous computational mathematics and quantum computing.

## 🎯 Project Mission

Build reproducible finite-system benchmarks for:
- **GaugeGap**: Yang-Mills mass gap (lattice gauge theory)
- **FlowGap**: Navier-Stokes regularity (reduced PDE models)
- **CurveRank**: Riemann Hypothesis (spectral operator screening)

**Important**: We maintain strict claim boundaries. See [`AGENTS.md`](AGENTS.md) for language guidelines.

---

## 🚀 Quick Start for Contributors

### 1. Fork and Clone

```bash
# Fork on GitHub, then:
git clone https://github.com/YOUR_USERNAME/gaugegap-foundry.git
cd gaugegap-foundry
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with all dependencies
pip install -e ".[all]"

# Run tests to verify
python -m pytest
```

### 3. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

---

## 📋 Ways to Contribute

### 1. Report Issues

**Bug Reports**
- Use GitHub Issues
- Include minimal reproducible example
- Specify Python version and OS
- Attach relevant error messages

**Feature Requests**
- Describe the use case
- Explain how it fits project goals
- Consider implementation complexity

**Questions**
- Check existing documentation first
- Use GitHub Discussions for general questions
- Use Issues for specific technical problems

### 2. Submit Pull Requests

**Before You Start**
- Check existing issues and PRs
- Discuss major changes in an issue first
- Follow the claim boundary guidelines

**PR Checklist**
- [ ] Code follows project style
- [ ] Tests added for new functionality
- [ ] All tests pass (`pytest`)
- [ ] Documentation updated
- [ ] Claim boundary compliance verified
- [ ] Commit messages are clear

**PR Process**
1. Write clear description of changes
2. Link related issues
3. Wait for CI checks to pass
4. Address review feedback
5. Maintainer will merge when ready

### 3. Add New Operators (CurveRank Track)

To add a candidate Hilbert-Pólya operator:

```python
# 1. Add to src/gaugegap/curverank_operators.py
def build_your_operator(n_basis: int, **params) -> np.ndarray:
    """
    Construct your candidate operator.
    
    Args:
        n_basis: Truncation size
        **params: Operator-specific parameters
    
    Returns:
        Hermitian matrix of shape (n_basis, n_basis)
    """
    # Your implementation here
    pass
```

```yaml
# 2. Register in hypotheses/curverank-XXXX.yaml
id: curverank-XXXX
track: curverank
operator_family: your_operator
description: Brief description of your operator
kill_criteria:
  - spectral_mismatch_threshold: 10.0
  - truncation_stability: true
references:
  - "Your paper or source"
```

```python
# 3. Add test in tests/test_curverank_operators.py
def test_your_operator():
    H = build_your_operator(n_basis=10)
    assert H.shape == (10, 10)
    assert np.allclose(H, H.conj().T)  # Hermitian
```

```bash
# 4. Run screening
python scripts/run_curverank_screen.py \
    --family your_operator \
    --n-basis 10,15,20 \
    --k-zeros 20 \
    --output-dir results/your-operator
```

### 4. Add New Benchmarks (GaugeGap/FlowGap)

Follow the hypothesis registry pattern:

1. Create hypothesis YAML in `hypotheses/`
2. Implement model in `src/gaugegap/models/`
3. Add exact solver in `src/gaugegap/solvers/`
4. Create run script in `scripts/`
5. Add tests in `tests/`
6. Update documentation

### 5. Improve Documentation

- Fix typos and unclear explanations
- Add examples and tutorials
- Improve API documentation
- Create Jupyter notebooks
- Write blog posts or guides

### 6. Add Quantum Hardware Support

To add a new quantum provider:

```python
# 1. Create adapter in src/gaugegap/providers/
class YourProviderAdapter(QuantumProvider):
    """Adapter for Your Quantum Provider."""
    
    def submit_circuit(self, circuit, shots=1024):
        # Implementation
        pass
    
    def get_backend_info(self):
        # Implementation
        pass
```

```python
# 2. Add tests in tests/test_providers.py
def test_your_provider_adapter():
    adapter = YourProviderAdapter(api_key="test")
    # Test implementation
```

```python
# 3. Create example script in scripts/
# scripts/run_gaugegap_yourprovider.py
```

---

## 🎨 Code Standards

### Python Style

- **Python 3.10+** required
- Follow PEP 8 style guide
- Use type hints for public APIs
- Maximum line length: 100 characters
- Use descriptive variable names

```python
# Good
def compute_spectral_mismatch(
    eigenvalues: np.ndarray,
    target_zeros: np.ndarray,
    metric: str = "l2"
) -> float:
    """Compute mismatch between eigenvalues and target zeros."""
    pass

# Bad
def compute(e, t, m="l2"):
    pass
```

### Documentation

- Docstrings for all public functions/classes
- Use Google-style docstrings
- Include examples in docstrings
- Keep README and docs up to date

```python
def example_function(param1: int, param2: str) -> bool:
    """
    Brief one-line description.
    
    Longer description if needed, explaining the purpose,
    algorithm, or important details.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When param1 is negative
    
    Example:
        >>> result = example_function(42, "test")
        >>> print(result)
        True
    """
    pass
```

### Testing

- Write tests for all new features
- Aim for >80% code coverage
- Use pytest fixtures for setup
- Test edge cases and error conditions

```python
import pytest
import numpy as np

def test_spectral_mismatch():
    """Test spectral mismatch computation."""
    evals = np.array([14.1, 21.0, 25.0])
    zeros = np.array([14.134725, 21.022040, 25.010858])
    
    mismatch = compute_spectral_mismatch(evals, zeros)
    
    assert mismatch > 0
    assert mismatch < 1.0  # Should be small for good match

def test_spectral_mismatch_edge_cases():
    """Test edge cases."""
    # Empty arrays
    with pytest.raises(ValueError):
        compute_spectral_mismatch(np.array([]), np.array([]))
    
    # Mismatched lengths
    with pytest.raises(ValueError):
        compute_spectral_mismatch(np.array([1, 2]), np.array([1]))
```

### Claim Boundary Compliance

**CRITICAL**: All contributions must respect claim boundaries.

**Allowed Language**:
- "finite-system benchmark"
- "truncated lattice gauge model"
- "reduced PDE surrogate"
- "spectral screening"
- "hypothesis pruning"
- "impossibility proof for specific operator"

**Forbidden Language**:
- "proof of Yang-Mills mass gap"
- "proof of Navier-Stokes regularity"
- "proof of Riemann Hypothesis"
- "solved Millennium Prize problem"
- "AI discovered/proved/solved"
- "quantum computer proves theorem"

**Verification**: CI automatically checks for violations.

---

## 🔄 Development Workflow

### 1. Local Development

```bash
# Make changes
vim src/gaugegap/your_module.py

# Run tests
python -m pytest tests/test_your_module.py -v

# Run all tests
python -m pytest

# Check code style (optional)
pip install ruff
ruff check src/
```

### 2. Commit Changes

```bash
# Stage changes
git add src/gaugegap/your_module.py tests/test_your_module.py

# Commit with clear message
git commit -m "Add spectral operator for quantum graphs

- Implement quantum graph Hamiltonian construction
- Add tests for Hermiticity and spectrum
- Register in hypothesis registry
- Update documentation

Closes #123"
```

**Commit Message Format**:
- First line: Brief summary (50 chars max)
- Blank line
- Detailed description (wrap at 72 chars)
- Reference issues/PRs

### 3. Push and Create PR

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create PR on GitHub
# - Use clear title
# - Fill out PR template
# - Link related issues
# - Wait for CI checks
```

### 4. Address Review Feedback

```bash
# Make requested changes
vim src/gaugegap/your_module.py

# Commit changes
git add -u
git commit -m "Address review feedback: improve error handling"

# Push updates
git push origin feature/your-feature-name
```

---

## 🧪 Testing Guidelines

### Running Tests

```bash
# All tests
python -m pytest

# Specific file
python -m pytest tests/test_curverank_spectral.py

# Specific test
python -m pytest tests/test_curverank_spectral.py::test_berry_keating_operator

# With coverage
python -m pytest --cov=src/gaugegap --cov-report=html

# Verbose output
python -m pytest -v -s
```

### Test Categories

1. **Unit Tests**: Test individual functions
2. **Integration Tests**: Test component interactions
3. **Smoke Tests**: Quick sanity checks
4. **Regression Tests**: Prevent known bugs from returning

### Test Fixtures

```python
import pytest
import numpy as np

@pytest.fixture
def sample_operator():
    """Provide sample operator for tests."""
    return np.array([[1, 0], [0, 2]])

@pytest.fixture
def riemann_zeros():
    """Provide first few Riemann zeros."""
    return np.array([14.134725, 21.022040, 25.010858])

def test_with_fixtures(sample_operator, riemann_zeros):
    """Test using fixtures."""
    # Use fixtures in test
    pass
```

---

## 📚 Documentation Guidelines

### Code Documentation

- Every public function/class needs a docstring
- Include type hints
- Provide usage examples
- Document exceptions

### User Documentation

- Keep README.md up to date
- Update relevant docs/ files
- Add examples to QUICKSTART.md
- Create tutorials for complex features

### API Documentation

- Use clear, consistent naming
- Group related functions
- Provide migration guides for breaking changes

---

## 🐛 Debugging Tips

### Common Issues

**Import Errors**
```bash
# Reinstall in editable mode
pip install -e ".[all]"
```

**Test Failures**
```bash
# Run with verbose output
python -m pytest -v -s

# Run specific failing test
python -m pytest tests/test_file.py::test_function -v
```

**Numerical Precision**
```python
# Use np.allclose for floating-point comparisons
assert np.allclose(result, expected, rtol=1e-10, atol=1e-12)
```

---

## 🏆 Recognition

Contributors will be:
- Listed in CITATION.cff
- Acknowledged in papers
- Credited in release notes
- Invited to collaborate on publications

---

## 📞 Getting Help

- **GitHub Issues**: Bug reports, feature requests
- **GitHub Discussions**: Questions, ideas, general discussion
- **Email**: [maintainer email] for private inquiries
- **Documentation**: Check docs/ directory first

---

## 📜 License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

---

## 🙏 Thank You!

Every contribution helps advance open science and rigorous computational mathematics. Whether you're fixing a typo, adding a test, or implementing a new operator, your work matters.

**Let's build something meaningful together!**

---

**Last Updated**: 2026-05-28  
**Version**: 0.1.0