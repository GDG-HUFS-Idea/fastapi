from typing import List, Tuple
from sqlmodel import and_, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.common.enums import MarketScope
from app.domain.market_research import MarketResearch
from app.common.exceptions import MarketResearchRepositoryError
from app.domain.market_trend import MarketTrend
from app.domain.revenue_benchmark import RevenueBenchmark


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

    async def find_joined_by_ksic_hierarchy(
        self,
        ksic_hierarchy: str,
    ) -> (
        Tuple[
            MarketResearch,
            List[MarketTrend],
            List[MarketTrend],
            RevenueBenchmark,
            RevenueBenchmark,
        ]
        | None
    ):
        try:
            # ksic_hierarchy 문자열을 파싱 ("large>medium>small>detail")
            hierarchy_parts = ksic_hierarchy.split('>')
            if len(hierarchy_parts) != 4:
                return None

            large_name, medium_name, small_name, detail_name = hierarchy_parts

            # JSONB 쿼리를 위한 조건 구성 (올바른 문법 사용)
            jsonb_condition = and_(
                MarketResearch.ksic_hierarchy['large']['name'].astext == large_name,  # type: ignore
                MarketResearch.ksic_hierarchy['medium']['name'].astext == medium_name,  # type: ignore
                MarketResearch.ksic_hierarchy['small']['name'].astext == small_name,  # type: ignore
                MarketResearch.ksic_hierarchy['detail']['name'].astext == detail_name,  # type: ignore
            )

            # MarketResearch 조회
            market_query = select(MarketResearch).where(jsonb_condition)
            market_result = await self._session.exec(market_query)
            market_research = market_result.one_or_none()

            if market_research is None:
                return None

            # MarketTrend 조회 (domestic 5개)
            domestic_trends_query = (
                select(MarketTrend)
                .where(and_(MarketTrend.market_id == market_research.id, MarketTrend.scope == MarketScope.DOMESTIC))
                .order_by(MarketTrend.year.desc())  # type: ignore
                .limit(5)
            )
            domestic_trends_result = await self._session.exec(domestic_trends_query)
            domestic_trends = list(domestic_trends_result.all())

            # MarketTrend 조회 (global 5개)
            global_trends_query = (
                select(MarketTrend)
                .where(and_(MarketTrend.market_id == market_research.id, MarketTrend.scope == MarketScope.GLOBAL))
                .order_by(MarketTrend.year.desc())  # type: ignore
                .limit(5)
            )
            global_trends_result = await self._session.exec(global_trends_query)
            global_trends = list(global_trends_result.all())

            # RevenueBenchmark 조회 (domestic 1개, 최신 연도)
            domestic_revenue_query = (
                select(RevenueBenchmark)
                .where(and_(RevenueBenchmark.market_id == market_research.id, RevenueBenchmark.scope == MarketScope.DOMESTIC))
                .order_by(RevenueBenchmark.year.desc())  # type: ignore
                .limit(1)
            )
            domestic_revenue_result = await self._session.exec(domestic_revenue_query)
            domestic_revenue = domestic_revenue_result.one_or_none()

            # RevenueBenchmark 조회 (global 1개, 최신 연도)
            global_revenue_query = (
                select(RevenueBenchmark)
                .where(and_(RevenueBenchmark.market_id == market_research.id, RevenueBenchmark.scope == MarketScope.GLOBAL))
                .order_by(RevenueBenchmark.year.desc())  # type: ignore
                .limit(1)
            )
            global_revenue_result = await self._session.exec(global_revenue_query)
            global_revenue = global_revenue_result.one_or_none()

            return (
                market_research,
                domestic_trends,
                global_trends,
                domestic_revenue,
                global_revenue,
            )  # type: ignore

        except SQLAlchemyError as exception:
            raise MarketResearchRepositoryError(f"시장 분석 조회 중 오류가 발생했습니다: {str(exception)}") from exception
        except Exception as exception:
            raise MarketResearchRepositoryError(f"시장 분석 조회 중 예상치 못한 오류가 발생했습니다: {str(exception)}") from exception
