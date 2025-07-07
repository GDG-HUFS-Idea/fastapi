import json
import logging
import random
from textwrap import dedent
from pydantic import BaseModel, Field, ValidationError
from tiktoken import encoding_for_model
from typing import List, Union
from pydantic import BaseModel, Field

from app.common.utils import retry, validate_json
from app.core.cache import get_static_redis_session
from app.external.openai import OpenAIClient
from app.service.analyzer.pre_analysis_data import PreAnalysisDataServiceResponse
from app.service.cache.task_progress import TaskProgressCache
from app.common.enums import TaskStatus
from app.common.exceptions import AnalysisServiceError, JSONValidationError, ModelValidationError

logger = logging.getLogger(__name__)


class _CodeNamePair(BaseModel):
    code: str
    name: str


class _KsicHierarchy(BaseModel):
    large: _CodeNamePair
    medium: _CodeNamePair
    small: _CodeNamePair
    detail: _CodeNamePair


class _MarketAnalysis(BaseModel):
    domestic: str
    global_: str = Field(alias="global")


class _GrowthRates(BaseModel):
    five_year_korea: str = Field(alias="5YearKorea")
    five_year_global: str = Field(alias="5YearGlobal")
    source: str


class _MarketSizeData(BaseModel):
    year: int
    size: str
    growth_rate: str = Field(alias="growthRate")


class _MarketSizeSource(BaseModel):
    source: str


class _MarketSizeByYear(BaseModel):
    domestic: List[Union[_MarketSizeData, _MarketSizeSource]]
    global_: List[Union[_MarketSizeData, _MarketSizeSource]] = Field(alias="global")


class _AverageRevenue(BaseModel):
    domestic: str
    global_: str = Field(alias="global")
    source: str


class _SimilarService(BaseModel):
    tags: List[str]
    name: str
    url: str
    description: str
    target_audience: str = Field(alias="targetAudience")
    summary: str
    similarity: int


class _TargetAudience(BaseModel):
    segment: str
    reasons: str
    interest_factors: str = Field(alias="interestFactors")
    online_activities: str = Field(alias="onlineActivities")
    online_touchpoints: str = Field(alias="onlineTouchpoints")
    offline_touchpoints: str = Field(alias="offlineTouchpoints")


class _InvestmentPriority(BaseModel):
    name: str
    description: str


class _BusinessModel(BaseModel):
    tagline: str
    value: str
    value_details: str = Field(alias="valueDetails")
    revenue_structure: str = Field(alias="revenueStructure")
    investment_priorities: List[_InvestmentPriority] = Field(alias="investmentPriorities")
    break_even_point: str = Field(alias="breakEvenPoint")


class _PhasedStrategy(BaseModel):
    pre_launch: str = Field(alias="preLaunch")
    launch: str
    growth: str


class _MarketingStrategy(BaseModel):
    approach: str
    channels: List[str]
    messages: List[str]
    budget_allocation: str = Field(alias="budgetAllocation")
    kpis: List[str]
    phased_strategy: _PhasedStrategy = Field(alias="phasedStrategy")


class _SupportProgram(BaseModel):
    name: str
    organization: str
    amount: str
    period: str
    details: str


class _Limitation(BaseModel):
    category: str
    details: str
    impact: str
    solution: str


class _TeamRole(BaseModel):
    title: str
    skills: str
    responsibilities: str
    priority: Union[str, int]


class _RequiredTeam(BaseModel):
    roles: List[_TeamRole]


class _Scores(BaseModel):
    market: int
    opportunity: int
    similar_service: int = Field(alias="similarService")
    risk: int
    total: float


class OverviewAnalysisServiceResponse(BaseModel):
    ksic_code: str = Field(alias="ksicCode")
    ksic_category: str = Field(alias="ksicCategory")
    ksic_hierarchy: _KsicHierarchy = Field(alias="ksicHierarchy")
    market_analysis: _MarketAnalysis = Field(alias="marketAnalysis")
    growth_rates: _GrowthRates = Field(alias="growthRates")
    market_size_by_year: _MarketSizeByYear = Field(alias="marketSizeByYear")
    average_revenue: _AverageRevenue = Field(alias="averageRevenue")
    similar_services: List[_SimilarService] = Field(alias="similarServices")
    target_audience: List[_TargetAudience] = Field(alias="targetAudience")
    business_model: _BusinessModel = Field(alias="businessModel")
    marketing_strategy: _MarketingStrategy = Field(alias="marketingStrategy")
    opportunities: List[str]
    support_programs: List[_SupportProgram] = Field(alias="supportPrograms")
    limitations: List[_Limitation]
    required_team: _RequiredTeam = Field(alias="requiredTeam")
    scores: _Scores
    one_line_review: str = Field(alias="oneLineReview")


class OverviewAnalysisService:
    _OPENAI_MODEL = "gpt-4o-mini"
    _MAX_ATTEMPTS = 3
    _TEMPERATURE = 0.2
    _MAX_TOKENS = 5000
    _TIMEOUT_SECONDS = 60 * 5

    def __init__(
        self,
    ) -> None:
        self._openai_client = OpenAIClient()

    async def analyze(
        self,
        task_id: str,
        pre_analysis_data: PreAnalysisDataServiceResponse,
    ) -> OverviewAnalysisServiceResponse:
        try:
            redis = await get_static_redis_session()
            self._task_progress_cache = TaskProgressCache(session=redis)

            # 1. 본 분석 준비
            logger.info("본 분석 준비 중")
            await self._task_progress_cache.update_partial(
                key=task_id,
                progress=round(random.uniform(0.33, 0.45), 2),
                message="본 분석 준비 중입니다...",
            )

            base_progress = round(random.uniform(0.45, 0.55), 2)
            encoding = encoding_for_model(self._OPENAI_MODEL)
            estimated_output_tokens = self._MAX_TOKENS * 1.1
            user_prompt = self._generate_prompt(pre_analysis_data)
            system_prompt = dedent(
                """
                당신은 비즈니스 분석 전문가입니다.
                객관적인 데이터를 기반으로 사업 아이디어를 분석하고, 점수를 산출하세요.
                추가 설명이나 불필요한 문장은 포함하지 마세요.
                반드시 중괄호 { }로 시작하는 순수 JSON을 반환해야 합니다.
                """
            ).strip()

            # 2. 본 분석 실행
            logger.info("본 분석 실행 중")
            await self._task_progress_cache.update_partial(
                key=task_id,
                progress=base_progress,
                message="본 분석을 시작합니다. 잠시만 기다려 주세요...",
            )

            async def operation():
                total_content = ""
                last_progress = base_progress

                async for content_piece in self._openai_client.stream(
                    user_prompt,
                    system_prompt,
                    timeout_seconds=self._TIMEOUT_SECONDS,
                    temperature=self._TEMPERATURE,
                    max_tokens=self._MAX_TOKENS,
                ):
                    total_content += content_piece

                    # 예상 토큰 수에 기반한 진행률 계산
                    total_tokens = len(encoding.encode(total_content))
                    token_ratio = min(total_tokens / estimated_output_tokens, 1.0)

                    progress = round(base_progress + token_ratio * (0.95 - base_progress), 2)

                    # 진행률이 이전보다 클 때만 업데이트
                    if progress > last_progress:
                        logger.info(f"본 분석 진행 중 ({int(progress * 100)}%)")
                        await self._task_progress_cache.update_partial(
                            key=task_id,
                            progress=progress,
                            message="분석 결과를 생성하고 있습니다...",
                        )
                        last_progress = progress

                logger.info(total_content.strip())
                parsed_content = json.loads(validate_json(total_content.strip()))
                return OverviewAnalysisServiceResponse.model_validate(parsed_content)

            return await retry(
                function=operation,
                max_attempts=self._MAX_ATTEMPTS,
            )

        except JSONValidationError as exception:
            await self._task_progress_cache.update_partial(
                key=task_id,
                status=TaskStatus.FAILED,
                message="분석 결과 형식이 올바르지 않습니다.",
            )
            raise JSONValidationError(f"JSON 형식 검증 오류가 발생했습니다: {str(exception)}") from exception
        except ValidationError as exception:
            await self._task_progress_cache.update_partial(
                key=task_id,
                status=TaskStatus.FAILED,
                message="분석 결과 검증에 실패했습니다.",
            )
            raise ModelValidationError(f"모델 검증 오류가 발생했습니다: {str(exception)}") from exception
        except Exception as exception:
            await self._task_progress_cache.update_partial(
                key=task_id,
                status=TaskStatus.FAILED,
                message="본 분석 서비스에서 오류가 발생했습니다. 나중에 다시 시도해 주세요.",
            )
            logger.error(f"본 분석 서비스에서 오류가 발생했습니다: {str(exception)}")
            raise AnalysisServiceError(f"본 분석 서비스에서 오류가 발생했습니다: {str(exception)}") from exception

    def _generate_prompt(
        self,
        pre_analysis_data: PreAnalysisDataServiceResponse,
    ) -> str:
        main_analysis_prompt = dedent(
            f"""
            다음 데이터를 기반으로 상세한 사업화 분석 리포트를 JSON 형식으로 생성해주세요:
            ## 비즈니스 아이디어 정보 ##
            문제점: {', '.join(pre_analysis_data.business_case.problem.issues)}
            개발 동기: {pre_analysis_data.business_case.problem.motivation}
            핵심 요소: {', '.join(pre_analysis_data.business_case.solution.features)}
            방법론: {pre_analysis_data.business_case.solution.method}
            기대 성과: {pre_analysis_data.business_case.solution.deliverable}

            ## 산업 분류 정보 ##
            대분류: {pre_analysis_data.market.ksic_category.large.name} ({pre_analysis_data.market.ksic_category.large.code})
            중분류: {pre_analysis_data.market.ksic_category.medium.name} ({pre_analysis_data.market.ksic_category.medium.code})
            소분류: {pre_analysis_data.market.ksic_category.small.name} ({pre_analysis_data.market.ksic_category.small.code})
            세분류: {pre_analysis_data.market.ksic_category.detail.name} ({pre_analysis_data.market.ksic_category.detail.code})

            ## 시장 분석 정보 ##
            ### 국내 시장 ###
            {pre_analysis_data.market.domestic_market_research.model_dump_json(indent=2)}

            ### 글로벌 시장 ###
            {pre_analysis_data.market.global_market_research.model_dump_json(indent=2)}

            ## 유사 서비스 정보 ##
            {pre_analysis_data.similar_service.model_dump_json(indent=2)}

            ## 기회 요인 ##
            {pre_analysis_data.opportunity}

            ## 한계점 ##
            {pre_analysis_data.limitation}

            ## 팀 구성 정보 ##
            {pre_analysis_data.team_requirement}

            반드시 'ksicCode', 'ksicCategory', 'ksicHierarchy' 필드를 포함하여 KSIC 분류 정보를 완벽하게 표시해주세요.
            KSIC 계층 구조는 대분류, 중분류, 소분류, 세분류 정보를 모두 포함해야 합니다.

            위의 데이터를 종합적으로 분석하여 다음 항목을 포함한 리포트를 작성해주세요:
            1. 시장 분석:
                - 국내 시장: 최근 5년간(2020-2025) 시장규모와 성장률(정확한 소수점 표기)
                - 글로벌 시장: 최근 5년간(2020-2025) 시장규모와 성장률(정확한 소수점 표기)
                - 국내 업계 평균 매출 수준(달러 기준, 구체적 수치)
                - 글로벌 업계 평균 매출 수준(달러 기준, 구체적 수치)

            2. 유사 서비스 분석:
                - 유사도 점수가 높은 상위 5개 서비스를 반드시 구체적인 이름과 함께 제공
                - 각 서비스마다 다음 정보를 명확하게 포함:
                    * 서비스 이름 (실제 서비스명 필수 포함)
                    * 서비스 URL (실제 존재하는 웹사이트 주소)
                    * 태그(50자 이내 5개 키워드)
                    * 서비스 설명 (300자 이상의 구체적이고 상세한 설명)
                    * 주요 타겟층 (구체적인 인구통계학적 특성 포함)
                    * 한 줄 요약 (서비스의 핵심 가치 제안)
                    * 유사도 점수 (1-100점 사이의 구체적인 수치)

            3. 주 타겟층(최소 3개 이상의 세그먼트 구체적 제시):
                - 각 세그먼트별 인구통계학적 특성을 상세히 기술
                - 연령대, 성별, 직업, 소득수준, 관심사 등 구체적 정보 포함
                - 각 타겟층별 선정 이유와 근거 제시
                - 각 타겟층의 구체적인 니즈와 페인포인트 설명
                - 온라인 활동 패턴 (사용 플랫폼, 사용 시간대, 소비 콘텐츠)
                - 주요 온라인 접점 (구체적인 플랫폼, 서비스명, 이용 형태)
                - 주요 오프라인 접점 (구체적인 장소, 이용 서비스, 활동 형태)

            4. 예상 비즈니스 모델(구체적 수익 창출 방안):
                - 한 줄 카피(tagline): 실제 광고에 사용할 수 있는 핵심 가치 제안 문구 (예: '당신의 아이디어, 데이터로 검증하다', '무릎에서 시작해 시장을 움직이는 혁신')
                - 제품이 전달하는 핵심 가치: 고객 문제 해결 방식과 차별화 요소
                - 가치 전달 메커니즘: 가치 전달 과정과 고객 경험 시나리오
                - 수익 구조 분석: 주 수익원, 가격 책정 전략, 수익 창출 모델 (구독형, 광고형, 프리미엄형, 거래 수수료 등 구체적 모델 제시)
                - 투자 비용 우선순위: 최소 5가지 이상의 투자 영역과 예상 비용 비율 및 각 항목별 100자 내외의 세부 설명
                - 손익분기점 예상: 초기 투자 규모와 회수 기간 예측

            5. 마케팅 전략(구체적인 실행 계획):
                - 각 타겟 고객층별 차별화된 접근 전략과 메시지
                - 채널별 마케팅 전략 (온라인/오프라인 채널 구분하여 최소 3개 이상)
                - 주요 마케팅 메시지와 UVP(Unique Value Proposition)
                - 마케팅 예산 배분 (채널별 구체적 비율과 예산 범위)
                - 마케팅 성과 측정 KPI와 기대 성과
                - 단계별 마케팅 전략 (런칭 전, 런칭 시점, 성장기 구분)

            6. 기회 요인 및 관련 지원 사업:
                - 시장 기회 요인 (최소 5가지, 구체적인 근거와 함께)
                - 활용 가능한 지원 사업/공모전 (실제 존재하는 프로그램, 신청 시기 포함)
                - 지원 내용과 금액 (구체적인 지원 범위와 금액 명시)

            7. 한계점:
                - 법률적 규제 (구체적인 법률명과 조항 포함)
                - 특허 관련 이슈 (유사 특허 존재 여부, 회피 전략)
                - 시장 진입 장벽 (기존 업체, 초기 투자 요구 등 구체적 설명)
                - 기술적 제약 (구현 난이도, 필요 기술, 개발 기간 등)

            8. 예상 필요 팀원(구체적 역할과 인원수):
                - 핵심 역할 및 직책 (최소 5개 이상의 구체적 직무)
                - 각 역할별 필요 역량과 경력 수준 상세 기술
                - 담당 업무 범위와 책임 영역 명확히 정의
                - 팀 구성 우선순위와 채용 순서 제안
                - 각 역할별 예상 연봉 범위 (시장 기준)
                - 조직 구조와 보고 체계 제안

            9. 분야별 점수(100점 만점):
                - 시장성 (시장 규모, 성장률, 진입 가능성 등 고려)
                - 실현 가능성 (기술적, 운영적 관점에서 평가)
                - 수익성 (예상 수익 모델의 지속가능성 평가)
                - 지속 가능성 (장기적 성장 가능성 평가)
                - 총점 (평균값, 소수점 첫째 자리까지 표기)

            10. 종합 평가:
                - 아이디어 강점 요약 (3-5가지 핵심 강점)
                - 위험 요소 요약 (3-5가지 주요 위험)
                - 시장 진출 타이밍 제안 (현재/6개월 내/1년 내/2년 내 등 구체적 시점)
                - 최종 한 줄 평가 (100-150자 이내로 종합적 평가 포함)
                - 형식: '제안하신 아이디어는 [강점 요소]가 강점이 될 수 있고, [위험 요소] 부분에 위험성을 가지고 있습니다. 시장 진출 타이밍은 [구체적 시점]이 적절해 보입니다.'
            모든 데이터를 활용하여 사업 아이디어의 가능성을 객관적으로 평가해주세요.
            """
        ).strip()

        scoring_criteria_prompt = dedent(
            """
            ## 점수 산출 기준 (매우 중요) ##
            아래 기준에 따라 주어진 데이터를 분석하여 객관적으로 점수를 산출해야 합니다:

            1. 시장성 점수(0-100):
               - 시장 규모(40%): 시장 규모가 클수록 높은 점수
               - 성장률(30%): 연평균 성장률이 높을수록 높은 점수
               - 진입 가능성(30%): 진입장벽이 낮을수록 높은 점수

            2. 기회 점수(0-100):
               - 트렌드 부합성(25%): 현재 시장 트렌드와 일치할수록 높은 점수
               - 차별화 가능성(25%): 기존 서비스와 차별화 정도에 따라 점수 부여
               - 성장 잠재력(25%): 향후 성장 가능성에 따라 점수 부여
               - 확장성(25%): 다양한 영역으로 확장 가능성에 따라 점수 부여

            3. 유사서비스 점수(0-100):
               - 경쟁 상황(40%): 경쟁이 적을수록 높은 점수
               - 차별화 요소(40%): 경쟁사 대비 차별화 정도에 따라 점수 부여
               - 시장 포지셔닝(20%): 명확한 포지셔닝 가능성에 따라 점수 부여

            4. 위험성 점수(0-100):
               - 법률/규제(25%): 규제가 적을수록 높은 점수
               - 특허/IP 이슈(25%): IP 문제가 적을수록 높은 점수
               - 진입장벽(25%): 초기 투자 요구가 적을수록 높은 점수
               - 기술 구현 난이도(25%): 구현이 쉬울수록 높은 점수

            5. 총점 계산:
               - 위 네 가지 점수의 단순 평균값(소수점 첫째 자리까지 표기)
               - 예시: (시장성 80 + 기회 70 + 유사서비스 75 + 위험성 65) / 4 = 72.5점

            주의: 하드코딩된 점수를 사용하지 말고, 반드시 위 기준에 따라 객관적으로 점수를 산출하세요.
            """
        ).strip()

        json_schema_template = dedent(
            """
            {
                "ksicCode": "세분류 코드(예: J6211)",
                "ksicCategory": "세분류명(예: 시스템 소프트웨어 개발 및 기타 소프트웨어 개발)",
                "ksicHierarchy": {
                    "large": {"code": "대분류 코드", "name": "대분류명"},
                    "medium": {"code": "중분류 코드", "name": "중분류명"},
                    "small": {"code": "소분류 코드", "name": "소분류명"},
                    "detail": {"code": "세분류 코드", "name": "세분류명"}
                },
                "marketAnalysis": {
                "domestic": "국내 시장 분석 내용(출처 포함, 구체적 수치 데이터 포함)",
                "global": "글로벌 시장 분석 내용(출처 포함, 한국어로 작성, 구체적 수치 데이터 포함)"
            },
            "growthRates": {
                "5YearKorea": "최근 5년간 국내 연평균 성장률(정확한 소수점 표기, 예: 5.75%)",
                "5YearGlobal": "최근 5년간 글로벌 연평균 성장률(정확한 소수점 표기, 예: 7.2%)"
                "source": "성장률 데이터 출처(구체적 기관명 또는 보고서명 필수 포함)"
            },
             "marketSizeByYear": {
                "domestic": [
                    {"year": 2020, "size": "$ 금액", "growthRate": "성장률(%)"},
                    {"year": 2021, "size": "$ 금액", "growthRate": "성장률(%)"},
                    {"year": 2022, "size": "$ 금액", "growthRate": "성장률(%)"},
                    {"year": 2023, "size": "$ 금액", "growthRate": "성장률(%)"},
                    {"year": 2024, "size": "$ 금액", "growthRate": "성장률(%)"},
                    {"year": 2025, "size": "$ 금액(예상)", "growthRate": "성장률(%)"},
                    {"source": "종합 시장 데이터 출처(구체적 기관명 또는 보고서명 필수 포함)"}
                ],
                "global": [
                    {"year": 2020, "size": "$ 금액", "growthRate": "성장률(%)"},
                    {"year": 2021, "size": "$ 금액", "growthRate": "성장률(%)"},
                    {"year": 2022, "size": "$ 금액", "growthRate": "성장률(%)"},
                    {"year": 2023, "size": "$ 금액", "growthRate": "성장률(%)"},
                    {"year": 2024, "size": "$ 금액", "growthRate": "성장률(%)"},
                    {"year": 2025, "size": "$ 금액(예상)", "growthRate": "성장률(%)"},
                    {"source": "종합 시장 데이터 출처(구체적 기관명 또는 보고서명 필수 포함)"}
                ]
                },
                "averageRevenue": {
                "domestic": "국내 업계 평균 매출(달러 표기, 예: $500,000)",
                "global": "글로벌 업계 평균 매출(달러 표기, 예: $2,500,000)",
                "source": "평균 매출 데이터 출처(구체적 기관명 또는 보고서명 필수 포함)"
            },
            "similarServices": [
                {
                    "tags": ["태그1", "태그2", "태그3", "태그4", "태그5"],
                    "name": "구체적인 실제 서비스명(필수)",
                    "url": "실제 접속 가능한 홈페이지 URL(필수)",
                    "description": "서비스에 대한 상세 설명(500자 이상)",
                    "targetAudience": "해당 서비스의 주요 타겟층 상세 설명",
                    "summary": "서비스를 요약한 한 줄 설명(50자 내외)",
                    "similarity": 85
                }
            ],
            "targetAudience": [
                {
                    "segment": "구체적인 인구통계학적 특성을 포함한 타겟층 설명(예: 30-40대 직장인)",
                    "reasons": "이 세그먼트를 타겟으로 선정한 구체적인 이유와 근거",
                    "interestFactors": "이 세그먼트의 관심사와 흥미 요소 상세 설명",
                    "onlineActivities": "이 세그먼트의 온라인 활동 패턴과 특성",
                    "onlineTouchpoints": "이 세그먼트와 접점을 가질 수 있는 온라인 채널(구체적 명시)",
                    "offlineTouchpoints": "이 세그먼트와 접점을 가질 수 있는 오프라인 장소/활동(구체적 명시)"
                },
                {
                    "segment": "구체적인 인구통계학적 특성을 포함한 타겟층 설명(예: 20대 초중반 대학생)",
                    "reasons": "이 세그먼트를 타겟으로 선정한 구체적인 이유와 근거",
                    "interestFactors": "이 세그먼트의 관심사와 흥미 요소 상세 설명",
                    "onlineActivities": "이 세그먼트의 온라인 활동 패턴과 특성",
                    "onlineTouchpoints": "이 세그먼트와 접점을 가질 수 있는 온라인 채널(구체적 명시)",
                    "offlineTouchpoints": "이 세그먼트와 접점을 가질 수 있는 오프라인 장소/활동(구체적 명시)"
                },
                {
                    "segment": "구체적인 인구통계학적 특성을 포함한 타겟층 설명(예: 40-50대 소상공인)",
                    "reasons": "이 세그먼트를 타겟으로 선정한 구체적인 이유와 근거",
                    "interestFactors": "이 세그먼트의 관심사와 흥미 요소 상세 설명",
                    "onlineActivities": "이 세그먼트의 온라인 활동 패턴과 특성",
                    "onlineTouchpoints": "이 세그먼트와 접점을 가질 수 있는 온라인 채널(구체적 명시)",
                    "offlineTouchpoints": "이 세그먼트와 접점을 가질 수 있는 오프라인 장소/활동(구체적 명시)"
                }
            ],
            "businessModel": {
                "tagline": "홍보에 사용할 수 있는 구어체 광고 카피 문구",
                "value": "제품/서비스가 전달하는 핵심 가치 명확하게 제시",
                "valueDetails": "가치에 대한 세부 설명과 구체적인 고객 혜택",
                "revenueStructure": "주요 수익원과 수익 창출 방식에 대한 상세 설명(금액, 모델 등)",
                "investmentPriorities": [
                    {"name": "우선순위1(비중: XX%)", "description": "이 투자 항목에 대한 100자 내외의 상세 설명 - 왜 중요한지, 어떻게 활용될지, 예상 효과는 무엇인지 등 구체적으로 기술"},
                    {"name": "우선순위2(비중: XX%)", "description": "이 투자 항목에 대한 100자 내외의 상세 설명 - 왜 중요한지, 어떻게 활용될지, 예상 효과는 무엇인지 등 구체적으로 기술"},
                    {"name": "우선순위3(비중: XX%)", "description": "이 투자 항목에 대한 100자 내외의 상세 설명 - 왜 중요한지, 어떻게 활용될지, 예상 효과는 무엇인지 등 구체적으로 기술"},
                    {"name": "우선순위4(비중: XX%)", "description": "이 투자 항목에 대한 100자 내외의 상세 설명 - 왜 중요한지, 어떻게 활용될지, 예상 효과는 무엇인지 등 구체적으로 기술"},
                    {"name": "우선순위5(비중: XX%)", "description": "이 투자 항목에 대한 100자 내외의 상세 설명 - 왜 중요한지, 어떻게 활용될지, 예상 효과는 무엇인지 등 구체적으로 기술"}
                ],
                "breakEvenPoint": "손익분기점 도달 예상 시점과 필요 조건"
            },
            "marketingStrategy": {
                "approach": "전반적인 마케팅 접근 방법과 전략적 방향",
                "channels": ["채널1(활용도: XX%)", "채널2(활용도: XX%)", "채널3(활용도: XX%)"],
                "messages": ["핵심 메시지1", "핵심 메시지2", "핵심 메시지3"],
                "budgetAllocation": "채널별 예산 배분과 전체 마케팅 예산 제안",
                "kpis": ["핵심 성과 지표1", "핵심 성과 지표2", "핵심 성과 지표3"],
                "phasedStrategy": {
                    "preLaunch": "출시 전 마케팅 전략",
                    "launch": "출시 시점 마케팅 전략",
                    "growth": "성장기 마케팅 전략"
                }
            },
            "opportunities": [
                "기회요인1(근거: 구체적 시장 데이터)",
                "기회요인2(근거: 구체적 시장 데이터)",
                "기회요인3(근거: 구체적 시장 데이터)",
                "기회요인4(근거: 구체적 시장 데이터)",
                "기회요인5(근거: 구체적 시장 데이터)"
            ],
            "supportPrograms": [
                {"name": "지원 프로그램1", "organization": "주관 기관", "amount": "지원 금액", "period": "신청 기간", "details": "지원 내용 상세"},
                {"name": "지원 프로그램2", "organization": "주관 기관", "amount": "지원 금액", "period": "신청 기간", "details": "지원 내용 상세"}
            ],
            "limitations": [
                {"category": "법률/규제", "details": "구체적인 법률명과 조항", "impact": "영향", "solution": "대응 방안"},
                {"category": "특허/지적재산권", "details": "관련 특허 정보", "impact": "영향", "solution": "대응 방안"},
                {"category": "시장 진입장벽", "details": "구체적 장벽 요소", "impact": "영향", "solution": "대응 방안"},
                {"category": "기술적 제약", "details": "구현 난이도, 필요 기술", "impact": "영향", "solution": "대응 방안"}
            ],
            "requiredTeam": {
                "roles": [
                    {
                        "title": "직책명",
                        "skills": "필요 역량 및 경력 요건 상세",
                        "responsibilities": "담당 업무 범위 구체적 설명",
                        "priority": "채용 우선순위(1-5 단계)",
                    },
                    {
                        "title": "직책명",
                        "skills": "필요 역량 및 경력 요건 상세",
                        "responsibilities": "담당 업무 범위 구체적 설명",
                        "priority": "채용 우선순위(1-5 단계)",
                    },
                    {
                        "title": "직책명",
                        "skills": "필요 역량 및 경력 요건 상세",
                        "responsibilities": "담당 업무 범위 구체적 설명",
                        "priority": "채용 우선순위(1-5 단계)",
                    },
                    {
                        "title": "직책명",
                        "skills": "필요 역량 및 경력 요건 상세",
                        "responsibilities": "담당 업무 범위 구체적 설명",
                        "priority": "채용 우선순위(1-5 단계)",
                    },
                    {
                        "title": "직책명",
                        "skills": "필요 역량 및 경력 요건 상세",
                        "responsibilities": "담당 업무 범위 구체적 설명",
                        "priority": "채용 우선순위(1-5 단계)",
                    }
                ],
            },
                "scores": {
                    "market": "주어진 데이터를 기반으로 시장성 점수 산출 (0-100 사이 값)",
                    "opportunity": "주어진 데이터를 기반으로 기회 점수 산출 (0-100 사이 값)",
                    "similarService": "주어진 데이터를 기반으로 유사서비스 점수 산출 (0-100 사이 값)",
                    "risk": "주어진 데이터를 기반으로 위험성 점수 산출 (0-100 사이 값)",
                    "total": "위 네 가지 점수의 평균값 (소수점 첫째 자리까지)"
                },
                "oneLineReview": "제안하신 아이디어는 [강점 요소]가 강점이 될 수 있고, [위험 요소] 부분에 위험성을 가지고 있습니다. 실현 가능성은 [높음/중간/낮음]이며, 지속 가능성은 [높음/중간/낮음]입니다. 시장 진출 타이밍은 [구체적 시점]이 적절해 보입니다."
            }
            """
        ).strip()

        complete_analysis_prompt = dedent(
            f"""
            ## 중요: 다음 점수 산출 기준을 반드시 따라주세요 ##
            {scoring_criteria_prompt}

            {main_analysis_prompt}

            반드시 아래의 정확한 JSON 형식으로 응답해주세요:
            {json_schema_template}

            응답은 반드시 유효한 JSON 형식이어야 합니다.
            모든 분석에 출처를 반드시 포함해주세요.
            모든 텍스트는 한국어로 작성해주세요.
            주어진 데이터를 적극 활용하되, 필요한 경우 합리적인 추론으로 보완해주세요.
            특히 시장 분석, 성장률, 평균 매출 부분은 반드시 구체적인 수치로 작성해주세요.
            유사 서비스는 반드시 실제 존재하는 서비스명과 URL을 포함해주세요.
            주 타겟층은 구체적인 인구통계학적 특성을 포함하고 최소 3개 이상 제시해주세요.
            비즈니스 모델은 구체적인 수익 창출 방식과 금액 추정을 포함해주세요.
            각 투자 우선순위 항목에는 반드시 100자 내외의 세부 설명을 포함해야 합니다.
            점수는 반드시 위에 제시된 점수 산출 기준에 따라 계산하고, 하드코딩된 값을 사용하지 마세요.
            최종 한줄평은 '[강점] 요소가 강점이 될 수 있고, [위험요소] 부분에 위험성을 가지고 있습니다. 실현 가능성은 [높음/중간/낮음]이며, 지속 가능성은 [높음/중간/낮음]입니다. 시장 진출 타이밍은 [구체적 시점]이 적절해 보입니다.' 형식을 따라주세요.
            """
        ).strip()

        return complete_analysis_prompt
