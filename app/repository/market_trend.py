from typing import List, Tuple
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.common.enums import MarketScope
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

        except Exception as exception:
            raise MarketTrendRepositoryError("시장 트렌드 저장 중 오류가 발생했습니다.") from exception

    async def find_by_market_id(
        self,
        market_id: int,
    ) -> Tuple[List[MarketTrend], List[MarketTrend]] | None:
        try:
            domestic_statement = (
                select(MarketTrend)
                .where(MarketTrend.market_id == market_id, MarketTrend.scope == MarketScope.DOMESTIC)
                .order_by(MarketTrend.year.desc())  # type: ignore
                .limit(5)
            )
            domestic_result = await self._session.exec(domestic_statement)
            domestic_trends = list(domestic_result.all())

            global_statement = (
                select(MarketTrend)
                .where(MarketTrend.market_id == market_id, MarketTrend.scope == MarketScope.GLOBAL)
                .order_by(MarketTrend.year.desc())  # type: ignore
                .limit(5)
            )
            global_result = await self._session.exec(global_statement)
            global_trends = list(global_result.all())

            if domestic_trends and global_trends:
                return (domestic_trends, global_trends)
            else:
                return None

        except Exception as exception:
            raise MarketTrendRepositoryError("시장 트렌드 조회 중 오류가 발생했습니다.") from exception
