from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis, from_url
from typing import AsyncGenerator
from sqlmodel.ext.asyncio.session import AsyncSession

from app.common.exceptions import InternalServerException, JWTDecodeError, JWTExpiredError, JWTInvalidError, UnauthorizedException
from app.core.config import setting
from app.core.database import get_sessionmaker
from app.repository.market_research import MarketResearchRepository
from app.repository.market_trend import MarketTrendRepository
from app.repository.overview_analysis import OverviewAnalysisRepository
from app.repository.project import ProjectRepository
from app.repository.project_idea import ProjectIdeaRepository
from app.repository.revenue_benchmark import RevenueBenchmarkRepository
from app.repository.term import TermRepository
from app.repository.user_agreement import UserAgreementRepository
from app.repository.user import UserRepository
from app.service.analyzer.overview_analysis import OverviewAnalysisService
from app.service.analyzer.pre_analysis_data import PreAnalysisDataService
from app.service.auth.jwt import JWTService, Payload
from app.service.auth.oauth import OAuthService
from app.service.cache.oauth_profile import OAuthProfileCache
from app.service.cache.task_progress import TaskProgressCache
from app.usecase.analysis.retrieve_overview_analysis import RetrieveOverviewAnalysisUsecase
from app.usecase.analysis.start_overview_analysis_task import StartOverviewAnalysisTaskUsecase
from app.usecase.analysis.watch_overview_analysis_task_progress import WatchOverviewAnalysisTaskProgressUsecase
from app.usecase.auth.handle_oauth_callback import HandleOAuthCallbackUsecase
from app.usecase.auth.oauth_sign_up import OAuthSignUpUsecase
from app.usecase.auth.redirect_oauth import RedirectOAuthUsecase
from app.usecase.auth.retrieve_oauth_result import RetrieveOAuthResultUsecase
from app.usecase.term.retrieve_terms import RetrieveTermsUsecase


async def get_redis_session() -> AsyncGenerator[Redis, None]:
    client = await from_url(
        f"redis://{setting.REDIS_HOST}:{setting.REDIS_PORT}",
        db=0,
        decode_responses=True,
        socket_keepalive=True,
    )

    try:
        yield client
    finally:
        await client.aclose()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    sessionmaker = get_sessionmaker()

    async with sessionmaker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> Payload:
    try:
        if not credentials or not credentials.credentials:
            raise UnauthorizedException("Authorization header가 없습니다")

        payload = JWTService.decode(credentials.credentials)
        return payload

    except JWTExpiredError as exception:
        raise UnauthorizedException("토큰이 만료되었습니다") from exception
    except JWTInvalidError as exception:
        raise UnauthorizedException("유효하지 않은 토큰입니다") from exception
    except JWTDecodeError as exception:
        raise UnauthorizedException("토큰 디코딩 중 오류가 발생했습니다") from exception
    except UnauthorizedException:
        raise  # UnauthorizedException은 그대로 전파
    except Exception as exception:
        raise InternalServerException(f"JWT 인증 처리 중 예상치 못한 오류가 발생했습니다: {str(exception)}") from exception


# Caches
def get_task_progress_cache(session: Redis = Depends(get_redis_session)):
    return TaskProgressCache(session)


def get_oauth_profile_cache(session: Redis = Depends(get_redis_session)):
    return OAuthProfileCache(session)


# Repositories
def get_user_repository(session: AsyncSession = Depends(get_db_session)):
    return UserRepository(session)


def get_term_repository(session: AsyncSession = Depends(get_db_session)):
    return TermRepository(session)


def get_user_agreement_repository(session: AsyncSession = Depends(get_db_session)):
    return UserAgreementRepository(session)


def get_project_repository(session: AsyncSession = Depends(get_db_session)):
    return ProjectRepository(session)


def get_project_idea_repository(session: AsyncSession = Depends(get_db_session)):
    return ProjectIdeaRepository(session)


def get_overview_analysis_repository(session: AsyncSession = Depends(get_db_session)):
    return OverviewAnalysisRepository(session)


def get_market_research_repository(session: AsyncSession = Depends(get_db_session)):
    return MarketResearchRepository(session)


# Services
def get_oauth_service():
    return OAuthService()


def get_pre_analysis_data_service():
    return PreAnalysisDataService()


def get_overview_analysis_service():
    return OverviewAnalysisService()


# Usecases
def get_handle_oauth_callback_usecase(
    oauth_service: OAuthService = Depends(get_oauth_service),
    oauth_profile_cache: OAuthProfileCache = Depends(get_oauth_profile_cache),
):
    return HandleOAuthCallbackUsecase(oauth_service, oauth_profile_cache)


def get_redirect_oauth_usecase(oauth_service: OAuthService = Depends(get_oauth_service)):
    return RedirectOAuthUsecase(oauth_service)


def get_retrieve_oauth_result_usecase(
    user_repository: UserRepository = Depends(get_user_repository),
    term_repository: TermRepository = Depends(get_term_repository),
    oauth_profile_cache: OAuthProfileCache = Depends(get_oauth_profile_cache),
):
    return RetrieveOAuthResultUsecase(user_repository, term_repository, oauth_profile_cache)


def get_oauth_sign_up_usecase(
    user_repository: UserRepository = Depends(get_user_repository),
    term_repository: TermRepository = Depends(get_term_repository),
    user_agreement_repository: UserAgreementRepository = Depends(get_user_agreement_repository),
    oauth_profile_cache: OAuthProfileCache = Depends(get_oauth_profile_cache),
):
    return OAuthSignUpUsecase(user_repository, term_repository, user_agreement_repository, oauth_profile_cache)


def get_retrieve_terms_usecase(term_repository: TermRepository = Depends(get_term_repository)):
    return RetrieveTermsUsecase(term_repository)


def get_start_overview_analysis_task_usecase(
    pre_analysis_data_service: PreAnalysisDataService = Depends(get_pre_analysis_data_service),
    overview_analysis_service: OverviewAnalysisService = Depends(get_overview_analysis_service),
    task_progress_cache: TaskProgressCache = Depends(get_task_progress_cache),
):
    return StartOverviewAnalysisTaskUsecase(
        pre_analysis_data_service,
        overview_analysis_service,
        task_progress_cache,
    )


def get_watch_overview_analysis_task_progress_usecase(task_progress_cache: TaskProgressCache = Depends(get_task_progress_cache)):
    return WatchOverviewAnalysisTaskProgressUsecase(task_progress_cache)


def get_retrieve_overview_analysis_usecase(
    project_repository: ProjectRepository = Depends(get_project_repository),
    overview_analysis_repository: OverviewAnalysisRepository = Depends(get_overview_analysis_repository),
    market_research_repository: MarketResearchRepository = Depends(get_market_research_repository),
    market_trend_repository: MarketTrendRepository = Depends(get_market_research_repository),
    revenue_benchmark_repository: RevenueBenchmarkRepository = Depends(get_market_research_repository),
):
    return RetrieveOverviewAnalysisUsecase(
        project_repository,
        overview_analysis_repository,
        market_research_repository,
        market_trend_repository,
        revenue_benchmark_repository,
    )
