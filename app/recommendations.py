def analyze_zone(zone, rainfall_probability):
    moisture = zone["moisture"]
    health = zone["health"]

    # Very dry soil and little chance of rain
    if moisture < 30 and rainfall_probability < 50:
        return {
            "level": "critical",
            "message": (
                f'{zone["name"]} is severely dry. '
                "Immediate irrigation recommended."
            ),
            "action": "irrigate"
        }

    # Dry soil but significant chance of rain
    if moisture < 30 and rainfall_probability >= 50:
        return {
            "level": "warning",
            "message": (
                f'{zone["name"]} is dry, but rainfall probability '
                "is high. Consider waiting for rain."
            ),
            "action": "wait"
        }

    # Moderately dry soil
    if moisture < 45 and rainfall_probability < 50:
        return {
            "level": "warning",
            "message": (
                f'{zone["name"]} has low soil moisture. '
                "Irrigation recommended."
            ),
            "action": "irrigate"
        }

    # Moderately dry + likely rain
    if moisture < 45 and rainfall_probability >= 50:
        return {
            "level": "warning",
            "message": (
                f'{zone["name"]} has low moisture, but rain may be '
                "expected. Monitor before irrigating."
            ),
            "action": "monitor"
        }

    # Excessive moisture
    if moisture > 85:
        return {
            "level": "warning",
            "message": (
                f'{zone["name"]} has excessive soil moisture. '
                "Avoid irrigation."
            ),
            "action": "avoid_irrigation"
        }

    # Poor crop health
    if health < 50:
        return {
            "level": "warning",
            "message": (
                f'{zone["name"]} has declining crop health. '
                "Monitor the zone closely."
            ),
            "action": "monitor"
        }

    return {
        "level": "healthy",
        "message": (
            f'{zone["name"]} is operating within healthy conditions.'
        ),
        "action": "none"
    }


def generate_recommendations(zones, rainfall_probability):
    recommendations = []

    for zone in zones:
        analysis = analyze_zone(
            zone,
            rainfall_probability
        )

        if analysis["level"] != "healthy":
            recommendations.append({
                "zone": zone["name"],
                **analysis
            })

    return recommendations
