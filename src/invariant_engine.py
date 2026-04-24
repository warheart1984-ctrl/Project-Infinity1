"""Cross-domain invariant calculations for AAIS.

This module packages the invariant engine from the design doc into a reusable,
deterministic library that stays friendly to runtime traces and JSON payloads.
It covers four domains:

1. Matrix invariants
2. Polynomial invariants
3. Topological invariants
4. Statistical invariants
"""

from __future__ import annotations

from collections.abc import Iterable
import math
import warnings

import networkx as nx
import numpy as np
from scipy.stats import kurtosis, skew
import sympy as sp


def _normalize_scalar(value):
    if isinstance(value, sp.Basic):
        value = complex(value.evalf()) if value.is_complex else float(value)
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, complex):
        if abs(value.imag) <= 1e-12:
            return float(value.real)
        return {
            "real": round(float(value.real), 12),
            "imag": round(float(value.imag), 12),
        }
    if isinstance(value, (int, float)):
        numeric = float(value)
        if math.isnan(numeric) or math.isinf(numeric):
            raise ValueError("Invariant calculation produced a non-finite numeric result.")
        return numeric
    return value


def _coerce_square_matrix(matrix) -> np.ndarray:
    array = np.asarray(matrix, dtype=float)
    if array.ndim != 2 or array.shape[0] != array.shape[1]:
        raise ValueError("Input must be a square matrix.")
    return array


def _normalize_coefficients(coeffs) -> list[float]:
    if not isinstance(coeffs, Iterable) or isinstance(coeffs, (str, bytes)):
        raise ValueError("Polynomial coefficients must be a non-string iterable.")
    normalized = [float(value) for value in coeffs]
    if not normalized:
        raise ValueError("Polynomial coefficients cannot be empty.")
    while len(normalized) > 1 and abs(normalized[0]) <= 1e-12:
        normalized.pop(0)
    if all(abs(value) <= 1e-12 for value in normalized):
        raise ValueError("Polynomial coefficients cannot all be zero.")
    return normalized


def _build_polynomial(coeffs: list[float]) -> sp.Poly:
    x = sp.symbols("x")
    degree = len(coeffs) - 1
    expression = sum(sp.Float(coeff) * x ** power for coeff, power in zip(coeffs, range(degree, -1, -1)))
    return sp.Poly(expression, x)


def _normalize_edges(edges) -> list[tuple]:
    if edges is None:
        return []
    if not isinstance(edges, Iterable) or isinstance(edges, (str, bytes)):
        raise ValueError("Edges must be an iterable of (u, v) pairs.")
    normalized: list[tuple] = []
    for edge in edges:
        if not isinstance(edge, Iterable) or isinstance(edge, (str, bytes)):
            raise ValueError("Each edge must be an iterable with exactly two nodes.")
        pair = tuple(edge)
        if len(pair) != 2:
            raise ValueError("Each edge must contain exactly two nodes.")
        normalized.append(pair)
    return normalized


def _coerce_numeric_data(data) -> np.ndarray:
    array = np.asarray(list(data), dtype=float)
    if array.ndim != 1 or array.size == 0:
        raise ValueError("Statistical data must be a non-empty one-dimensional sequence.")
    if np.isnan(array).all():
        raise ValueError("Statistical data cannot be entirely NaN.")
    return array


def _safe_distribution_moment(data: np.ndarray, *, mode: str) -> float:
    finite = data[~np.isnan(data)]
    if finite.size == 0:
        raise ValueError("Statistical data cannot be entirely NaN.")
    if finite.size < 2 or np.allclose(finite, finite[0]):
        return 0.0
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        raw = skew(finite, nan_policy="omit") if mode == "skew" else kurtosis(finite, nan_policy="omit")
    numeric = float(raw)
    if math.isnan(numeric) or math.isinf(numeric):
        return 0.0
    return numeric


class MathInvariants:
    """Deterministic invariant calculations across multiple mathematical domains."""

    @staticmethod
    def matrix_invariants(matrix) -> dict:
        """Return trace, determinant, eigenvalues, rank, and Frobenius norm."""
        array = _coerce_square_matrix(matrix)
        eigenvalues = [_normalize_scalar(value) for value in np.linalg.eigvals(array)]
        return {
            "trace": _normalize_scalar(np.trace(array)),
            "determinant": _normalize_scalar(np.linalg.det(array)),
            "eigenvalues": eigenvalues,
            "rank": int(np.linalg.matrix_rank(array)),
            "frobenius_norm": _normalize_scalar(np.linalg.norm(array, "fro")),
        }

    @staticmethod
    def polynomial_invariants(coeffs) -> dict:
        """Return degree, discriminant, and leading coefficient for numeric coefficients."""
        normalized = _normalize_coefficients(coeffs)
        poly = _build_polynomial(normalized)
        return {
            "degree": int(poly.degree()),
            "discriminant": _normalize_scalar(poly.discriminant()),
            "leading_coefficient": _normalize_scalar(poly.LC()),
        }

    @staticmethod
    def topological_invariants(edges) -> dict:
        """Return graph invariants for an undirected edge list."""
        graph = nx.Graph()
        graph.add_edges_from(_normalize_edges(edges))
        vertices = graph.number_of_nodes()
        edge_count = graph.number_of_edges()
        connected_components = nx.number_connected_components(graph) if vertices else 0
        return {
            "vertices": vertices,
            "edges": edge_count,
            "connected_components": connected_components,
            "euler_characteristic": vertices - edge_count + connected_components,
            "number_of_cycles": len(nx.cycle_basis(graph)),
        }

    @staticmethod
    def statistical_invariants(data) -> dict:
        """Return mean, variance, standard deviation, skewness, and kurtosis."""
        array = _coerce_numeric_data(data)
        return {
            "mean": _normalize_scalar(np.nanmean(array)),
            "variance": _normalize_scalar(np.nanvar(array)),
            "standard_deviation": _normalize_scalar(np.nanstd(array)),
            "skewness": _normalize_scalar(_safe_distribution_moment(array, mode="skew")),
            "kurtosis": _normalize_scalar(_safe_distribution_moment(array, mode="kurtosis")),
        }

    @staticmethod
    def cross_domain_report(
        *,
        matrix=None,
        polynomial_coeffs=None,
        edges=None,
        data=None,
    ) -> dict:
        """Return a compact multi-domain report for whichever inputs are provided."""
        domains: dict[str, dict] = {}
        if matrix is not None:
            domains["matrix"] = MathInvariants.matrix_invariants(matrix)
        if polynomial_coeffs is not None:
            domains["polynomial"] = MathInvariants.polynomial_invariants(polynomial_coeffs)
        if edges is not None:
            domains["topology"] = MathInvariants.topological_invariants(edges)
        if data is not None:
            domains["statistics"] = MathInvariants.statistical_invariants(data)
        if not domains:
            raise ValueError("At least one domain input is required.")
        return {
            "module": "invariant_engine",
            "domains": domains,
            "domain_count": len(domains),
            "available_domains": list(domains.keys()),
        }


InvariantEngine = MathInvariants

