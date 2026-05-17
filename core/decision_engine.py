import random
import logging
from core.prompt_library import DESIGN_WEIGHTS, DESIGN_TYPES

logger = logging.getLogger(__name__)

class DecisionEngine:
    @staticmethod
    def select_category() -> tuple[str, str]:
        """Returns (design_type, design_description) based on defined weights. Kept method name for compatibility."""
        keys = list(DESIGN_WEIGHTS.keys())
        weights = [DESIGN_WEIGHTS[k] for k in keys]
        
        selected_key = random.choices(keys, weights=weights, k=1)[0]
        logger.info(f"Decision Engine selected design type: {selected_key}")
        return selected_key, DESIGN_TYPES[selected_key]
