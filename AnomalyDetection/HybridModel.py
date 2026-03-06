import numpy as np

def compute_hybrid_score(
        market_score,
        beneish_score,
        text_score,
        realtime_score=None
    ):

    # Normalize components
    components = [
        market_score,
        beneish_score,
        text_score
    ]

    if realtime_score is not None:
        components.append(realtime_score)

    components = np.array(components, dtype=float)

    return np.mean(components)