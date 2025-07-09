from typing import Dict, Any

from app.core.module.ksicclassifier import KSICClassifier
from app.core.module.market_analyzer import MarketAnalyzer
from app.core.module.similar_service_finder import SimilarServiceFinder
from app.core.module.opportunity_analyzer import OpportunityAnalyzer
from app.core.module.limitation_analyzer import LimitationAnalyzer
from app.core.module.team_analyzer import TeamAnalyzer

def reinitialize_modules() -> Dict[str, Any]:
    """분석 모듈을 초기화하고 반환합니다."""
    return {
        'classifier': KSICClassifier(),        # Perplexity
        'market': MarketAnalyzer(),            # Perplexity
        'similar': SimilarServiceFinder(),     # Perplexity
        'opportunity': OpportunityAnalyzer(),  # Perplexity
        'limitation': LimitationAnalyzer(),    # Perplexity
        'team': TeamAnalyzer()                 # Perplexity
    } 