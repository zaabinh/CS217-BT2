"""Numerical primitives for the mathematical relations in the report."""
import math


def sin_deg(angle: float) -> float:
    return math.sin(math.radians(angle))


def cos_deg(angle: float) -> float:
    return math.cos(math.radians(angle))


def acos_deg(value: float) -> float:
    """Clamp only machine roundoff, never the domain validation tolerance."""
    if not math.isfinite(value) or not -1 - 1e-12 <= value <= 1 + 1e-12:
        raise ValueError("arccos argument outside [-1, 1]")
    return math.degrees(math.acos(max(-1.0, min(1.0, value))))


def cosine_side(b: float, c: float, angle: float) -> float:
    """Cosine law in half-angle form to avoid subtractive cancellation."""
    scale = max(b, c)
    return scale * math.hypot((b - c) / scale,
                             2 * math.sqrt((b / scale) * (c / scale)) * sin_deg(angle / 2))


def cosine_angle(a: float, b: float, c: float) -> float:
    """Evaluate the cosine-law angle via atan2 to preserve thin-triangle precision.

    The sine numerator is 4*area (Kahan's rearrangement of Heron).
    This is the same unique angle as acos, with no inverse-sine branching.
    """
    scale = max(a, b, c)
    x, y, z = a / scale, b / scale, c / scale
    u, v = max(y, z), min(y, z)
    cosine_numerator = (u-x)*(u+x)+v*v
    sine_numerator = _four_area(x, y, z)
    return math.degrees(math.atan2(sine_numerator, cosine_numerator))


def _four_area(a: float, b: float, c: float) -> float:
    x, y, z = sorted((a, b, c), reverse=True)
    factors = (x+(y+z), z-(x-y), z+(x-y), x+(y-z))
    return math.prod(math.sqrt(factor) for factor in factors)


def heron(p: float, a: float, b: float, c: float) -> float:
    """Kahan's equivalent Heron form; Q02 must validate p before evaluation.

    Rearranging the side differences avoids cancellation in rounded p-a.
    The registry retains p as the required input, exactly as R20 specifies.
    """
    scale = max(a, b, c)
    return ((_four_area(a/scale, b/scale, c/scale)/4)*scale)*scale
