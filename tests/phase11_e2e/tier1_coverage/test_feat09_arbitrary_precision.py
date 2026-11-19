"""Feature 9: Arbitrary-Precision Engine Core.

Verifies:
1. Exact big-integer arithmetic scaling across 100, 500, 1000, and 1500 digits.
2. AST verification of zero float conversions in core mathematical modules.
3. Exact digit count computation matching 10^(d-1) <= N < 10^d bounds.
4. Seamless interoperability between native Python int and gmpy2.mpz.
5. Exact string serialization and deserialization roundtrip for multi-hundred digit numbers.
"""

import ast
from pathlib import Path
import pytest
import gmpy2
from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter
from tests.phase11_e2e.contracts.math_contracts import compute_manifold


@pytest.mark.phase11_tier1
def test_f09_bigint_arithmetic_scaling() -> None:
    """Verifies arbitrary-precision arithmetic at 100, 500, 1000, and 1500 digits."""
    # Since C(x) ~= 12 * x^5, a coordinate x with D/5 digits produces ~D digits
    target_digits = [100, 500, 1000, 1500]
    for d in target_digits:
        # Choose x ~ 10^(d/5)
        x_exp = d // 5
        x = 10 ** x_exp + 30
        # Ensure 6 | x
        x -= (x % 6)

        C, A, B = compute_manifold(x)
        assert B - A == 2
        digit_count = len(str(C))
        assert abs(digit_count - d) <= 5, f"Expected ~{d} digits, got {digit_count}"
        assert C.bit_length() > int(d * 3.3)


@pytest.mark.phase11_tier1
def test_f09_ast_verification_no_float_conversions() -> None:
    """Uses AST parsing to assert zero float() casts in mathematical evaluation files."""
    paths_to_check = [Path("tests/phase11_e2e/contracts/math_contracts.py")]
    math_model_path = Path("src/phase11/math_model.py")
    if math_model_path.is_file():
        paths_to_check.append(math_model_path)

    for path in paths_to_check:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        float_calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "float":
                    float_calls.append(node.lineno)
        assert len(float_calls) == 0, f"Found float() call in {path} at lines {float_calls}"


@pytest.mark.phase11_tier1
def test_f09_exact_digit_count_calculation() -> None:
    """Verifies exact digit count satisfies 10^(d-1) <= N < 10^d for big numbers."""
    x = 10 ** 40
    x -= (x % 6)
    C, A, B = compute_manifold(x)
    for num in [C, A, B]:
        s = str(num)
        d = len(s)
        assert num >= 10 ** (d - 1)
        assert num < 10 ** d


@pytest.mark.phase11_tier1
def test_f09_gmpy2_mpz_interoperability() -> None:
    """Verifies that gmpy2.mpz operations match native Python arbitrary-precision ints."""
    x_val = 10 ** 50 + 42
    x_mpz = gmpy2.mpz(x_val)

    # 12*x^5 + 6*x^3
    py_result = 12 * (x_val ** 5) + 6 * (x_val ** 3)
    mpz_result = 12 * (x_mpz ** 5) + 6 * (x_mpz ** 3)

    assert int(mpz_result) == py_result
    assert gmpy2.is_even(mpz_result)
    assert gmpy2.gcd(mpz_result, 6) == 6


@pytest.mark.phase11_tier1
def test_f09_bigint_string_serialization_roundtrip() -> None:
    """Verifies lossless serialization and deserialization of 500+ digit candidates."""
    x = 10 ** 100 + 6
    C, A, B = compute_manifold(x)

    str_A = str(A)
    str_B = str(B)
    reconstructed_A = int(str_A)
    reconstructed_B = int(str_B)

    assert reconstructed_A == A
    assert reconstructed_B == B
    assert reconstructed_B - reconstructed_A == 2
