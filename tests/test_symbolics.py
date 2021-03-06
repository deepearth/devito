import sympy
import time
import pytest

from devito import Grid, Function, solve, div, grad, TimeFunction


def test_float_indices():
    """
    Test that indices only contain Integers.
    """
    grid = Grid((10,))
    x = grid.dimensions[0]
    x0 = x + 1.0 * x.spacing
    u = Function(name="u", grid=grid, space_order=2)
    indices = u.subs({x: x0}).indexify().indices[0]
    assert len(indices.atoms(sympy.Float)) == 0
    assert indices == x + 1

    indices = u.subs({x: 1.0}).indexify().indices[0]
    assert len(indices.atoms(sympy.Float)) == 0
    assert indices == 1


@pytest.mark.parametrize('so', [2, 4])
def test_solve(so):
    """
    Test that our solve produces the correct output and faster than sympy's
    default behavior for an affine equation (i.e. PDE time steppers).
    """
    grid = Grid((10, 10, 10))
    u = TimeFunction(name="u", grid=grid, time_order=2, space_order=so)
    v = Function(name="v", grid=grid, space_order=so)
    eq = u.dt2 - div(v * grad(u))

    # Standard sympy solve
    t0 = time.time()
    sol1 = sympy.solve(eq.evaluate, u.forward, rational=False, simplify=False)[0]
    t1 = time.time() - t0

    # Devito custom solve for linear equation in the target ax + b (most PDE tie steppers)
    t0 = time.time()
    sol2 = solve(eq.evaluate, u.forward)
    t12 = time.time() - t0

    diff = sympy.simplify(sol1 - sol2)
    # Difference can end up with super small coeffs with different evaluation
    # so zero out everything very small
    assert diff.xreplace({k: 0 if abs(k) < 1e-10 else k
                          for k in diff.atoms(sympy.Float)}) == 0
    # Make sure faster (actually much more than 10 for very complex cases)
    assert t12 < t1/10
