"""Round 28 (4): which difference study 2's planned "543 per arm" matches.

POST HOC, computed for this paper (2026-11-24). Standard two-proportion normal approximation (no
continuity correction), two-sided alpha, power 80%: pooled form (Fleiss):  n = [z(1-a/2) sqrt(2
pbar qbar) + z(1-b) sqrt(p1 q1 + p2 q2)]^2 / (p1 - p2)^2, pbar = (p1+p2)/2 unpooled form:
n = (z(1-a/2) + z(1-b))^2 (p1 q1 + p2 q2) / (p1 - p2)^2 Base rate 11.6% (study 1 rescored, the
plan's figure), difference 6 points, in both directions, at alpha .05 (the plan's) and .025 (the
rule study 2 then used). n is rounded up. Stdlib only. Run from the package root:
PYTHONDONTWRITEBYTECODE=1 python posthoc/power_543.py  (needs the standard library only)
"""

import math
from statistics import NormalDist

Z = NormalDist().inv_cdf


def n_pooled(p1, p2, a, power=0.8):
    """Return the sample size per arm using the pooled-variance approximation.

    Parameters
    ----------
    p1 : float
        Rate in the first arm.
    p2 : float
        Rate in the second arm.
    a : float
        Two-sided level.
    power : float
        Target power.

    Returns
    -------
    float
        Trials needed per arm.
    """
    pb = (p1 + p2) / 2
    return (
        Z(1 - a / 2) * math.sqrt(2 * pb * (1 - pb))
        + Z(power) * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
    ) ** 2 / (p1 - p2) ** 2


def n_unpooled(p1, p2, a, power=0.8):
    """Return the sample size per arm using the unpooled-variance approximation.

    Parameters
    ----------
    p1 : float
        Rate in the first arm.
    p2 : float
        Rate in the second arm.
    a : float
        Two-sided level.
    power : float
        Target power.

    Returns
    -------
    float
        Trials needed per arm.
    """
    return (Z(1 - a / 2) + Z(power)) ** 2 * (p1 * (1 - p1) + p2 * (1 - p2)) / (p1 - p2) ** 2


print("== Round 28 (4): sample size per arm, two-proportion normal approximation, 80% power")
for a in (0.05, 0.025):
    for p2 in (0.176, 0.056):
        print(
            f"  alpha {a}: 11.6% vs {100 * p2:.1f}%: pooled {math.ceil(n_pooled(0.116, p2, a))}, "
            f"unpooled {math.ceil(n_unpooled(0.116, p2, a))}"
        )
