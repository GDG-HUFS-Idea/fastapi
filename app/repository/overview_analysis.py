from typing import Optional, Tuple
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.domain.overview_analysis import OverviewAnalysis
from app.common.exceptions import OverviewAnalysisRepositoryError
from app.domain.project import Project
from app.repository.project_idea import ProjectIdea


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

        except Exception as exception:
            raise OverviewAnalysisRepositoryError("개요 분석 저장 중 오류가 발생했습니다.") from exception

    async def find_by_project_id(
        self,
        project_id: int,
    ) -> Optional[Tuple[Project, ProjectIdea, OverviewAnalysis]]:
        try:
            query = (
                select(Project, ProjectIdea, OverviewAnalysis)
                .join(ProjectIdea, onclause=(Project.id == ProjectIdea.project_id))  # type: ignore
                .join(OverviewAnalysis, onclause=(ProjectIdea.id == OverviewAnalysis.idea_id))  # type: ignore
                .where(Project.id == project_id)
            )
            result = await self._session.exec(query)
            return result.one_or_none()

        except Exception as exception:
            raise OverviewAnalysisRepositoryError("개요 분석 데이터를 찾는 중 오류가 발생했습니다.") from exception
