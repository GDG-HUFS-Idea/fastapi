from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.domain.market_research import MarketResearch
from app.common.exceptions import MarketResearchRepositoryError


class MarketResearchRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    async def save(
        self,
        market_research: MarketResearch,
    ) -> None:
        try:
            self._session.add(market_research)
            await self._session.commit()
            await self._session.refresh(market_research)
        except SQLAlchemyError as exception:
            raise MarketResearchRepositoryError(f"시장 분석 저장 중 오류가 발생했습니다: {str(exception)}") from exception
        except Exception as exception:
            raise MarketResearchRepositoryError(f"시장 분석 저장 중 예상치 못한 오류가 발생했습니다: {str(exception)}") from exception
