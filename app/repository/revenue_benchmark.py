from typing import List, Tuple
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.common.enums import MarketScope
from app.domain.revenue_benchmark import RevenueBenchmark
from app.common.exceptions import RevenueBenchmarkRepositoryError


class RevenueBenchmarkRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    async def save_batch(
        self,
        market_trends: List[RevenueBenchmark],
    ) -> None:
        try:
            for term in market_trends:
                self._session.add(term)

            await self._session.flush()

            for term in market_trends:
                await self._session.refresh(term)

        except Exception as exception:
            raise RevenueBenchmarkRepositoryError("수익 벤치마크 저장 중 오류가 발생했습니다.") from exception

    async def find_by_market_id(
        self,
        market_id: int,
    ) -> Tuple[RevenueBenchmark, RevenueBenchmark] | None:
        try:
            domestic_statement = (
                select(RevenueBenchmark)
                .where(RevenueBenchmark.market_id == market_id, RevenueBenchmark.scope == MarketScope.DOMESTIC)
                .limit(1)
            )
            domestic_result = await self._session.exec(domestic_statement)
            domestic_benchmark = domestic_result.first()

            global_statement = (
                select(RevenueBenchmark)
                .where(RevenueBenchmark.market_id == market_id, RevenueBenchmark.scope == MarketScope.GLOBAL)
                .limit(1)
            )
            global_result = await self._session.exec(global_statement)
            global_benchmark = global_result.first()

            if domestic_benchmark and global_benchmark:
                return (domestic_benchmark, global_benchmark)
            else:
                return None

        except Exception as exception:
            raise RevenueBenchmarkRepositoryError("수익 벤치마크 조회 중 오류가 발생했습니다.") from exception
