"""
Child's Pose validator.

Visibility rule:
  If a body part required for a step is NOT VISIBLE, that step scores 0
  with a clear "not visible" message.

NEW (Score-zero hiding):
  Any step whose score == 0 is marked with `hide_from_ui = True` so the UI
  can skip rendering that card. In the FINAL score calculation, those zero
  scores are replaced with 50 (neutral), so a single zero does not crater
  the total.
"""

import math


def calculate_angle(a, b, c):
    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])
    dot = ba[0] * bc[0] + ba[1] * bc[1]
    mag_ba = math.sqrt(ba[0] ** 2 + ba[1] ** 2)
    mag_bc = math.sqrt(bc[0] ** 2 + bc[1] ** 2)
    if mag_ba == 0 or mag_bc == 0:
        return 0
    cos_angle = max(-1, min(1, dot / (mag_ba * mag_bc)))
    return math.degrees(math.acos(cos_angle))


def score_value(deviation, ideal_max, fail_min, curve="quadratic"):
    if deviation <= ideal_max:
        return 100.0
    if deviation >= fail_min:
        return 0.0
    span = fail_min - ideal_max
    over = deviation - ideal_max
    progress = over / span
    if curve == "quadratic":
        return round(100.0 * (1.0 - progress) ** 2, 1)
    return round(100.0 * (1.0 - progress), 1)


def _not_visible(step_num, name, body_part, cue):
    return {
        "step": step_num, "name": name,
        "passed": False, "score": 0.0,
        "issue": f"Cannot evaluate - {body_part} not visible in the frame",
        "cue": cue,
        "not_visible": True,
    }


def check_hips_on_heels(features, visible=True):
    if not visible:
        return _not_visible(1, "Hips on Heels", "hips/legs",
                            "Lower your hips back toward your heels")
    ratio = features["hip_to_heel_ratio"]
    score = score_value(ratio, 0.25, 1.20, "quadratic")
    passed = ratio <= 0.45
    return {
        "step": 1, "name": "Hips on Heels",
        "passed": passed, "score": score,
        "issue": None if passed else
                 "Hips are not sinking back - sit your hips down toward your heels",
        "cue": "Lower your hips back toward your heels",
        "not_visible": False,
    }


def check_torso_fold(features, visible=True):
    if not visible:
        return _not_visible(2, "Torso Folded Forward", "torso (shoulders, hips, knees)",
                            "Fold your chest down toward the floor")
    angle = features["torso_thigh_angle"]
    score = score_value(angle - 10.0, 15.0, 80.0, "quadratic")
    passed = angle <= 35.0
    return {
        "step": 2, "name": "Torso Folded Forward",
        "passed": passed, "score": score,
        "issue": None if passed else
                 "Torso is not folded down - bring your chest closer to your thighs",
        "cue": "Fold your chest down toward the floor, forehead toward the mat",
        "not_visible": False,
    }


def check_arms_extended(features, visible=True):
    if not visible:
        return _not_visible(3, "Arms Extended Forward", "arms (shoulders, elbows, wrists)",
                            "Stretch your arms out in front, palms down")
    e_left = features["left_elbow_angle"]
    e_right = features["right_elbow_angle"]
    worst_elbow = min(e_left, e_right)
    if worst_elbow >= 165:
        elbow_score = 100.0
    else:
        elbow_score = score_value(165 - worst_elbow, 0.0, 50.0, "quadratic")

    ext_left = features["left_arm_extension_ratio"]
    ext_right = features["right_arm_extension_ratio"]
    worst_ext = min(ext_left, ext_right)
    if worst_ext >= 1.85:
        extension_score = 100.0
    else:
        extension_score = score_value(1.85 - worst_ext, 0.0, 0.80, "quadratic")

    asymmetry = abs(e_left - e_right)
    symmetry_score = score_value(asymmetry, 5.0, 35.0, "quadratic")

    score = round(elbow_score * 0.50 + extension_score * 0.30 + symmetry_score * 0.20, 1)

    issues = []
    if worst_elbow < 160:
        issues.append("Elbows are bent - keep your arms actively engaged and straight")
    if worst_ext < 1.70:
        issues.append("Reach your arms further forward")
    if asymmetry > 15:
        issues.append("Arms are not parallel - keep them even")

    passed = len(issues) == 0
    issue = " - ".join(issues) if issues else None

    return {
        "step": 3, "name": "Arms Extended Forward",
        "passed": passed, "score": score,
        "issue": issue,
        "cue": "Stretch your arms out in front, palms down, elbows straight",
        "not_visible": False,
    }


def check_spine_lengthened(features, visible=True):
    if not visible:
        return _not_visible(4, "Spine Lengthened", "spine line (hips, shoulders, wrists)",
                            "Lengthen the spine - reach fingertips forward, sit hips back")
    deviation = features["spine_line_deviation"]
    score = score_value(deviation, 15.0, 70.0, "quadratic")
    passed = deviation <= 30.0
    return {
        "step": 4, "name": "Spine Lengthened",
        "passed": passed, "score": score,
        "issue": None if passed else
                 "Spine is not elongated - reach fingertips forward and sit hips back",
        "cue": "Lengthen the spine - elongate from fingertips to hips",
        "not_visible": False,
    }


def check_forehead_down(features, visible=True):
    if not visible:
        return _not_visible(5, "Forehead Down", "head and arms",
                            "Rest your forehead on the mat, or on a block if needed")
    head_lift = features["head_lift_above_mat"]
    score = score_value(head_lift, 0.05, 0.40, "quadratic")
    passed = head_lift <= 0.12
    return {
        "step": 5, "name": "Forehead Down",
        "passed": passed, "score": score,
        "issue": None if passed else
                 "Head is lifted - rest your forehead on the mat (or a block)",
        "cue": "Relax the forehead onto the mat - use a block if needed",
        "not_visible": False,
    }


def check_shoulders_relaxed(features, visible=True):
    if not visible:
        return _not_visible(6, "Shoulders Relaxed", "shoulders and ears",
                            "Relax your shoulders away from your ears")
    drop = features["shoulder_ear_drop"]
    if drop >= 0.04:
        score = 100.0
    elif drop >= -0.04:
        score = round(60.0 + (drop + 0.04) * (40.0 / 0.08), 1)
    elif drop >= -0.15:
        score = round(max(0.0, 60.0 * (drop + 0.15) / 0.11), 1)
    else:
        score = 0.0

    passed = drop >= -0.03

    return {
        "step": 6, "name": "Shoulders Relaxed",
        "passed": passed, "score": score,
        "issue": None if passed else
                 "Shoulders are hunched up - relax them down, away from your ears",
        "cue": "Relax your shoulders away from your ears, no tension in the neck",
        "not_visible": False,
    }


STEP_WEIGHTS = {1: 0.20, 2: 0.25, 3: 0.20, 4: 0.15, 5: 0.10, 6: 0.10}


def validate_pose(features, step_visibility=None):
    if step_visibility is None:
        step_visibility = {i: True for i in range(1, 7)}

    step_results = [
        check_hips_on_heels(features, step_visibility.get(1, True)),
        check_torso_fold(features, step_visibility.get(2, True)),
        check_arms_extended(features, step_visibility.get(3, True)),
        check_spine_lengthened(features, step_visibility.get(4, True)),
        check_forehead_down(features, step_visibility.get(5, True)),
        check_shoulders_relaxed(features, step_visibility.get(6, True)),
    ]

    # NEW LOGIC: Mark zero-score steps to hide from UI, substitute 50 in formula.
    # This prevents a single "0" (whether from a hidden body part or a genuinely
    # bad rep) from cratering the final score. The UI skips these cards entirely.
    for s in step_results:
        if s["score"] == 0.0:
            s["hide_from_ui"] = True
            s["effective_score"] = 50.0
        else:
            s["hide_from_ui"] = False
            s["effective_score"] = s["score"]

    # Final-score formula uses effective_score (50 for hidden steps)
    base_score = 0.0
    for s in step_results:
        s["weight"] = STEP_WEIGHTS[s["step"]]
        base_score += s["effective_score"] * s["weight"]

    worst = min(s["effective_score"] for s in step_results)
    very_bad = sum(1 for s in step_results if s["effective_score"] < 20)
    critical = sum(1 for s in step_results if s["effective_score"] < 40)

    final_score = base_score
    if very_bad >= 2:
        final_score *= 0.65
    elif very_bad >= 1:
        final_score *= 0.90
    elif critical >= 2:
        final_score *= 0.92

    if worst < 50:
        final_score = min(final_score, 85.0)
    if worst < 30:
        final_score = min(final_score, 72.0)
    if worst < 15:
        final_score = min(final_score, 60.0)

    final_score = int(round(final_score))
    final_score = max(0, min(100, final_score))

    # Don't include hidden steps in the visible issues list
    issues = [s["issue"] for s in step_results
              if s["issue"] and not s.get("hide_from_ui")]

    return {
        "final_score": final_score,
        "steps": step_results,
        "issues": issues,
    }
