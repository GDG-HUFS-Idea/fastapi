from typing import Dict, Any

from app.core.modules.ksicclassifier import KSICClassifier
from app.core.modules.market_analyzer import MarketAnalyzer
from app.core.modules.similar_service_finder import SimilarServiceFinder
from app.core.modules.opportunity_analyzer import OpportunityAnalyzer
from app.core.modules.limitation_analyzer import LimitationAnalyzer
from app.core.modules.team_analyzer import TeamAnalyzer

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