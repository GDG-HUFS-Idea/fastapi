from typing import Optional
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.domain.overview_analysis import OverviewAnalysis
from app.common.exceptions import OverviewAnalysisRepositoryError
from app.domain.project_idea import ProjectIdea


class OverviewAnalysisRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    async def save(
        self,
        analysis: OverviewAnalysis,
    ) -> None:
        try:
            self._session.add(analysis)
            await self._session.flush()
            await self._session.refresh(analysis)

        except SQLAlchemyError as exception:
            raise OverviewAnalysisRepositoryError(f"분석 저장 중 오류가 발생했습니다: {str(exception)}") from exception
        except Exception as exception:
            raise OverviewAnalysisRepositoryError(f"분석 저장 중 예상치 못한 오류가 발생했습니다: {str(exception)}") from exception

    async def find_by_project_id(
        self,
        project_id: int,
    ) -> Optional[OverviewAnalysis]:
        try:
            query = select(OverviewAnalysis).join(ProjectIdea).where(ProjectIdea.project_id == project_id)
            result = await self._session.exec(query)
            return result.one_or_none()

        except SQLAlchemyError as exception:
            raise OverviewAnalysisRepositoryError(
                f"프로젝트({project_id}) 분석 조회 중 오류가 발생했습니다: {str(exception)}"
            ) from exception
        except Exception as exception:
            raise OverviewAnalysisRepositoryError(f"프로젝트 분석 조회 중 예상치 못한 오류가 발생했습니다: {str(exception)}") from exception
