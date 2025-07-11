from typing import Optional
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.common import schemas
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

        except Exception as exception:
            raise MarketResearchRepositoryError("시장 분석 저장 중 오류가 발생했습니다.") from exception

    async def find_by_ksic_hierarchy(
        self,
        ksic_hierarchy: schemas.KSICHierarchy,
    ) -> Optional[MarketResearch]:
        try:
            stmt = select(MarketResearch).where(MarketResearch.ksic_hierarchy == ksic_hierarchy)
            result = await self._session.exec(stmt)
            return result.one_or_none()

        except Exception as exception:
            raise MarketResearchRepositoryError("시장 분석 조회 중 오류가 발생했습니다.") from exception
