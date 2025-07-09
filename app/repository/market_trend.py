from typing import List
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.domain.market_trend import MarketTrend
from app.common.exceptions import MarketTrendRepositoryError


class MarketTrendRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    async def save_batch(
        self,
        market_trends: List[MarketTrend],
    ) -> None:
        try:
            for term in market_trends:
                self._session.add(term)

            await self._session.flush()

            for term in market_trends:
                await self._session.refresh(term)

        except SQLAlchemyError as exception:
            raise MarketTrendRepositoryError(f"MarketTrend 배치 저장 중 오류가 발생했습니다: {str(exception)}") from exception
        except Exception as exception:
            raise MarketTrendRepositoryError(f"MarketTrend 배치 저장 중 예상치 못한 오류가 발생했습니다: {str(exception)}") from exception
