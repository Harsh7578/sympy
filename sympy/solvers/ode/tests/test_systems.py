from sympy import (symbols, Symbol, diff, Function, Derivative, Matrix, Rational, S,
                   I, Eq, sqrt)
from sympy.functions import exp, cos, sin, log
from sympy.solvers.ode import dsolve
from sympy.solvers.ode.subscheck import checksysodesol
from sympy.solvers.ode.systems import (neq_nth_linear_constant_coeff_match, linear_ode_to_matrix,
                                       ODEOrderError, ODENonlinearError, _simpsol)
from sympy.integrals.integrals import Integral
from sympy.testing.pytest import raises, slow, ON_TRAVIS, skip

C0, C1, C2, C3, C4, C5, C6, C7, C8, C9, C10 = symbols('C0:11')


def test_linear_ode_to_matrix():
    f, g, h = symbols("f, g, h", cls=Function)
    t = Symbol("t")
    funcs = [f(t), g(t), h(t)]
    f1 = f(t).diff(t)
    g1 = g(t).diff(t)
    h1 = h(t).diff(t)
    f2 = f(t).diff(t, 2)
    g2 = g(t).diff(t, 2)
    h2 = h(t).diff(t, 2)

    eqs_1 = [Eq(f1, g(t)), Eq(g1, f(t))]
    sol_1 = ([Matrix([[1, 0], [0, 1]]), Matrix([[ 0, -1], [-1,  0]])], Matrix([[0],[0]]))
    assert linear_ode_to_matrix(eqs_1, funcs[:-1], t, 1) == sol_1

    eqs_2 = [Eq(f1, f(t) + 2*g(t)), Eq(g1, h(t)), Eq(h1, g(t) + h(t) + f(t))]
    sol_2 = ([Matrix([[1, 0, 0], [0, 1, 0], [0, 0, 1]]), Matrix([[-1, -2,  0], [ 0,  0, -1], [-1, -1, -1]])],
             Matrix([[0], [0], [0]]))
    assert linear_ode_to_matrix(eqs_2, funcs, t, 1) == sol_2

    eqs_3 = [Eq(2*f1 + 3*h1, f(t) + g(t)), Eq(4*h1 + 5*g1, f(t) + h(t)), Eq(5*f1 + 4*g1, g(t) + h(t))]
    sol_3 = ([Matrix([[2, 0, 3], [0, 5, 4], [5, 4, 0]]), Matrix([[-1, -1,  0], [-1,  0, -1], [0, -1, -1]])],
             Matrix([[0], [0], [0]]))
    assert linear_ode_to_matrix(eqs_3, funcs, t, 1) == sol_3

    eqs_4 = [Eq(f2 + h(t), f1 + g(t)), Eq(2*h2 + g2 + g1 + g(t), 0), Eq(3*h1, 4)]
    sol_4 = ([Matrix([[1, 0, 0], [0, 1, 2], [0, 0, 0]]), Matrix([[-1, 0, 0], [0, 1, 0], [0, 0, 3]]),
              Matrix([[0, -1, 1], [0,  1, 0], [0, 0, 0]])], Matrix([[0], [0], [4]]))
    assert linear_ode_to_matrix(eqs_4, funcs, t, 2) == sol_4

    eqs_5 = [Eq(f2, g(t)), Eq(f1 + g1, f(t))]
    raises(ODEOrderError, lambda: linear_ode_to_matrix(eqs_5, funcs[:-1], t, 1))

    eqs_6 = [Eq(f1, f(t)**2), Eq(g1, f(t) + g(t))]
    raises(ODENonlinearError, lambda: linear_ode_to_matrix(eqs_6, funcs[:-1], t, 1))


def test_neq_nth_linear_constant_coeff_match():
    x, y, z, w = symbols('x, y, z, w', cls=Function)
    t = Symbol('t')
    x1 = diff(x(t), t)
    y1 = diff(y(t), t)
    z1 = diff(z(t), t)
    w1 = diff(w(t), t)
    x2 = diff(x(t), t, t)
    funcs = [x(t), y(t)]
    funcs_2 = funcs + [z(t), w(t)]

    eqs_1 = (5 * x1 + 12 * x(t) - 6 * (y(t)), (2 * y1 - 11 * t * x(t) + 3 * y(t) + t))
    assert neq_nth_linear_constant_coeff_match(eqs_1, funcs, t) is None

    eqs_2 = (5 * (x1**2) + 12 * x(t) - 6 * (y(t)), (2 * y1 - 11 * t * x(t) + 3 * y(t) + t))
    assert neq_nth_linear_constant_coeff_match(eqs_2, funcs, t) is None

    eqs_3 = (5 * x1 + 12 * x(t) - 6 * (y(t)), (2 * y1 - 11 * x(t) + 3 * y(t)), (5 * w1 + z(t)), (z1 + w(t)))
    answer_3 = {'no_of_equation': 4,
     'eq': (12*x(t) - 6*y(t) + 5*Derivative(x(t), t),
      -11*x(t) + 3*y(t) + 2*Derivative(y(t), t),
      z(t) + 5*Derivative(w(t), t),
      w(t) + Derivative(z(t), t)),
     'func': [x(t), y(t), z(t), w(t)],
     'order': {x(t): 1, y(t): 1, z(t): 1, w(t): 1},
     'is_linear': True,
     'is_constant': True,
     'is_homogeneous': True,
     'func_coeff': Matrix([
     [Rational(12, 5), Rational(-6, 5), 0, 0],
     [Rational(-11, 2),  Rational(3, 2),   0, 0],
     [0, 0, 0, 1],
     [0, 0, Rational(1, 5), 0]]),
     'type_of_equation': 'type1',
     'is_general': True}
    assert neq_nth_linear_constant_coeff_match(eqs_3, funcs_2, t) == answer_3

    eqs_4 = (5 * x1 + 12 * x(t) - 6 * (y(t)), (2 * y1 - 11 * x(t) + 3 * y(t)), (z1 - w(t)), (w1 - z(t)))
    answer_4 = {'no_of_equation': 4,
     'eq': (12 * x(t) - 6 * y(t) + 5 * Derivative(x(t), t),
            -11 * x(t) + 3 * y(t) + 2 * Derivative(y(t), t),
            -w(t) + Derivative(z(t), t),
            -z(t) + Derivative(w(t), t)),
     'func': [x(t), y(t), z(t), w(t)],
     'order': {x(t): 1, y(t): 1, z(t): 1, w(t): 1},
     'is_linear': True,
     'is_constant': True,
     'is_homogeneous': True,
     'func_coeff': Matrix([
         [Rational(12, 5), Rational(-6, 5), 0, 0],
         [Rational(-11, 2), Rational(3, 2), 0, 0],
         [0, 0, 0, -1],
         [0, 0, -1, 0]]),
     'type_of_equation': 'type1',
     'is_general': True}
    assert neq_nth_linear_constant_coeff_match(eqs_4, funcs_2, t) == answer_4

    eqs_5 = (5 * x1 + 12 * x(t) - 6 * (y(t)) + x2, (2 * y1 - 11 * x(t) + 3 * y(t)), (z1 - w(t)), (w1 - z(t)))
    assert neq_nth_linear_constant_coeff_match(eqs_5, funcs_2, t) is None

    eqs_6 = (Eq(x1,3*y(t)-11*z(t)),Eq(y1,7*z(t)-3*x(t)),Eq(z1,11*x(t)-7*y(t)))
    answer_6 = {'no_of_equation': 3, 'eq': (Eq(Derivative(x(t), t), 3*y(t) - 11*z(t)), Eq(Derivative(y(t), t), -3*x(t) + 7*z(t)),
            Eq(Derivative(z(t), t), 11*x(t) - 7*y(t))), 'func': [x(t), y(t), z(t)], 'order': {x(t): 1, y(t): 1, z(t): 1},
            'is_linear': True, 'is_constant': True, 'is_homogeneous': True,
            'func_coeff': Matrix([
                         [  0, -3, 11],
                         [  3,  0, -7],
                         [-11,  7,  0]]),
            'type_of_equation': 'type1', 'is_general': True}

    assert neq_nth_linear_constant_coeff_match(eqs_6, funcs_2[:-1], t) == answer_6

    eqs_7 = (Eq(x1, y(t)), Eq(y1, x(t)))
    answer_7 = {'no_of_equation': 2, 'eq': (Eq(Derivative(x(t), t), y(t)), Eq(Derivative(y(t), t), x(t))),
                'func': [x(t), y(t)], 'order': {x(t): 1, y(t): 1}, 'is_linear': True, 'is_constant': True,
                'is_homogeneous': True, 'func_coeff': Matrix([
                                                        [ 0, -1],
                                                        [-1,  0]]),
                'type_of_equation': 'type1', 'is_general': True}
    assert neq_nth_linear_constant_coeff_match(eqs_7, funcs, t) == answer_7

    eqs_8 = (Eq(x1, 21*x(t)), Eq(y1, 17*x(t)+3*y(t)), Eq(z1, 5*x(t)+7*y(t)+9*z(t)))
    answer_8 = {'no_of_equation': 3, 'eq': (Eq(Derivative(x(t), t), 21*x(t)), Eq(Derivative(y(t), t), 17*x(t) + 3*y(t)),
            Eq(Derivative(z(t), t), 5*x(t) + 7*y(t) + 9*z(t))), 'func': [x(t), y(t), z(t)], 'order': {x(t): 1, y(t): 1, z(t): 1},
            'is_linear': True, 'is_constant': True, 'is_homogeneous': True,
            'func_coeff': Matrix([
                            [-21,  0,  0],
                            [-17, -3,  0],
                            [ -5, -7, -9]]),
            'type_of_equation': 'type1', 'is_general': True}

    assert neq_nth_linear_constant_coeff_match(eqs_8, funcs_2[:-1], t) == answer_8

    eqs_9 = (Eq(x1,4*x(t)+5*y(t)+2*z(t)),Eq(y1,x(t)+13*y(t)+9*z(t)),Eq(z1,32*x(t)+41*y(t)+11*z(t)))
    answer_9 = {'no_of_equation': 3, 'eq': (Eq(Derivative(x(t), t), 4*x(t) + 5*y(t) + 2*z(t)),
                Eq(Derivative(y(t), t), x(t) + 13*y(t) + 9*z(t)), Eq(Derivative(z(t), t), 32*x(t) + 41*y(t) + 11*z(t))),
                'func': [x(t), y(t), z(t)], 'order': {x(t): 1, y(t): 1, z(t): 1}, 'is_linear': True,
                'is_constant': True, 'is_homogeneous': True,
                'func_coeff': Matrix([
                            [ -4,  -5,  -2],
                            [ -1, -13,  -9],
                            [-32, -41, -11]]),
                'type_of_equation': 'type1', 'is_general': True}
    assert neq_nth_linear_constant_coeff_match(eqs_9, funcs_2[:-1], t) == answer_9

    eqs_10 = (Eq(3*x1,4*5*(y(t)-z(t))),Eq(4*y1,3*5*(z(t)-x(t))),Eq(5*z1,3*4*(x(t)-y(t))))
    answer_10 = {'no_of_equation': 3, 'eq': (Eq(3*Derivative(x(t), t), 20*y(t) - 20*z(t)),
                Eq(4*Derivative(y(t), t), -15*x(t) + 15*z(t)), Eq(5*Derivative(z(t), t), 12*x(t) - 12*y(t))),
                'func': [x(t), y(t), z(t)], 'order': {x(t): 1, y(t): 1, z(t): 1}, 'is_linear': True,
                'is_constant': True, 'is_homogeneous': True,
                'func_coeff': Matrix([
                                [  0, Rational(-20, 3),  Rational(20, 3)],
                                [Rational(15, 4),     0, Rational(-15, 4)],
                                [Rational(-12, 5), Rational(12, 5),  0]]),
                'type_of_equation': 'type1', 'is_general': True}
    assert neq_nth_linear_constant_coeff_match(eqs_10, funcs_2[:-1], t) == answer_10

    eq11 = (Eq(x1,3*y(t)-11*z(t)),Eq(y1,7*z(t)-3*x(t)),Eq(z1,11*x(t)-7*y(t)))
    sol11 = {'no_of_equation': 3, 'eq': (Eq(Derivative(x(t), t), 3*y(t) - 11*z(t)), Eq(Derivative(y(t), t), -3*x(t) + 7*z(t)),
            Eq(Derivative(z(t), t), 11*x(t) - 7*y(t))), 'func': [x(t), y(t), z(t)], 'order': {x(t): 1, y(t): 1, z(t): 1},
            'is_linear': True, 'is_constant': True, 'is_homogeneous': True, 'func_coeff': Matrix([
            [  0, -3, 11], [  3,  0, -7], [-11,  7,  0]]), 'type_of_equation': 'type1', 'is_general': True}
    assert neq_nth_linear_constant_coeff_match(eq11, funcs_2[:-1], t) == sol11

    eq12 = (Eq(Derivative(x(t), t), y(t)), Eq(Derivative(y(t), t), x(t)))
    sol12 = {'no_of_equation': 2, 'eq': (Eq(Derivative(x(t), t), y(t)), Eq(Derivative(y(t), t), x(t))),
             'func': [x(t), y(t)], 'order': {x(t): 1, y(t): 1}, 'is_linear': True, 'is_constant': True,
             'is_homogeneous': True, 'func_coeff': Matrix([
            [0, -1],
            [-1, 0]]), 'type_of_equation': 'type1', 'is_general': True}
    assert neq_nth_linear_constant_coeff_match(eq12, [x(t), y(t)], t) == sol12

    eq13 = (Eq(Derivative(x(t), t), 21 * x(t)), Eq(Derivative(y(t), t), 17 * x(t) + 3 * y(t)),
            Eq(Derivative(z(t), t), 5 * x(t) + 7 * y(t) + 9 * z(t)))
    sol13 = {'no_of_equation': 3, 'eq': (
    Eq(Derivative(x(t), t), 21 * x(t)), Eq(Derivative(y(t), t), 17 * x(t) + 3 * y(t)),
    Eq(Derivative(z(t), t), 5 * x(t) + 7 * y(t) + 9 * z(t))), 'func': [x(t), y(t), z(t)],
             'order': {x(t): 1, y(t): 1, z(t): 1}, 'is_linear': True, 'is_constant': True, 'is_homogeneous': True,
             'func_coeff': Matrix([
                 [-21, 0, 0],
                 [-17, -3, 0],
                 [-5, -7, -9]]), 'type_of_equation': 'type1', 'is_general': True}
    assert neq_nth_linear_constant_coeff_match(eq13, [x(t), y(t), z(t)], t) == sol13

    eq14 = (
    Eq(Derivative(x(t), t), 4 * x(t) + 5 * y(t) + 2 * z(t)), Eq(Derivative(y(t), t), x(t) + 13 * y(t) + 9 * z(t)),
    Eq(Derivative(z(t), t), 32 * x(t) + 41 * y(t) + 11 * z(t)))
    sol14 = {'no_of_equation': 3, 'eq': (
    Eq(Derivative(x(t), t), 4 * x(t) + 5 * y(t) + 2 * z(t)), Eq(Derivative(y(t), t), x(t) + 13 * y(t) + 9 * z(t)),
    Eq(Derivative(z(t), t), 32 * x(t) + 41 * y(t) + 11 * z(t))), 'func': [x(t), y(t), z(t)],
             'order': {x(t): 1, y(t): 1, z(t): 1}, 'is_linear': True, 'is_constant': True, 'is_homogeneous': True,
             'func_coeff': Matrix([
                 [-4, -5, -2],
                 [-1, -13, -9],
                 [-32, -41, -11]]), 'type_of_equation': 'type1', 'is_general': True}
    assert neq_nth_linear_constant_coeff_match(eq14, [x(t), y(t), z(t)], t) == sol14

    eq15 = (Eq(3 * Derivative(x(t), t), 20 * y(t) - 20 * z(t)), Eq(4 * Derivative(y(t), t), -15 * x(t) + 15 * z(t)),
            Eq(5 * Derivative(z(t), t), 12 * x(t) - 12 * y(t)))
    sol15 = {'no_of_equation': 3, 'eq': (
    Eq(3 * Derivative(x(t), t), 20 * y(t) - 20 * z(t)), Eq(4 * Derivative(y(t), t), -15 * x(t) + 15 * z(t)),
    Eq(5 * Derivative(z(t), t), 12 * x(t) - 12 * y(t))), 'func': [x(t), y(t), z(t)],
             'order': {x(t): 1, y(t): 1, z(t): 1}, 'is_linear': True, 'is_constant': True, 'is_homogeneous': True,
             'func_coeff': Matrix([
                 [0, Rational(-20, 3), Rational(20, 3)],
                 [Rational(15, 4), 0, Rational(-15, 4)],
                 [Rational(-12, 5), Rational(12, 5), 0]]), 'type_of_equation': 'type1', 'is_general': True}
    assert neq_nth_linear_constant_coeff_match(eq15, [x(t), y(t), z(t)], t) == sol15

    # Constant coefficient homogeneous ODEs
    eq1 = (Eq(diff(x(t),t), x(t) + y(t) + 9), Eq(diff(y(t),t), 2*x(t) + 5*y(t) + 23))
    sol1 = {'no_of_equation': 2, 'eq': (Eq(Derivative(x(t), t), x(t) + y(t) + 9),
        Eq(Derivative(y(t), t), 2*x(t) + 5*y(t) + 23)), 'func': [x(t), y(t)],
        'order': {x(t): 1, y(t): 1}, 'is_linear': True, 'is_constant': True, 'is_homogeneous': False, 'is_general': True,
        'func_coeff': Matrix([[-1, -1], [-2, -5]]), 'rhs': Matrix([[ 9], [23]]), 'type_of_equation': 'type2'}
    assert neq_nth_linear_constant_coeff_match(eq1, funcs, t) == sol1

    # Non constant coefficient non-homogeneous ODEs
    eq1 = (Eq(diff(x(t), t), 5 * t * x(t) + 2 * y(t)), Eq(diff(y(t), t), 2 * x(t) + 5 * t * y(t)))
    sol1 = {'no_of_equation': 2, 'eq': (Eq(Derivative(x(t), t), 5*t*x(t) + 2*y(t)), Eq(Derivative(y(t), t), 5*t*y(t) + 2*x(t))),
            'func': [x(t), y(t)], 'order': {x(t): 1, y(t): 1}, 'is_linear': True, 'is_constant': False,
            'is_homogeneous': True, 'func_coeff': Matrix([ [-5*t,   -2], [  -2, -5*t]]), 'commutative_antiderivative': Matrix([
            [5*t**2/2,      2*t], [     2*t, 5*t**2/2]]), 'type_of_equation': 'type3', 'is_general': True}
    assert neq_nth_linear_constant_coeff_match(eq1, funcs, t) == sol1


def test_matrix_exp():
    from sympy.matrices.dense import Matrix, eye, zeros
    from sympy.solvers.ode.systems import matrix_exp
    t = Symbol('t')

    for n in range(1, 6+1):
        assert matrix_exp(zeros(n), t) == eye(n)

    for n in range(1, 6+1):
        A = eye(n)
        expAt = exp(t) * eye(n)
        assert matrix_exp(A, t) == expAt

    for n in range(1, 6+1):
        A = Matrix(n, n, lambda i,j: i+1 if i==j else 0)
        expAt = Matrix(n, n, lambda i,j: exp((i+1)*t) if i==j else 0)
        assert matrix_exp(A, t) == expAt

    A = Matrix([[0, 1], [-1, 0]])
    expAt = Matrix([[cos(t), sin(t)], [-sin(t), cos(t)]])
    assert matrix_exp(A, t) == expAt

    A = Matrix([[2, -5], [2, -4]])
    expAt = Matrix([
            [3*exp(-t)*sin(t) + exp(-t)*cos(t), -5*exp(-t)*sin(t)],
            [2*exp(-t)*sin(t), -3*exp(-t)*sin(t) + exp(-t)*cos(t)]
            ])
    assert matrix_exp(A, t) == expAt

    A = Matrix([[21, 17, 6], [-5, -1, -6], [4, 4, 16]])
    # TO update this.
    # expAt = Matrix([
    #     [(8*t*exp(12*t) + 5*exp(12*t) - 1)*exp(4*t)/4,
    #      (8*t*exp(12*t) + 5*exp(12*t) - 5)*exp(4*t)/4,
    #      (exp(12*t) - 1)*exp(4*t)/2],
    #     [(-8*t*exp(12*t) - exp(12*t) + 1)*exp(4*t)/4,
    #      (-8*t*exp(12*t) - exp(12*t) + 5)*exp(4*t)/4,
    #      (-exp(12*t) + 1)*exp(4*t)/2],
    #     [4*t*exp(16*t), 4*t*exp(16*t), exp(16*t)]])
    expAt = Matrix([
        [2*t*exp(16*t) + 5*exp(16*t)/4 - exp(4*t)/4, 2*t*exp(16*t) + 5*exp(16*t)/4 - 5*exp(4*t)/4,  exp(16*t)/2 - exp(4*t)/2],
        [ -2*t*exp(16*t) - exp(16*t)/4 + exp(4*t)/4,  -2*t*exp(16*t) - exp(16*t)/4 + 5*exp(4*t)/4, -exp(16*t)/2 + exp(4*t)/2],
        [                             4*t*exp(16*t),                                4*t*exp(16*t),                 exp(16*t)]
        ])
    assert matrix_exp(A, t) == expAt

    A = Matrix([[1, 1, 0, 0],
                [0, 1, 1, 0],
                [0, 0, 1, -S(1)/8],
                [0, 0, S(1)/2, S(1)/2]])
    expAt = Matrix([
        [exp(t), t*exp(t), 4*t*exp(3*t/4) + 8*t*exp(t) + 48*exp(3*t/4) - 48*exp(t),
                            -2*t*exp(3*t/4) - 2*t*exp(t) - 16*exp(3*t/4) + 16*exp(t)],
        [0, exp(t), -t*exp(3*t/4) - 8*exp(3*t/4) + 8*exp(t), t*exp(3*t/4)/2 + 2*exp(3*t/4) - 2*exp(t)],
        [0, 0, t*exp(3*t/4)/4 + exp(3*t/4), -t*exp(3*t/4)/8],
        [0, 0, t*exp(3*t/4)/2, -t*exp(3*t/4)/4 + exp(3*t/4)]
        ])
    assert matrix_exp(A, t) == expAt

    A = Matrix([
    [ 0, 1,  0, 0],
    [-1, 0,  0, 0],
    [ 0, 0,  0, 1],
    [ 0, 0, -1, 0]])

    expAt = Matrix([
    [ cos(t), sin(t),         0,        0],
    [-sin(t), cos(t),         0,        0],
    [      0,      0,    cos(t),   sin(t)],
    [      0,      0,   -sin(t),   cos(t)]])
    assert matrix_exp(A, t) == expAt

    A = Matrix([
    [ 0, 1,  1, 0],
    [-1, 0,  0, 1],
    [ 0, 0,  0, 1],
    [ 0, 0, -1, 0]])

    expAt = Matrix([
    [ cos(t), sin(t),  t*cos(t), t*sin(t)],
    [-sin(t), cos(t), -t*sin(t), t*cos(t)],
    [      0,      0,    cos(t),   sin(t)],
    [      0,      0,   -sin(t),   cos(t)]])
    assert matrix_exp(A, t) == expAt

    # This case is unacceptably slow right now but should be solvable...
    #a, b, c, d, e, f = symbols('a b c d e f')
    #A = Matrix([
    #[-a,  b,          c,  d],
    #[ a, -b,          e,  0],
    #[ 0,  0, -c - e - f,  0],
    #[ 0,  0,          f, -d]])

    A = Matrix([[0, I], [I, 0]])
    expAt = Matrix([
    [exp(I*t)/2 + exp(-I*t)/2, exp(I*t)/2 - exp(-I*t)/2],
    [exp(I*t)/2 - exp(-I*t)/2, exp(I*t)/2 + exp(-I*t)/2]])
    assert matrix_exp(A, t) == expAt


def test_sysode_linear_neq_order1_type1():

    f, g, x, y, h = symbols('f g x y h', cls=Function)
    a, b, c, t = symbols('a b c t')

    eq1 = [Eq(x(t).diff(t), x(t)), Eq(y(t).diff(t), y(t))]
    sol1 = [Eq(x(t), C1*exp(t)), Eq(y(t), C2*exp(t))]
    assert dsolve(eq1) == sol1
    assert checksysodesol(eq1, sol1) == (True, [0, 0])

    eq2 = [Eq(x(t).diff(t), 2*x(t)), Eq(y(t).diff(t), 3*y(t))]
    #sol2 = [Eq(x(t), C1*exp(2*t)), Eq(y(t), C2*exp(3*t))]
    sol2 = [Eq(x(t), C1*exp(2*t)), Eq(y(t), C2*exp(3*t))]
    assert dsolve(eq2) == sol2
    assert checksysodesol(eq2, sol2) == (True, [0, 0])

    eq3 = [Eq(x(t).diff(t), a*x(t)), Eq(y(t).diff(t), a*y(t))]
    sol3 = [Eq(x(t), C1*exp(a*t)), Eq(y(t), C2*exp(a*t))]
    assert dsolve(eq3) == sol3
    assert checksysodesol(eq3, sol3) == (True, [0, 0])

    # Regression test case for issue #15474
    # https://github.com/sympy/sympy/issues/15474
    eq4 = [Eq(x(t).diff(t), a*x(t)), Eq(y(t).diff(t), b*y(t))]
    sol4 = [Eq(x(t), C1*exp(a*t)), Eq(y(t), C2*exp(b*t))]
    assert dsolve(eq4) == sol4
    assert checksysodesol(eq4, sol4) == (True, [0, 0])

    eq5 = [Eq(x(t).diff(t), -y(t)), Eq(y(t).diff(t), x(t))]
    sol5 = [Eq(x(t), -C1*sin(t) - C2*cos(t)), Eq(y(t), C1*cos(t) - C2*sin(t))]
    assert dsolve(eq5) == sol5
    assert checksysodesol(eq5, sol5) == (True, [0, 0])

    eq6 = [Eq(x(t).diff(t), -2*y(t)), Eq(y(t).diff(t), 2*x(t))]
    sol6 = [Eq(x(t), -C1*sin(2*t) - C2*cos(2*t)), Eq(y(t), C1*cos(2*t) - C2*sin(2*t))]
    assert dsolve(eq6) == sol6
    assert checksysodesol(eq6, sol6) == (True, [0, 0])

    eq7 = [Eq(x(t).diff(t), I*y(t)), Eq(y(t).diff(t), I*x(t))]
    sol7 = [Eq(x(t), -C1*exp(-I*t) + C2*exp(I*t)), Eq(y(t), C1*exp(-I*t) + C2*exp(I*t))]
    assert dsolve(eq7) == sol7
    assert checksysodesol(eq7, sol7) == (True, [0, 0])

    eq8 = [Eq(x(t).diff(t), -a*y(t)), Eq(y(t).diff(t), a*x(t))]
    sol8 = [Eq(x(t), -I*C1*exp(-I*a*t) + I*C2*exp(I*a*t)), Eq(y(t), C1*exp(-I*a*t) + C2*exp(I*a*t))]
    assert dsolve(eq8) == sol8
    assert checksysodesol(eq8, sol8) == (True, [0, 0])

    eq9 = [Eq(x(t).diff(t), x(t) + y(t)), Eq(y(t).diff(t), x(t) - y(t))]
    sol9 = [Eq(x(t), C1*(1 - sqrt(2))*exp(-sqrt(2)*t) + C2*(1 + sqrt(2))*exp(sqrt(2)*t)),
           Eq(y(t), C1*exp(-sqrt(2)*t) + C2*exp(sqrt(2)*t))]
    assert dsolve(eq9) == sol9
    assert checksysodesol(eq9, sol9) == (True, [0, 0])

    eq10 = [Eq(x(t).diff(t), x(t) + y(t)), Eq(y(t).diff(t), x(t) + y(t))]
    sol10 = [Eq(x(t), -C1 + C2*exp(2*t)), Eq(y(t), C1 + C2*exp(2*t))]
    assert dsolve(eq10) == sol10
    assert checksysodesol(eq10, sol10) == (True, [0, 0])

    eq11 = [Eq(x(t).diff(t), 2*x(t) + y(t)), Eq(y(t).diff(t), -x(t) + 2*y(t))]
    sol11 = [Eq(x(t), (C1*sin(t) + C2*cos(t))*exp(2*t)),
            Eq(y(t), (C1*cos(t) - C2*sin(t))*exp(2*t))]
    assert dsolve(eq11) == sol11
    assert checksysodesol(eq11, sol11) == (True, [0, 0])

    eq12 = [Eq(x(t).diff(t), x(t) + 2*y(t)), Eq(y(t).diff(t), 2*x(t) + y(t))]
    sol12 = [Eq(x(t), -C1*exp(-t) + C2*exp(3*t)), Eq(y(t), C1*exp(-t) + C2*exp(3*t))]
    assert dsolve(eq12) == sol12
    assert checksysodesol(eq12, sol12) == (True, [0, 0])

    eq13 = [Eq(x(t).diff(t), 4*x(t) + y(t)), Eq(y(t).diff(t), -x(t) + 2*y(t))]
    sol13 = [Eq(x(t), (C1 + C2*t + C2)*exp(3*t)), Eq(y(t), (-C1 - C2*t)*exp(3*t))]
    assert dsolve(eq13) == sol13
    assert checksysodesol(eq13, sol13) == (True, [0, 0])

    eq14 = [Eq(x(t).diff(t), a*y(t)), Eq(y(t).diff(t), a*x(t))]
    sol14 = [Eq(x(t), -C1*exp(-a*t) + C2*exp(a*t)), Eq(y(t), C1*exp(-a*t) + C2*exp(a*t))]
    assert dsolve(eq14) == sol14
    assert checksysodesol(eq14, sol14) == (True, [0, 0])

    eq15 = [Eq(x(t).diff(t), a*y(t)), Eq(y(t).diff(t), b*x(t))]
    sol15 = [Eq(x(t), -C1*a*exp(-t*sqrt(a*b))/sqrt(a*b) + C2*a*exp(t*sqrt(a*b))/sqrt(a*b)),
            Eq(y(t), C1*exp(-t*sqrt(a*b)) + C2*exp(t*sqrt(a*b)))]
    assert dsolve(eq15) == sol15
    assert checksysodesol(eq15, sol15) == (True, [0, 0])

    eq16 = [Eq(x(t).diff(t), a*x(t) + b*y(t)), Eq(y(t).diff(t), c*x(t))]
    sol16 = [Eq(x(t), -2*C1*b*exp(t*(a/2 - sqrt(a**2 + 4*b*c)/2))/(a + sqrt(a**2 + 4*b*c)) - 2*C2*b*exp(t*(a/2 + sqrt(a**2 + 4*b*c)/2))/(a - sqrt(a**2 + 4*b*c))),
            Eq(y(t), C1*exp(t*(a/2 - sqrt(a**2 + 4*b*c)/2)) + C2*exp(t*(a/2 + sqrt(a**2 + 4*b*c)/2)))]
    assert dsolve(eq16) == sol16
    assert checksysodesol(eq16, sol16) == (True, [0, 0])

    # Regression test case for issue #18562
    # https://github.com/sympy/sympy/issues/18562
    eq17 = [Eq(x(t).diff(t), x(t) + a*y(t)), Eq(y(t).diff(t), x(t)*a - y(t))]
    sol17 = [Eq(x(t), -C1*a*exp(-t*sqrt(a**2 + 1))/(sqrt(a**2 + 1) + 1) + C2*a*exp(t*sqrt(a**2 + 1))/(sqrt(a**2 + 1) - 1)),
            Eq(y(t), C1*exp(-t*sqrt(a**2 + 1)) + C2*exp(t*sqrt(a**2 + 1)))]
    assert dsolve(eq17) == sol17
    assert checksysodesol(eq17, sol17) == (True, [0, 0])

    eq18 = [Eq(x(t).diff(t), 0), Eq(y(t).diff(t), 0)]
    sol18 = [Eq(x(t), C1), Eq(y(t), C2)]
    assert dsolve(eq18) == sol18
    assert checksysodesol(eq18, sol18) == (True, [0, 0])

    eq19 = [Eq(x(t).diff(t), 2*x(t) - y(t)), Eq(y(t).diff(t), x(t))]
    sol19 = [Eq(x(t), (C1 + C2*t + C2)*exp(t)), Eq(y(t), (C1 + C2*t)*exp(t))]
    assert dsolve(eq19) == sol19
    assert checksysodesol(eq19, sol19) == (True, [0, 0])

    eq20 = [Eq(x(t).diff(t), x(t)), Eq(y(t).diff(t), x(t) + y(t))]
    sol20 = [Eq(x(t), C2*exp(t)), Eq(y(t), (C1 + C2*t)*exp(t))]
    assert dsolve(eq20) == sol20
    assert checksysodesol(eq20, sol20) == (True, [0, 0])

    eq21 = [Eq(x(t).diff(t), 3*x(t)), Eq(y(t).diff(t), x(t) + y(t))]
    sol21 = [Eq(x(t), 2*C2*exp(3*t)), Eq(y(t), C1*exp(t) + C2*exp(3*t))]
    assert dsolve(eq21) == sol21
    assert checksysodesol(eq21, sol21) == (True, [0, 0])

    eq22 = [Eq(x(t).diff(t), 3*x(t)), Eq(y(t).diff(t), y(t))]
    sol22 = [Eq(x(t), C2*exp(3*t)), Eq(y(t), C1*exp(t))]
    assert dsolve(eq22) == sol22
    assert checksysodesol(eq22, sol22) == (True, [0, 0])

    Z0 = Function('Z0')
    Z1 = Function('Z1')
    Z2 = Function('Z2')
    Z3 = Function('Z3')

    k01, k10, k20, k21, k23, k30 = symbols('k01 k10 k20 k21 k23 k30')

    eq1 = (Eq(Derivative(Z0(t), t), -k01*Z0(t) + k10*Z1(t) + k20*Z2(t) + k30*Z3(t)), Eq(Derivative(Z1(t), t),
         k01*Z0(t) - k10*Z1(t) + k21*Z2(t)), Eq(Derivative(Z2(t), t), -(k20 + k21 + k23)*Z2(t)), Eq(Derivative(Z3(t),
         t), k23*Z2(t) - k30*Z3(t)))

    sol1 = [Eq(Z0(t), C1*k10/k01 + C2*(-k10 + k30)*exp(-k30*t)/(k01 + k10 - k30) - C3*exp(t*(-k01 - k10)) + C4*(-k10*k20 - k10*k21 + k10*k30 + k20**2 + k20*k21 + k20*k23 - k20*k30 - k23*k30)*exp(t*(-k20 - k21 - k23))/(k23*(-k01 - k10 + k20 + k21 + k23))),
        Eq(Z1(t), C1 - C2*k01*exp(-k30*t)/(k01 + k10 - k30) + C3*exp(t*(-k01 - k10)) + C4*(-k01*k20 - k01*k21 + k01*k30 + k20*k21 + k21**2 + k21*k23 - k21*k30)*exp(t*(-k20 - k21 - k23))/(k23*(-k01 - k10 + k20 + k21 + k23))),
        Eq(Z2(t), C4*(-k20 - k21 - k23 + k30)*exp(t*(-k20 - k21 - k23))/k23),
        Eq(Z3(t), C2*exp(-k30*t) + C4*exp(t*(-k20 - k21 - k23)))]

    assert dsolve(eq1, simplify=False) == sol1
    assert checksysodesol(eq1, sol1) == (True, [0, 0, 0, 0])

    x, y, z = symbols('x y z', cls=Function)
    k2, k3 = symbols('k2 k3')
    eq2 = (
       Eq(Derivative(z(t), t), k2 * y(t)),
       Eq(Derivative(x(t), t), k3 * y(t)),
       Eq(Derivative(y(t), t), (-k2 - k3) * y(t))
    )
    sol2 = {Eq(z(t), C1 - C3 * k2 * exp(t * (-k2 - k3)) / (k2 + k3)),
           Eq(x(t), C2 - C3 * k3 * exp(t * (-k2 - k3)) / (k2 + k3)),
           Eq(y(t), C3 * exp(t * (-k2 - k3)))}
    assert set(dsolve(eq2)) == sol2
    assert checksysodesol(eq2, sol2) == (True, [0, 0, 0])

    u, v, w = symbols('u v w', cls=Function)
    eq3 = [4 * u(t) - v(t) - 2 * w(t) + Derivative(u(t), t),
          2 * u(t) + v(t) - 2 * w(t) + Derivative(v(t), t),
          5 * u(t) + v(t) - 3 * w(t) + Derivative(w(t), t)]
    sol3 = [Eq(u(t), C1*exp(-2*t) + C2*cos(sqrt(3)*t)/2 - C3*sin(sqrt(3)*t)/2 + sqrt(3)*(C2*sin(sqrt(3)*t)
            + C3*cos(sqrt(3)*t))/6), Eq(v(t), C2*cos(sqrt(3)*t)/2 - C3*sin(sqrt(3)*t)/2 + sqrt(3)*(C2*sin(sqrt(3)*t)
            + C3*cos(sqrt(3)*t))/6), Eq(w(t), C1*exp(-2*t) + C2*cos(sqrt(3)*t) - C3*sin(sqrt(3)*t))]
    assert dsolve(eq3) == sol3
    assert checksysodesol(eq3, sol3) == (True, [0, 0, 0])

    tw = Rational(2, 9)
    eq4 = [Eq(x(t).diff(t), 2 * x(t) + y(t) - tw * 4 * z(t) - tw * w(t)),
          Eq(y(t).diff(t), 2 * y(t) + 8 * tw * z(t) + 2 * tw * w(t)),
          Eq(z(t).diff(t), Rational(37, 9) * z(t) - tw * w(t)), Eq(w(t).diff(t), 22 * tw * w(t) - 2 * tw * z(t))]

    sol4 = [Eq(x(t), (C1 + C2*t)*exp(2*t)),
            Eq(y(t), C2*exp(2*t) + 2*C3*exp(4*t)),
            Eq(z(t), 2*C3*exp(4*t) - C4*exp(5*t)/4),
            Eq(w(t), C3*exp(4*t) + C4*exp(5*t))]

    assert dsolve(eq4) == sol4
    assert checksysodesol(eq4, sol4) == (True, [0, 0, 0, 0])

    # Regression test case for issue #15574
    # https://github.com/sympy/sympy/issues/15574
    eq5 = [Eq(x(t).diff(t), x(t)), Eq(y(t).diff(t), y(t)), Eq(z(t).diff(t), z(t)), Eq(w(t).diff(t), w(t))]
    sol5 = [Eq(x(t), C1*exp(t)), Eq(y(t), C2*exp(t)), Eq(z(t), C3*exp(t)), Eq(w(t), C4*exp(t))]
    assert dsolve(eq5) == sol5
    assert checksysodesol(eq5, sol5) == (True, [0, 0, 0, 0])

    eq6 = [Eq(x(t).diff(t), x(t) + y(t)), Eq(y(t).diff(t), y(t) + z(t)),
          Eq(z(t).diff(t), z(t) + Rational(-1, 8) * w(t)),
          Eq(w(t).diff(t), Rational(1, 2) * (w(t) + z(t)))]

    sol6 = [Eq(x(t), (C3 + C4*t)*exp(t) + (4*C1 + 4*C2*t + 48*C2)*exp(3*t/4)),
            Eq(y(t), C4*exp(t) + (-C1 - C2*t - 8*C2)*exp(3*t/4)),
            Eq(z(t), (C1/4 + C2*t/4 + C2)*exp(3*t/4)),
            Eq(w(t), (C1/2 + C2*t/2)*exp(3*t/4))]

    assert dsolve(eq6) == sol6
    assert checksysodesol(eq6, sol6) == (True, [0, 0, 0, 0])

    # Regression test case for issue #15574
    # https://github.com/sympy/sympy/issues/15574
    eq7 = [Eq(x(t).diff(t), x(t)), Eq(y(t).diff(t), y(t)), Eq(z(t).diff(t), z(t)),
          Eq(w(t).diff(t), w(t)), Eq(u(t).diff(t), u(t))]

    sol7 = [Eq(x(t), C1*exp(t)), Eq(y(t), C2*exp(t)), Eq(z(t), C3*exp(t)), Eq(w(t), C4*exp(t)),
           Eq(u(t), C5*exp(t))]

    assert dsolve(eq7) == sol7
    assert checksysodesol(eq7, sol7) == (True, [0, 0, 0, 0, 0])

    eq8 = [Eq(x(t).diff(t), 2 * x(t) + y(t)), Eq(y(t).diff(t), 2 * y(t)),
          Eq(z(t).diff(t), 4 * z(t)), Eq(w(t).diff(t), 5 * w(t) + u(t)),
          Eq(u(t).diff(t), 5 * u(t))]

    sol8 = [Eq(x(t), (C1 + C2*t)*exp(2*t)), Eq(y(t), C2*exp(2*t)), Eq(z(t), C3*exp(4*t)), Eq(w(t), (C4 + C5*t)*exp(5*t)),
            Eq(u(t), C5*exp(5*t))]

    assert dsolve(eq8) == sol8
    assert checksysodesol(eq8, sol8) == (True, [0, 0, 0, 0, 0])

    # Regression test case for issue #15574
    # https://github.com/sympy/sympy/issues/15574
    eq9 = [Eq(x(t).diff(t), x(t)), Eq(y(t).diff(t), y(t)), Eq(z(t).diff(t), z(t))]
    sol9 = [Eq(x(t), C1*exp(t)), Eq(y(t), C2*exp(t)), Eq(z(t), C3*exp(t))]
    assert dsolve(eq9) == sol9
    assert checksysodesol(eq9, sol9) == (True, [0, 0, 0])

    # Regression test case for issue #15407
    # https://github.com/sympy/sympy/issues/15407
    a_b, a_c = symbols('a_b a_c', real=True)

    eq10 = [Eq(x(t).diff(t), (-a_b - a_c)*x(t)), Eq(y(t).diff(t), a_b*y(t)), Eq(z(t).diff(t), a_c*x(t))]
    sol10 = [Eq(x(t), -C3*(a_b + a_c)*exp(t*(-a_b - a_c))/a_c), Eq(y(t), C2*exp(a_b*t)),
            Eq(z(t), C1 + C3*exp(t*(-a_b - a_c)))]
    assert dsolve(eq10) == sol10
    assert checksysodesol(eq10, sol10) == (True, [0, 0, 0])

    # Regression test case for issue #14312
    # https://github.com/sympy/sympy/issues/14312
    eq11 = (Eq(Derivative(x(t),t), k3*y(t)), Eq(Derivative(y(t),t), -(k3+k2)*y(t)), Eq(Derivative(z(t),t), k2*y(t)))
    sol11 = [Eq(x(t), C1 + C3*k3*exp(t*(-k2 - k3))/k2), Eq(y(t), -C3*(k2 + k3)*exp(t*(-k2 - k3))/k2),
            Eq(z(t), C2 + C3*exp(t*(-k2 - k3)))]
    assert dsolve(eq11) == sol11
    assert checksysodesol(eq11, sol11) == (True, [0, 0, 0])

    # Regression test case for issue #14312
    # https://github.com/sympy/sympy/issues/14312
    eq12 = (Eq(Derivative(z(t),t), k2*y(t)), Eq(Derivative(x(t),t), k3*y(t)), Eq(Derivative(y(t),t), -(k3+k2)*y(t)))
    sol12 = [Eq(z(t), C1 - C3*k2*exp(t*(-k2 - k3))/(k2 + k3)), Eq(x(t), C2 - C3*k3*exp(t*(-k2 - k3))/(k2 + k3)),
            Eq(y(t), C3*exp(t*(-k2 - k3)))]
    assert dsolve(eq12) == sol12
    assert checksysodesol(eq12, sol12) == (True, [0, 0, 0])

    # Regression test case for issue #15474
    # https://github.com/sympy/sympy/issues/15474
    eq13 = [Eq(diff(f(t), t), 2 * f(t) + g(t)),
         Eq(diff(g(t), t), a * f(t))]
    sol13 = [Eq(f(t), -C1*exp(t*(1 - sqrt(a + 1)))/(sqrt(a + 1) + 1) + C2*exp(t*(sqrt(a + 1) + 1))/(sqrt(a + 1) - 1)),
            Eq(g(t), C1*exp(t*(1 - sqrt(a + 1))) + C2*exp(t*(sqrt(a + 1) + 1)))]

    assert dsolve(eq13) == sol13
    assert checksysodesol(eq13, sol13) == (True, [0, 0])

    eq14 = [Eq(f(t).diff(t), 2 * g(t) - 3 * h(t)),
           Eq(g(t).diff(t), 4 * h(t) - 2 * f(t)),
           Eq(h(t).diff(t), 3 * f(t) - 4 * g(t))]
    sol14 = [Eq(f(t), 2*C1 - 8*C2*cos(sqrt(29)*t)/25 + 8*C3*sin(sqrt(29)*t)/25 - 3*sqrt(29)*(C2*sin(sqrt(29)*t)
            + C3*cos(sqrt(29)*t))/25), Eq(g(t), 3*C1/2 - 6*C2*cos(sqrt(29)*t)/25 + 6*C3*sin(sqrt(29)*t)/25
            + 4*sqrt(29)*(C2*sin(sqrt(29)*t) + C3*cos(sqrt(29)*t))/25), Eq(h(t), C1 + C2*cos(sqrt(29)*t)
            - C3*sin(sqrt(29)*t))]

    assert dsolve(eq14) == sol14
    assert checksysodesol(eq14, sol14) == (True, [0, 0, 0])

    eq15 = [Eq(2 * f(t).diff(t), 3 * 4 * (g(t) - h(t))),
          Eq(3 * g(t).diff(t), 2 * 4 * (h(t) - f(t))),
          Eq(4 * h(t).diff(t), 2 * 3 * (f(t) - g(t)))]
    sol15 = [Eq(f(t), C1 - 16*C2*cos(sqrt(29)*t)/13 + 16*C3*sin(sqrt(29)*t)/13 - 6*sqrt(29)*(C2*sin(sqrt(29)*t)
            + C3*cos(sqrt(29)*t))/13), Eq(g(t), C1 - 16*C2*cos(sqrt(29)*t)/13 + 16*C3*sin(sqrt(29)*t)/13
            + 8*sqrt(29)*(C2*sin(sqrt(29)*t) + C3*cos(sqrt(29)*t))/39), Eq(h(t), C1 + C2*cos(sqrt(29)*t) - C3*sin(sqrt(29)*t))]

    assert dsolve(eq15) == sol15
    assert checksysodesol(eq15, sol15) == (True, [0, 0, 0])

    eq16 = (Eq(diff(x(t), t), 21 * x(t)), Eq(diff(y(t), t), 17 * x(t) + 3 * y(t)),
           Eq(diff(z(t), t), 5 * x(t) + 7 * y(t) + 9 * z(t)))
    sol16 = [Eq(x(t), 216*C3*exp(21*t)/209), Eq(y(t), -6*C1*exp(3*t)/7 + 204*C3*exp(21*t)/209),
            Eq(z(t), C1*exp(3*t) + C2*exp(9*t) + C3*exp(21*t))]

    assert dsolve(eq16) == sol16
    assert checksysodesol(eq16, sol16) == (True, [0, 0, 0])

    eq17 = (Eq(diff(x(t),t),3*y(t)-11*z(t)),Eq(diff(y(t),t),7*z(t)-3*x(t)),Eq(diff(z(t),t),11*x(t)-7*y(t)))
    sol17 = [Eq(x(t), 7*C1/3 - 21*C2*cos(sqrt(179)*t)/170 + 21*C3*sin(sqrt(179)*t)/170 - 11*sqrt(179)*(C2*sin(sqrt(179)*t)
            + C3*cos(sqrt(179)*t))/170), Eq(y(t), 11*C1/3 - 33*C2*cos(sqrt(179)*t)/170 + 33*C3*sin(sqrt(179)*t)/170
            + 7*sqrt(179)*(C2*sin(sqrt(179)*t) + C3*cos(sqrt(179)*t))/170), Eq(z(t), C1 + C2*cos(sqrt(179)*t)
            - C3*sin(sqrt(179)*t))]

    assert dsolve(eq17) == sol17
    assert checksysodesol(eq17, sol17) == (True, [0, 0, 0])

    eq18 = (Eq(3*diff(x(t),t),4*5*(y(t)-z(t))),Eq(4*diff(y(t),t),3*5*(z(t)-x(t))),Eq(5*diff(z(t),t),3*4*(x(t)-y(t))))
    sol18 = [Eq(x(t), C1 - C2*cos(5*sqrt(2)*t) + C3*sin(5*sqrt(2)*t) - 4*sqrt(2)*(C2*sin(5*sqrt(2)*t) + C3*cos(5*sqrt(2)*t))/3),
            Eq(y(t), C1 - C2*cos(5*sqrt(2)*t) + C3*sin(5*sqrt(2)*t) + 3*sqrt(2)*(C2*sin(5*sqrt(2)*t) + C3*cos(5*sqrt(2)*t))/4),
            Eq(z(t), C1 + C2*cos(5*sqrt(2)*t) - C3*sin(5*sqrt(2)*t))]

    assert dsolve(eq18) == sol18
    assert checksysodesol(eq18, sol18) == (True, [0, 0, 0])

    eq19 = (Eq(diff(x(t),t),4*x(t) - z(t)),Eq(diff(y(t),t),2*x(t)+2*y(t)-z(t)),Eq(diff(z(t),t),3*x(t)+y(t)))
    sol19 = [Eq(x(t), (C1 + C2*t + 2*C2 + C3*t**2/2 + 2*C3*t + C3)*exp(2*t)),
            Eq(y(t), (C1 + C2*t + 2*C2 + C3*t**2/2 + 2*C3*t)*exp(2*t)),
            Eq(z(t), (2*C1 + 2*C2*t + 3*C2 + C3*t**2 + 3*C3*t)*exp(2*t))]

    assert dsolve(eq19) == sol19
    assert checksysodesol(eq19, sol19) == (True, [0, 0, 0])

    eq20 = (Eq(diff(x(t),t),4*x(t) - y(t) - 2*z(t)),Eq(diff(y(t),t),2*x(t) + y(t)- 2*z(t)),Eq(diff(z(t),t),5*x(t)-3*z(t)))
    sol20 = [Eq(x(t), C1*exp(2*t) - C2*sin(t)/5 + 3*C2*cos(t)/5 - 3*C3*sin(t)/5 - C3*cos(t)/5),
             Eq(y(t), -C2*sin(t)/5 + 3*C2*cos(t)/5 - 3*C3*sin(t)/5 - C3*cos(t)/5),
             Eq(z(t), C1*exp(2*t) + C2*cos(t) - C3*sin(t))]

    assert dsolve(eq20) == sol20
    assert checksysodesol(eq20, sol20) == (True, [0, 0, 0])

    eq21 = (Eq(diff(x(t),t), 9*y(t)), Eq(diff(y(t),t), 12*x(t)))
    sol21 = [Eq(x(t), -sqrt(3)*C1*exp(-6*sqrt(3)*t)/2 + sqrt(3)*C2*exp(6*sqrt(3)*t)/2),
            Eq(y(t), C1*exp(-6*sqrt(3)*t) + C2*exp(6*sqrt(3)*t))]

    assert dsolve(eq21) == sol21
    assert checksysodesol(eq21, sol21) == (True, [0, 0])

    eq22 = (Eq(diff(x(t),t), 2*x(t) + 4*y(t)), Eq(diff(y(t),t), 12*x(t) + 41*y(t)))
    sol22 = [Eq(x(t), C1*(-sqrt(1713)/24 + Rational(-13, 8))*exp(t*(Rational(43, 2) - sqrt(1713)/2)) \
            + C2*(Rational(-13, 8) + sqrt(1713)/24)*exp(t*(sqrt(1713)/2 + Rational(43, 2)))),
            Eq(y(t), C1*exp(t*(Rational(43, 2) - sqrt(1713)/2)) + C2*exp(t*(sqrt(1713)/2 + Rational(43, 2))))]

    assert dsolve(eq22) == sol22
    assert checksysodesol(eq22, sol22) == (True, [0, 0])

    eq23 = (Eq(diff(x(t),t), x(t) + y(t)), Eq(diff(y(t),t), -2*x(t) + 2*y(t)))
    sol23 = [Eq(x(t), (C1*cos(sqrt(7)*t/2)/4 - C2*sin(sqrt(7)*t/2)/4 + sqrt(7)*(C1*sin(sqrt(7)*t/2)
                        + C2*cos(sqrt(7)*t/2))/4)*exp(3*t/2)),
            Eq(y(t), (C1*cos(sqrt(7)*t/2) - C2*sin(sqrt(7)*t/2))*exp(3*t/2))]

    assert dsolve(eq23) == sol23
    assert checksysodesol(eq23, sol23) == (True, [0, 0])

    # Regression test case for issue #15474
    # https://github.com/sympy/sympy/issues/15474
    a = Symbol("a", real=True)
    eq24 = [x(t).diff(t) - a*y(t), y(t).diff(t) + a*x(t)]
    sol24 = [Eq(x(t), C1*sin(a*t) + C2*cos(a*t)), Eq(y(t), C1*cos(a*t) - C2*sin(a*t))]

    assert dsolve(eq24) == sol24
    assert checksysodesol(eq24, sol24) == (True, [0, 0])

    # Regression test case for issue #19150
    # https://github.com/sympy/sympy/issues/19150
    eq25 = [Eq(Derivative(f(t), t), 0),
           Eq(Derivative(g(t), t), 1/(c*b)* ( -2*g(t)+x(t)+f(t) )  ),
           Eq(Derivative(x(t), t), 1/(c*b)* ( -2*x(t)+g(t)+y(t) ) ),
           Eq(Derivative(y(t), t), 1/(c*b)* ( -2*y(t)+x(t)+h(t) ) ),
           Eq(Derivative(h(t), t), 0)]

    sol25 = [Eq(f(t), 4*C1 - 3*C2),
             Eq(g(t), 3*C1 - 2*C2 - C3*exp(-2*t/(b*c)) + C4*exp(t*(-2 - sqrt(2))/(b*c)) + C5*exp(t*(-2 + sqrt(2))/(b*c))),
             Eq(x(t), 2*C1 - C2 - sqrt(2)*C4*exp(t*(-2 - sqrt(2))/(b*c)) + sqrt(2)*C5*exp(t*(-2 + sqrt(2))/(b*c))),
             Eq(y(t), C1 + C3*exp(-2*t/(b*c)) + C4*exp(t*(-2 - sqrt(2))/(b*c)) + C5*exp(t*(-2 + sqrt(2))/(b*c))),
             Eq(h(t), C2)]

    assert dsolve(eq25) == sol25
    assert checksysodesol(eq25, sol25) == (True, [0, 0, 0, 0, 0])

    eq26 = [Eq(diff(f(t), t), 2*f(t)), Eq(diff(g(t), t), 3*f(t) + 7*g(t))]
    sol26 = [Eq(f(t), -5*C1*exp(2*t)/3), Eq(g(t), C1*exp(2*t) + C2*exp(7*t))]
    assert dsolve(eq26) == sol26
    assert checksysodesol(eq26, sol26) == (True, [0, 0])

    eq27 = [Eq(diff(f(t), t), -9*I*f(t) - 4*g(t)), Eq(diff(g(t), t), -4*I*g(t))]
    sol27 = [Eq(f(t), C1*exp(-9*I*t) + 4*I*C2*exp(-4*I*t)/5), Eq(g(t), C2*exp(-4*I*t))]
    assert dsolve(eq27) == sol27
    assert checksysodesol(eq27, sol27) == (True, [0, 0])

    eq28 = [Eq(diff(f(t), t), -9*I*f(t)), Eq(diff(g(t), t), -4*I*g(t))]
    sol28 = [Eq(f(t), C1*exp(-9*I*t)), Eq(g(t), C2*exp(-4*I*t))]
    assert dsolve(eq28) == sol28
    assert checksysodesol(eq28, sol28) == (True, [0, 0])

    eq29 = [Eq(Derivative(f(t), t), 0), Eq(Derivative(g(t), t), 0)]
    sol29 = [Eq(f(t), C1), Eq(g(t), C2)]
    assert dsolve(eq29) == sol29
    assert checksysodesol(eq29, sol29) == (True, [0, 0])

    eq30 = [Eq(Derivative(f(t), t), f(t)), Eq(Derivative(g(t), t), 0)]
    sol30 = [Eq(f(t), C2 * exp(t)), Eq(g(t), C1)]
    assert dsolve(eq30) == sol30
    assert checksysodesol(eq30, sol30) == (True, [0, 0])

    eq31 = [Eq(Derivative(f(t), t), g(t)), Eq(Derivative(g(t), t), 0)]
    sol31 = [Eq(f(t), C1 + C2 * t), Eq(g(t), C2)]
    assert dsolve(eq31) == sol31
    assert checksysodesol(eq31, sol31) == (True, [0, 0])

    eq32 = [Eq(Derivative(f(t), t), 0), Eq(Derivative(g(t), t), f(t))]
    sol32 = [Eq(f(t), C2), Eq(g(t), C1 + C2 * t)]
    assert dsolve(eq32) == sol32
    assert checksysodesol(eq32, sol32) == (True, [0, 0])

    eq33 = [Eq(Derivative(f(t), t), 0), Eq(Derivative(g(t), t), g(t))]
    sol33 = [Eq(f(t), C1), Eq(g(t), C2 * exp(t))]
    assert dsolve(eq33) == sol33
    assert checksysodesol(eq33, sol33) == (True, [0, 0])

    eq34 = [Eq(Derivative(f(t), t), f(t)), Eq(Derivative(g(t), t), I * g(t))]
    sol34 = [Eq(f(t), C1 * exp(t)), Eq(g(t), C2 * exp(I * t))]
    assert dsolve(eq34) == sol34
    assert checksysodesol(eq34, sol34) == (True, [0, 0])

    eq35 = [Eq(Derivative(f(t), t), I * f(t)), Eq(Derivative(g(t), t), -I * g(t))]
    sol35 = [Eq(f(t), C2 * exp(I * t)), Eq(g(t), C1 * exp(-I * t))]
    assert dsolve(eq35) == sol35
    assert checksysodesol(eq35, sol35) == (True, [0, 0])

    eq36 = [Eq(Derivative(f(t), t), I * g(t)), Eq(Derivative(g(t), t), 0)]
    sol36 = [Eq(f(t), I * (C1 + C2 * t)), Eq(g(t), C2)]
    assert dsolve(eq36) == sol36
    assert checksysodesol(eq36, sol36) == (True, [0, 0])

    eq37 = [Eq(Derivative(f(t), t), I * g(t)), Eq(Derivative(g(t), t), I * f(t))]
    sol37 = [Eq(f(t), -C1 * exp(-I * t) + C2 * exp(I * t)), Eq(g(t), C1 * exp(-I * t) + C2 * exp(I * t))]
    assert dsolve(eq37) == sol37
    assert checksysodesol(eq37, sol37) == (True, [0, 0])


def test_sysode_linear_neq_order1_type2():
    f, g, h, k = symbols('f g h k', cls=Function)
    x, t, a, b, c, d = symbols('x t a b c d')

    eq1 = [Eq(diff(f(x), x),  f(x) + g(x) + 5),
           Eq(diff(g(x), x), -f(x) - g(x) + 7)]
    sol1 = [Eq(f(x), C1 + C2*x + C2 + x*Integral(12, x) + Integral(12, x) + Integral(-12*x - 7, x)), Eq(g(x), -C1 -
                C2*x - x*Integral(12, x) - Integral(-12*x - 7, x))]
    assert dsolve(eq1) == sol1
    assert checksysodesol(eq1, sol1) == (True, [0, 0])

    eq2 = [Eq(diff(f(x), x), f(x) + g(x) + 5),
           Eq(diff(g(x), x), f(x) + g(x) + 7)]
    sol2 = [Eq(f(x), -C1 + C2*exp(2*x) + exp(2*x)*Integral(6*exp(-2*x), x) - Integral(1, x)), Eq(g(x), C1 + C2*exp(2*x)
                + exp(2*x)*Integral(6*exp(-2*x), x) + Integral(1, x))]
    assert dsolve(eq2) == sol2
    assert checksysodesol(eq2, sol2) == (True, [0, 0])

    eq3 = [Eq(diff(f(x), x), f(x) + 5), Eq(diff(g(x), x), f(x) + 7)]
    sol3 = [Eq(f(x), C2*exp(x) + exp(x)*Integral(5*exp(-x), x)), Eq(g(x), C1 + C2*exp(x) + exp(x)*Integral(5*exp(-x), x)
                + Integral(2, x))]
    assert dsolve(eq3) == sol3
    assert checksysodesol(eq3, sol3) == (True, [0, 0])

    eq4 = [Eq(diff(f(x), x), f(x) + exp(x)), Eq(diff(g(x), x), f(x) + g(x) + x*exp(x))]
    sol4 = [Eq(f(x), (C2 + Integral(1, x))*exp(x)), Eq(g(x), (C1 + C2*x + x*Integral(1, x) + Integral(0, x))*exp(x))]
    assert dsolve(eq4) == sol4
    assert checksysodesol(eq4, sol4) == (True, [0, 0])

    eq5 = [Eq(diff(f(x), x), f(x) + g(x) + 5*x), Eq(diff(g(x), x), f(x) - g(x))]
    sol5 = [Eq(f(x), C2*exp(sqrt(2)*x) + sqrt(2)*C2*exp(sqrt(2)*x) + (-sqrt(2)*C1
            + C1 - sqrt(2)*Integral(5*sqrt(2)*x*exp(sqrt(2)*x)/(-4 + 2*sqrt(2)) -
            5*x*exp(sqrt(2)*x)/(-4 + 2*sqrt(2)), x) +
            Integral(5*sqrt(2)*x*exp(sqrt(2)*x)/(-4 + 2*sqrt(2)) -
            5*x*exp(sqrt(2)*x)/(-4 + 2*sqrt(2)), x))*exp(-sqrt(2)*x) +
            exp(sqrt(2)*x)*Integral(5*sqrt(2)*x*exp(-sqrt(2)*x)/4, x) +
            sqrt(2)*exp(sqrt(2)*x)*Integral(5*sqrt(2)*x*exp(-sqrt(2)*x)/4, x)),
            Eq(g(x), C2*exp(sqrt(2)*x) + (C1 +
            Integral(5*sqrt(2)*x*exp(sqrt(2)*x)/(-4 + 2*sqrt(2)) -
            5*x*exp(sqrt(2)*x)/(-4 + 2*sqrt(2)), x))*exp(-sqrt(2)*x) +
            exp(sqrt(2)*x)*Integral(5*sqrt(2)*x*exp(-sqrt(2)*x)/4, x))]
    assert dsolve(eq5) == sol5
    assert checksysodesol(eq5, sol5) == (True, [0, 0])

    eq6 = [Eq(diff(f(x), x), -9*f(x) - 4*g(x)),
         Eq(diff(g(x), x), -4*g(x)),
         Eq(diff(h(x), x), h(x) + exp(x))]
    sol6 = [Eq(f(x), (C1 + Integral(0, x))*exp(-9*x) + (-4*C2/5 - 4*Integral(0,
            x)/5)*exp(-4*x)), Eq(g(x), (C2 + Integral(0, x))*exp(-4*x)), Eq(h(x),
            (C3 + Integral(1, x))*exp(x))]
    assert dsolve(eq6) == sol6
    assert checksysodesol(eq6, sol6) == (True, [0, 0, 0])

    # Regression test case for issue #8859
    # https://github.com/sympy/sympy/issues/8859
    eq7 = [Eq(diff(f(t),t), f(t) + 3*t), Eq(diff(g(t),t), g(t))]
    sol7 = [Eq(f(t), C1*exp(t) + exp(t)*Integral(3*t*exp(-t), t)), Eq(g(t),
            C2*exp(t) + exp(t)*Integral(0, t))]
    assert dsolve(eq7) == sol7
    assert checksysodesol(eq7, sol7) == (True, [0, 0])

    # Regression test case for issue #8567
    # https://github.com/sympy/sympy/issues/8567
    eq8 = [Eq(f(t).diff(t), f(t) + 2*g(t)), Eq(g(t).diff(t), -2*f(t) + g(t) + 2*exp(t))]
    sol8 = [Eq(f(t), C1*exp(t)*sin(2*t) + C2*exp(t)*cos(2*t) +
            exp(t)*sin(2*t)*Integral(-2*sin(2*t)**2/cos(2*t) + 2/cos(2*t), t) +
            exp(t)*cos(2*t)*Integral(-2*sin(2*t), t)), Eq(g(t), C1*exp(t)*cos(2*t)
            - C2*exp(t)*sin(2*t) - exp(t)*sin(2*t)*Integral(-2*sin(2*t), t) +
            exp(t)*cos(2*t)*Integral(-2*sin(2*t)**2/cos(2*t) + 2/cos(2*t), t))]
    assert dsolve(eq8) == sol8
    assert checksysodesol(eq8, sol8) == (True, [0, 0])

    # Regression test case for issue #19150
    # https://github.com/sympy/sympy/issues/19150
    eq9 = [Eq(Derivative(f(t), t), 1 / (a * b) * (-2 * f(t) + g(t) + c)),
          Eq(Derivative(g(t), t), 1 / (a * b) * (-2 * g(t) + f(t) + h(t))),
          Eq(Derivative(h(t), t), 1 / (a * b) * (-2 * h(t) + g(t) + d))]
    sol9 = [Eq(f(t), (-C1 + C2*exp(-sqrt(2)*t/(a*b)) + C3*exp(sqrt(2)*t/(a*b)) +
            exp(sqrt(2)*t/(a*b))*Integral(c*exp(-sqrt(2)*t/(a*b) +
            2*t/(a*b))/(4*a*b) + d*exp(-sqrt(2)*t/(a*b) + 2*t/(a*b))/(4*a*b), t) -
            Integral(-c*exp(2*t/(a*b))/(2*a*b) + d*exp(2*t/(a*b))/(2*a*b), t) +
            exp(-sqrt(2)*t/(a*b))*Integral(c*exp(sqrt(2)*t/(a*b) +
            2*t/(a*b))/(4*a*b) + d*exp(sqrt(2)*t/(a*b) + 2*t/(a*b))/(4*a*b),
            t))*exp(-2*t/(a*b))), Eq(g(t), (-sqrt(2)*C2*exp(-sqrt(2)*t/(a*b)) +
            sqrt(2)*C3*exp(sqrt(2)*t/(a*b)) +
            sqrt(2)*exp(sqrt(2)*t/(a*b))*Integral(c*exp(-sqrt(2)*t/(a*b) +
            2*t/(a*b))/(4*a*b) + d*exp(-sqrt(2)*t/(a*b) + 2*t/(a*b))/(4*a*b), t) -
            sqrt(2)*exp(-sqrt(2)*t/(a*b))*Integral(c*exp(sqrt(2)*t/(a*b) +
            2*t/(a*b))/(4*a*b) + d*exp(sqrt(2)*t/(a*b) + 2*t/(a*b))/(4*a*b),
            t))*exp(-2*t/(a*b))), Eq(h(t), (C1 + C2*exp(-sqrt(2)*t/(a*b)) +
            C3*exp(sqrt(2)*t/(a*b)) +
            exp(sqrt(2)*t/(a*b))*Integral(c*exp(-sqrt(2)*t/(a*b) +
            2*t/(a*b))/(4*a*b) + d*exp(-sqrt(2)*t/(a*b) + 2*t/(a*b))/(4*a*b), t) +
            Integral(-c*exp(2*t/(a*b))/(2*a*b) + d*exp(2*t/(a*b))/(2*a*b), t) +
            exp(-sqrt(2)*t/(a*b))*Integral(c*exp(sqrt(2)*t/(a*b) +
            2*t/(a*b))/(4*a*b) + d*exp(sqrt(2)*t/(a*b) + 2*t/(a*b))/(4*a*b),
            t))*exp(-2*t/(a*b)))]

    assert dsolve(eq9) == sol9
    assert checksysodesol(eq9, sol9) == (True, [0, 0, 0])


def test_sysode_linear_neq_order1_type3():
    f, g, h, k = symbols('f g h k', cls=Function)
    x = symbols('x')
    r = symbols('r', real=True)

    eqs1 = [Eq(diff(f(r), r),  f(r) + r*g(r)),
           Eq(diff(g(r), r),-r*f(r) + g(r))]
    sol1 = [Eq(f(r), (C1*cos(r**2/2) + C2*sin(r**2/2))*exp(r)),
           Eq(g(r), (-C1*sin(r**2/2) + C2*cos(r**2/2))*exp(r))]
    assert dsolve(eqs1) == sol1
    assert checksysodesol(eqs1, sol1) == (True, [0, 0])

    eqs2 = [Eq(diff(f(x), x),  x*f(x) + x**2*g(x)),
           Eq(diff(g(x), x),  2*x**2*f(x) + (x + 3*x**2)*g(x))]
    sol2 = [Eq(f(x), (6*sqrt(17)*C1/(-221 + 51*sqrt(17)) - 34*C1/(-221 + 51*sqrt(17)) - 13*C2/(-51 + 13*sqrt(17))
                        + 3*sqrt(17)*C2/(-51 + 13*sqrt(17)))*exp(-sqrt(17)*x**3/6 + x**3/2 + x**2/2)
                        + (45*sqrt(17)*C1/(-221 + 51*sqrt(17)) - 187*C1/(-221 + 51*sqrt(17)) - 3*sqrt(17)*C2/(-51 + 13*sqrt(17))
                        + 13*C2/(-51 + 13*sqrt(17)))*exp(x**3/2 + sqrt(17)*x**3/6 + x**2/2)),
            Eq(g(x), (102*C1/(-221 + 51*sqrt(17)) - 26*sqrt(17)*C1/(-221 + 51*sqrt(17))
                        + 6*sqrt(17)*C2/(-221 + 51*sqrt(17)) - 34*C2/(-221 + 51*sqrt(17)))*exp(x**3/2
                        + sqrt(17)*x**3/6 + x**2/2) + (26*sqrt(17)*C1/(-221 + 51*sqrt(17)) - 102*C1/(-221 + 51*sqrt(17))
                        + 45*sqrt(17)*C2/(-221 + 51*sqrt(17)) - 187*C2/(-221 + 51*sqrt(17)))*exp(-sqrt(17)*x**3/6
                        + x**3/2 + x**2/2))]

    assert dsolve(eqs2) == sol2
    assert checksysodesol(eqs2, sol2) == (True, [0, 0])

    eqs3 = [Eq(f(x).diff(x), x * f(x) + g(x)), Eq(g(x).diff(x), -f(x) + x * g(x))]
    sol3 = [Eq(f(x), (C1/2 - I*C2/2)*exp(x**2/2 + I*x) + (C1/2 + I*C2/2)*exp(x**2/2 - I*x)),
            Eq(g(x), (-I*C1/2 + C2/2)*exp(x**2/2 - I*x) + (I*C1/2 + C2/2)*exp(x**2/2 + I*x))]
    assert dsolve(eqs3) == sol3
    assert checksysodesol(eqs3, sol3) == (True, [0, 0])

    eqs4 = [Eq(f(x).diff(x), x*(f(x) + g(x) + h(x))), Eq(g(x).diff(x), x*(f(x) + g(x) + h(x))), Eq(h(x).diff(x), x*(f(x) + g(x) + h(x)))]
    sol4 = [Eq(f(x), 2*C1/3 - C2/3 - C3/3 + (C1/3 + C2/3 + C3/3)*exp(3*x**2/2)),
            Eq(g(x), -C1/3 + 2*C2/3 - C3/3 + (C1/3 + C2/3 + C3/3)*exp(3*x**2/2)),
            Eq(h(x), -C1/3 - C2/3 + 2*C3/3 + (C1/3 + C2/3 + C3/3)*exp(3*x**2/2))]
    assert dsolve(eqs4) == sol4
    assert checksysodesol(eqs4, sol4) == (True, [0, 0, 0])

    eqs5 = [Eq(f(x).diff(x), x**2*(f(x) + g(x) + h(x))), Eq(g(x).diff(x), x**2*(f(x) + g(x) + h(x))),
            Eq(h(x).diff(x), x**2*(f(x) + g(x) + h(x)))]
    sol5 = [Eq(f(x), 2*C1/3 - C2/3 - C3/3 + (C1/3 + C2/3 + C3/3)*exp(x**3)),
            Eq(g(x), -C1/3 + 2*C2/3 - C3/3 + (C1/3 + C2/3 + C3/3)*exp(x**3)),
            Eq(h(x), -C1/3 - C2/3 + 2*C3/3 + (C1/3 + C2/3 + C3/3)*exp(x**3))]
    assert dsolve(eqs5) == sol5
    assert checksysodesol(eqs5, sol5) == (True, [0, 0, 0])

    eqs6 = [Eq(Derivative(f(x), x), x*(f(x) + g(x) + h(x) + k(x))),
            Eq(Derivative(g(x), x), x*(f(x) + g(x) + h(x) + k(x))),
            Eq(Derivative(h(x), x), x*(f(x) + g(x) + h(x) + k(x))),
            Eq(Derivative(k(x), x), x*(f(x) + g(x) + h(x) + k(x)))]
    sol6 = [Eq(f(x), 3*C1/4 - C2/4 - C3/4 - C4/4 + (C1/4 + C2/4 + C3/4 + C4/4)*exp(2*x**2)),
            Eq(g(x), -C1/4 + 3*C2/4 - C3/4 - C4/4 + (C1/4 + C2/4 + C3/4 + C4/4)*exp(2*x**2)),
            Eq(h(x), -C1/4 - C2/4 + 3*C3/4 - C4/4 + (C1/4 + C2/4 + C3/4 + C4/4)*exp(2*x**2)),
            Eq(k(x), -C1/4 - C2/4 - C3/4 + 3*C4/4 + (C1/4 + C2/4 + C3/4 + C4/4)*exp(2*x**2))]
    assert dsolve(eqs6) == sol6
    assert checksysodesol(eqs6, sol6) == (True, [0, 0, 0, 0])

    y = symbols("y", real=True)

    eqs7 = [Eq(Derivative(f(y), y), y*f(y) + g(y)), Eq(Derivative(g(y), y), y*g(y) - f(y))]
    sol7 = [Eq(f(y), (C1*cos(y) + C2*sin(y))*exp(y**2/2)), Eq(g(y), (-C1*sin(y) + C2*cos(y))*exp(y**2/2))]
    assert dsolve(eqs7) == sol7
    assert checksysodesol(eqs7, sol7) == (True, [0, 0])


@slow
def test_linear_3eq_order1_type4_slow():
    x, y, z = symbols('x, y, z', cls=Function)
    t = Symbol('t')

    f = t ** 3 + log(t)
    g = t ** 2 + sin(t)
    eq1 = (Eq(diff(x(t), t), (4 * f + g) * x(t) - f * y(t) - 2 * f * z(t)),
                Eq(diff(y(t), t), 2 * f * x(t) + (f + g) * y(t) - 2 * f * z(t)), Eq(diff(z(t), t), 5 * f * x(t) + f * y(
        t) + (-3 * f + g) * z(t)))
    dsolve(eq1)


def test_linear_neq_order1_type2_big_test_cases():
    i, r1, c1, r2, c2, t = symbols('i, r1, c1, r2, c2, t')
    x1 = Function('x1')
    x2 = Function('x2')
    eq1 = r1*c1*Derivative(x1(t), t) + x1(t) - x2(t) - r1*i
    eq2 = r2*c1*Derivative(x1(t), t) + r2*c2*Derivative(x2(t), t) + x2(t) - r2*i
    eq = [eq1, eq2]
    _x1 = c1 ** 2 * r1 ** 2 + 2 * c1 ** 2 * r1 * r2 + c1 ** 2 * r2 ** 2 - 2 * c1 * c2 * r1 * r2 + 2 * c1 * c2 * r2 ** 2 + c2 ** 2 * r2 ** 2
    _x2 = Integral(i * r2 * exp(-sqrt(_x1) * t / (2 * c1 * c2 * r1 * r2) + t / (2 * c2 * r2)
                                + t / (2 * c2 * r1) + t / (2 * c1 * r1)) / sqrt(_x1), t)
    _x3 = Integral(-i * r2 * exp(sqrt(_x1) * t / (2 * c1 * c2 * r1 * r2) + t / (2 * c2 * r2)
                                 + t / (2 * c2 * r1) + t / (2 * c1 * r1)) / sqrt(_x1), t)
    _x4 = exp(sqrt(_x1) * t / (2 * c1 * c2 * r1 * r2) - t / (2 * c2 * r2) - t / (2 * c2 * r1) - t / (2 * c1 * r1))
    _x5 = exp(-sqrt(_x1) * t / (2 * c1 * c2 * r1 * r2) - t / (2 * c2 * r2) - t / (2 * c2 * r1) - t / (2 * c1 * r1))
    sol = [
        Eq(x1(t),
           - 2 * C1 * _x5 * c2 * r2 / (sqrt(_x1) + c1 * r1 + c1 * r2 - c2 * r2)
           - 2 * C2 * _x4 * c2 * r2 / (-sqrt(_x1) + c1 * r1 + c1 * r2 - c2 * r2)
           - 2 * _x2 * _x4 * c2 * r2 / (-sqrt(_x1) + c1 * r1 + c1 * r2 - c2 * r2)
           - 2 * _x3 * _x5 * c2 * r2 / (sqrt(_x1) + c1 * r1 + c1 * r2 - c2 * r2)),
        Eq(x2(t), C1 * _x5 + C2 * _x4 + _x2 * _x4 + _x3 * _x5),
    ]
    assert dsolve(eq) == sol
    assert checksysodesol(eq, sol) == (True, [0, 0])


def _de_lorentz_solution():
    m = Symbol("m", real=True)
    q = Symbol("q", real=True)
    t = Symbol("t", real=True)

    e1, e2, e3 = symbols("e1:4", real=True)
    b1, b2, b3 = symbols("b1:4", real=True)
    v1, v2, v3 = symbols("v1:4", cls=Function, real=True)

    eqs = [
        -e1 * q + m * Derivative(v1(t), t) - q * (-b2 * v3(t) + b3 * v2(t)),
        -e2 * q + m * Derivative(v2(t), t) - q * (b1 * v3(t) - b3 * v1(t)),
        -e3 * q + m * Derivative(v3(t), t) - q * (-b1 * v2(t) + b2 * v1(t))
    ]

    x1 = sqrt(b1 ** 2 + b2 ** 2 + b3 ** 2)
    x2 = exp(q * t * sqrt(-b1 ** 2 - b2 ** 2 - b3 ** 2) / m)
    x3 = 1 / (b1 ** 2 * x1 * x2 + b2 ** 2 * x1 * x2)
    x4 = 1 / (2 * b1 ** 2 * m * x2 + 2 * b2 ** 2 * m * x2 + 2 * b3 ** 2 * m * x2)
    x5 = Integral(
        b1 * b3 * e1 * q / (b1 ** 2 * m + b2 ** 2 * m + b3 ** 2 * m)
        + b2 * b3 * e2 * q / (b1 ** 2 * m + b2 ** 2 * m + b3 ** 2 * m)
        + b3 ** 2 * e3 * q / (b1 ** 2 * m + b2 ** 2 * m + b3 ** 2 * m), t)
    x6 = 1 / (2 * b1 ** 3 * b3 * m + 2 * I * b1 ** 2 * b2 * m * x1 + 2 * b1 * b2 ** 2 * b3 * m
              + 2 * b1 * b3 ** 3 * m + 2 * I * b2 ** 3 * m * x1 + 2 * I * b2 * b3 ** 2 * m * x1)
    x7 = Integral(
        b1 ** 2 * e3 * q * x4 - b1 * b3 * e1 * q * x4 + I * b1 * e2 * q * x1 * x4
        + b2 ** 2 * e3 * q * x4 - b2 * b3 * e2 * q * x4 - I * b2 * e1 * q * x1 * x4, t)
    x8 = Integral(
        b1 ** 3 * b2 * e2 * q * x2 * x6 - b1 ** 2 * b2 ** 2 * e1 * q * x2 * x6 - b1 ** 2 * b3 ** 2 * e1 * q * x2 * x6
        - I * b1 ** 2 * b3 * e2 * q * x1 * x2 * x6 + b1 ** 2 * e3 * q * x2 / (
                2 * b1 ** 2 * m + 2 * b2 ** 2 * m + 2 * b3 ** 2 * m)
        + b1 * b2 ** 3 * e2 * q * x2 * x6 - b2 ** 4 * e1 * q * x2 * x6 - b2 ** 2 * b3 ** 2 * e1 * q * x2 * x6
        - I * b2 ** 2 * b3 * e2 * q * x1 * x2 * x6 + b2 ** 2 * e3 * q * x2 / (
                2 * b1 ** 2 * m + 2 * b2 ** 2 * m + 2 * b3 ** 2 * m), t)
    sol = [
        Eq(v1(t),
           C1 * b1 / b3
           - I * C2 * b1 ** 2 * b2 * x3 - C2 * b1 * b3 * x1 * x3 - I * C2 * b2 ** 3 * x3 - I * C2 * b2 * b3 ** 2 * x3
           + I * C3 * b1 ** 2 * b2 * x2 / (b1 ** 2 * x1 + b2 ** 2 * x1) - C3 * b1 * b3 * x1 * x2 / (
                   b1 ** 2 * x1 + b2 ** 2 * x1)
           + I * C3 * b2 ** 3 * x2 / (b1 ** 2 * x1 + b2 ** 2 * x1) + I * C3 * b2 * b3 ** 2 * x2 / (
                   b1 ** 2 * x1 + b2 ** 2 * x1)
           + I * b1 ** 2 * b2 * x2 * x7 / (b1 ** 2 * x1 + b2 ** 2 * x1) - I * b1 ** 2 * b2 * x3 * x8
           - b1 * b3 * x1 * x2 * x7 / (b1 ** 2 * x1 + b2 ** 2 * x1) - b1 * b3 * x1 * x3 * x8 + b1 * x5 / b3
           + I * b2 ** 3 * x2 * x7 / (b1 ** 2 * x1 + b2 ** 2 * x1) - I * b2 ** 3 * x3 * x8
           + I * b2 * b3 ** 2 * x2 * x7 / (b1 ** 2 * x1 + b2 ** 2 * x1) - I * b2 * b3 ** 2 * x3 * x8),
        Eq(v2(t),
           C1 * b2 / b3
           + C2 * b1 * sqrt(-b1 ** 2 - b2 ** 2 - b3 ** 2) / (b1 ** 2 * x2 + b2 ** 2 * x2)
           - C2 * b2 * b3 / (b1 ** 2 * x2 + b2 ** 2 * x2) - I * C3 * b1 * x1 * x2 / (b1 ** 2 + b2 ** 2)
           - C3 * b2 * b3 * x2 / (b1 ** 2 + b2 ** 2) - I * b1 * x1 * x2 * x7 / (b1 ** 2 + b2 ** 2)
           + b1 * x8 * sqrt(-b1 ** 2 - b2 ** 2 - b3 ** 2) / (b1 ** 2 * x2 + b2 ** 2 * x2)
           - b2 * b3 * x2 * x7 / (b1 ** 2 + b2 ** 2) - b2 * b3 * x8 / (b1 ** 2 * x2 + b2 ** 2 * x2) + b2 * x5 / b3),
        Eq(v3(t), C1 + C3 * x2 + x2 * x7 + x5 + (C2 + x8) * exp(-q * t * sqrt(-b1 ** 2 - b2 ** 2 - b3 ** 2) / m)),
    ]

    return eqs, sol


# A very big solution is obtained for this
# test case. To be simplified in future.
def test_linear_new_order1_type2_de_lorentz():
    eqs, sol = _de_lorentz_solution()

    assert dsolve(eqs) == sol


@slow
def test_linear_new_order1_type2_de_lorentz_slow_check():
    if ON_TRAVIS:
        skip("Too slow for travis.")

    eqs, sol = _de_lorentz_solution()
    assert checksysodesol(eqs, sol) == (True, [0, 0, 0])


def _neq_order1_type2_slow():
    RC, t, C, Vs, L, R1, V0, I0 = symbols("RC t C Vs L R1 V0 I0")
    V = Function("V")
    I = Function("I")
    system = [Eq(V(t).diff(t), -1 / RC * V(t) + I(t) / C), Eq(I(t).diff(t), -R1 / L * I(t) - 1 / L * V(t) + Vs / L)]

    x_1 = sqrt(C ** 2 * L ** 2 - 2 * C ** 2 * L * R1 * RC + C ** 2 * R1 ** 2 * RC ** 2 - 4 * C * L * RC ** 2)
    x_2 = 1 / (
            C * L ** 3 - 2 * C * L ** 2 * R1 * RC + C * L * R1 ** 2 * RC ** 2 - 4 * L ** 2 * RC ** 2 - L ** 2 * x_1 +
            L * R1 * RC * x_1)
    x_3 = exp(t / (2 * RC) + R1 * t / (2 * L) + t * x_1 / (2 * C * L * RC))
    x_4 = exp(-t / (2 * RC) - R1 * t / (2 * L) - t * x_1 / (2 * C * L * RC))
    x_5 = Integral(-2 * RC ** 2 * Vs * exp(t / (2 * RC) + R1 * t / (2 * L) - t * x_1 / (2 * C * L * RC)) / (
            C * L ** 2 - 2 * C * L * R1 * RC + C * R1 ** 2 * RC ** 2 - 4 * L * RC ** 2 - L * x_1 + R1 * RC * x_1), t)
    x_6 = Integral(
        C * L ** 2 * Vs * x_2 * x_3 - 2 * C * L * R1 * RC * Vs * x_2 * x_3 + C * R1 ** 2 * RC ** 2 * Vs * x_2 * x_3 -
        2 * L * RC ** 2 * Vs * x_2 * x_3 - L * Vs * x_1 * x_2 * x_3 + R1 * RC * Vs * x_1 * x_2 * x_3,
        t)
    x_7 = exp(-t / (2 * RC) - R1 * t / (2 * L) + t * x_1 / (2 * C * L * RC))
    x_8 = 1 / (C * L - C * R1 * RC + x_1)
    sol = [Eq(V(t), 2 * C1 * L * RC * x_4 / (
            C * L - C * R1 * RC - x_1) + 2 * C2 * L * RC * x_7 * x_8 + 2 * L * RC * x_4 * x_6 / (
                      C * L - C * R1 * RC - x_1) + 2 * L * RC * x_5 * x_7 * x_8),
           Eq(I(t), C1 * x_4 + C2 * x_7 + x_4 * x_6 + x_5 * x_7)]

    return system, sol


# A very big solution is obtained for this
# test case. To be simplified in future.
def test_linear_neq_order1_type2_slow():
    system, sol = _neq_order1_type2_slow()

    assert dsolve(system) == sol


@slow
def test_linear_neq_order1_type2_slow_check():
    if ON_TRAVIS:
        skip("Too slow for travis.")

    system, sol = _neq_order1_type2_slow()

    assert checksysodesol(system, sol) == (True, [0, 0])


def test_linear_3eq_order1_type4_long():

    x, y, z = symbols('x, y, z', cls=Function)
    t = Symbol('t')

    f = t ** 3 + log(t)
    g = t ** 2 + sin(t)
    eq1 = (Eq(diff(x(t), t), (4 * f + g) * x(t) - f * y(t) - 2 * f * z(t)),
                Eq(diff(y(t), t), 2 * f * x(t) + (f + g) * y(t) - 2 * f * z(t)), Eq(diff(z(t), t), 5 * f * x(t) + f * y(
        t) + (-3 * f + g) * z(t)))

    dsolve_sol = dsolve(eq1)
    dsolve_sol1 = [_simpsol(sol) for sol in dsolve_sol]

    x_1 = sqrt(-t ** 6 - 8 * t ** 3 * log(t) + 8 * t ** 3 - 16 * log(t) ** 2 + 32 * log(t) - 16)
    x_2 = sqrt(3)
    x_3 = 8324372644 * C1 * x_1 * x_2 + 4162186322 * C2 * x_1 * x_2 - 8324372644 * C3 * x_1 * x_2
    x_4 = 1 / (1903457163 * t ** 3 + 3825881643 * x_1 * x_2 + 7613828652 * log(t) - 7613828652)
    x_5 = exp(t ** 3 / 3 + t * x_1 * x_2 / 4 - cos(t))
    x_6 = exp(t ** 3 / 3 - t * x_1 * x_2 / 4 - cos(t))
    x_7 = exp(t ** 4 / 2 + t ** 3 / 3 + 2 * t * log(t) - 2 * t - cos(t))
    x_8 = 91238 * C1 * x_1 * x_2 + 91238 * C2 * x_1 * x_2 - 91238 * C3 * x_1 * x_2
    x_9 = 1 / (66049 * t ** 3 - 50629 * x_1 * x_2 + 264196 * log(t) - 264196)
    x_10 = 50629 * C1 / 25189 + 37909 * C2 / 25189 - 50629 * C3 / 25189 - x_3 * x_4
    x_11 = -50629 * C1 / 25189 - 12720 * C2 / 25189 + 50629 * C3 / 25189 + x_3 * x_4
    sol = [Eq(x(t), x_10 * x_5 + x_11 * x_6 + x_7 * (C1 - C2)), Eq(y(t), x_10 * x_5 + x_11 * x_6), Eq(z(t), x_5 * (
            -424 * C1 / 257 - 167 * C2 / 257 + 424 * C3 / 257 - x_8 * x_9) + x_6 * (167 * C1 / 257 + 424 * C2 / 257 -
            167 * C3 / 257 + x_8 * x_9) + x_7 * (C1 - C2))]

    assert dsolve_sol1 == sol
    assert checksysodesol(eq1, dsolve_sol1) == (True, [0, 0, 0])
