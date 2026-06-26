import sympy
from sympy import symbols, Eq, solve, diff, integrate, simplify, parse_expr, N
from sympy.parsing.sympy_parser import (
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
)
import re

TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application, convert_xor)

def try_solve_math(text: str) -> str | None:
    cleaned = text.strip()
    lowered = cleaned.lower()

    # Производная
    m = re.search(r"производн\w*\s+(.*?)(?:\s+по\s+([a-zA-Zа-яА-Я]+))?$", lowered)
    if m:
        expr_str = m.group(1)
        var_name = m.group(2) or "x"
        try:
            x = symbols(var_name)
            expr = parse_expr(expr_str, transformations=TRANSFORMATIONS)
            result = diff(expr, x)
            return f"d/d{var_name}({expr}) = {simplify(result)}"
        except Exception:
            pass

    # Интеграл
    m = re.search(r"интеграл\w*\s+(?:от\s+)?(.*?)(?:\s+по\s+([a-zA-Zа-яА-Я]+)|\s*dx)?$", lowered)
    if m:
        expr_str = m.group(1)
        var_name = m.group(2) or "x"
        try:
            x = symbols(var_name)
            expr = parse_expr(expr_str, transformations=TRANSFORMATIONS)
            result = integrate(expr, x)
            return f"∫({expr}) d{var_name} = {result} + C"
        except Exception:
            pass

    # Уравнение с =
    if "=" in cleaned and not cleaned.strip().startswith("/"):
        eq_text = re.sub(r"(реши|вычисли|посчитай|уравнение|solve|calculate)", "", cleaned, flags=re.IGNORECASE)
        lhs_str, _, rhs_str = eq_text.partition("=")
        try:
            free_vars = sorted(set(re.findall(r"[a-zA-Zа-яА-Я]+", lhs_str + rhs_str)))
            free_vars = [v for v in free_vars if v.lower() not in ["реши", "вычисли", "посчитай", "уравнение"]]
            if free_vars:
                syms = symbols(" ".join(free_vars))
                if not isinstance(syms, (list, tuple)):
                    syms = (syms,)
                lhs = parse_expr(lhs_str, transformations=TRANSFORMATIONS)
                rhs = parse_expr(rhs_str, transformations=TRANSFORMATIONS)
                solutions = solve(Eq(lhs, rhs), syms)
                return f"{eq_text.strip()} => {solutions}"
        except Exception:
            pass

    # Простое выражение
    expr_candidate = re.sub(r"(реши|вычисли|посчитай|упрости|simplify|solve|calculate)", "", cleaned, flags=re.IGNORECASE).strip(" :,?")
    if expr_candidate:
        try:
            expr = parse_expr(expr_candidate, transformations=TRANSFORMATIONS)
            result = simplify(expr)
            if result.free_symbols:
                return f"{expr_candidate} = {result}"
            else:
                evaluated = N(result)
                return f"{expr_candidate} = {result} ≈ {evaluated}" if result != evaluated else f"{expr_candidate} = {result}"
        except Exception:
            return None
    return None