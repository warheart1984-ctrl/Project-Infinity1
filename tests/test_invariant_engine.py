"""Tests for the invariant engine module."""

import unittest

from src.invariant_engine import InvariantEngine, MathInvariants


class TestInvariantEngine(unittest.TestCase):
    """Verify the invariant engine stays deterministic across supported domains."""

    def test_matrix_invariants_returns_expected_values(self):
        result = MathInvariants.matrix_invariants([[1, 2], [3, 4]])

        self.assertEqual(result["trace"], 5.0)
        self.assertAlmostEqual(result["determinant"], -2.0, places=6)
        self.assertEqual(result["rank"], 2)
        self.assertAlmostEqual(result["frobenius_norm"], 30 ** 0.5, places=6)
        self.assertEqual(len(result["eigenvalues"]), 2)

    def test_polynomial_invariants_returns_expected_values(self):
        result = MathInvariants.polynomial_invariants([1, -5, 6])

        self.assertEqual(result["degree"], 2)
        self.assertAlmostEqual(result["discriminant"], 1.0, places=6)
        self.assertAlmostEqual(result["leading_coefficient"], 1.0, places=6)

    def test_topological_invariants_returns_expected_values(self):
        result = MathInvariants.topological_invariants([(1, 2), (2, 3), (3, 1), (4, 5)])

        self.assertEqual(result["vertices"], 5)
        self.assertEqual(result["edges"], 4)
        self.assertEqual(result["connected_components"], 2)
        self.assertEqual(result["euler_characteristic"], 3)
        self.assertEqual(result["number_of_cycles"], 1)

    def test_statistical_invariants_returns_expected_values(self):
        result = MathInvariants.statistical_invariants([2, 4, 4, 4, 5, 5, 7, 9])

        self.assertAlmostEqual(result["mean"], 5.0, places=6)
        self.assertAlmostEqual(result["variance"], 4.0, places=6)
        self.assertAlmostEqual(result["standard_deviation"], 2.0, places=6)
        self.assertTrue(isinstance(result["skewness"], float))
        self.assertTrue(isinstance(result["kurtosis"], float))

    def test_cross_domain_report_collects_multiple_domains(self):
        result = InvariantEngine.cross_domain_report(
            matrix=[[1, 0], [0, 1]],
            polynomial_coeffs=[1, 0, -1],
            edges=[("a", "b")],
            data=[1, 2, 3],
        )

        self.assertEqual(result["module"], "invariant_engine")
        self.assertEqual(result["domain_count"], 4)
        self.assertEqual(result["available_domains"], ["matrix", "polynomial", "topology", "statistics"])
        self.assertIn("matrix", result["domains"])
        self.assertIn("statistics", result["domains"])

    def test_cross_domain_report_requires_at_least_one_input(self):
        with self.assertRaises(ValueError):
            InvariantEngine.cross_domain_report()


if __name__ == "__main__":
    unittest.main()
