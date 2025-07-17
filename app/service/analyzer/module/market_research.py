import asyncio
import json
import logging
from textwrap import dedent
from pydantic import BaseModel, Field, ConfigDict, ValidationError
from typing import List

from app.common.utils import retry, validate_json
from app.external.openai_search import OpenAISearchClient
from app.common.exceptions import AnalysisServiceError, ExternalAPIError, JSONValidationError, ModelValidationError

logger = logging.getLogger(__name__)


class _CodeNamePair(BaseModel):
    code: str
    name: str


class _KsicCategory(BaseModel):
    large: _CodeNamePair
    medium: _CodeNamePair
    small: _CodeNamePair
    detail: _CodeNamePair


class _MarketSizeData(BaseModel):
    year: int
    size: int
    growth_rate: float = Field(alias="growthRate")


class _DomesticMarketData(BaseModel):
    ksic_code: str = Field(alias="ksicCode")
    ksic_category: str = Field(alias="ksicCategory")
    market_size_by_year: List[_MarketSizeData] = Field(alias="marketSizeByYear")
    average_revenue: int = Field(alias="averageRevenue")
    average_revenue_source: str = Field(alias="averageRevenueSource")
    competition_level: str = Field(alias="competitionLevel")
    key_competitors: List[str] = Field(alias="keyCompetitors")
    market_trends: List[str] = Field(alias="marketTrends")
    sources: List[str]


class _GlobalMarketData(BaseModel):
    market_size_by_year: List[_MarketSizeData] = Field(alias="marketSizeByYear")
    average_revenue: int = Field(alias="averageRevenue")
    average_revenue_source: str = Field(alias="averageRevenueSource")
    competition_level: str = Field(alias="competitionLevel")
    key_competitors: List[str] = Field(alias="keyCompetitors")
    market_trends: List[str] = Field(alias="marketTrends")
    sources: List[str]


class MarketResearchServiceResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    domestic_market_research: _DomesticMarketData
    global_market_research: _GlobalMarketData
    ksic_category: _KsicCategory


class MarketResearchService:
    _TIMEOUT_SECONDS = 60 * 5
    _TEMPERATURE = 0.7
    _MAX_TOKENS = 1000
    _MAX_ATTEMPTS = 3

    def __init__(
        self,
    ) -> None:
        self._openAI_search_client = OpenAISearchClient()

    async def execute(
        self,
        idea: str,
        issues: List[str],
        features: List[str],
        method: str,
    ) -> MarketResearchServiceResponse:
        try:

            async def operation():
                # KSIC 분류 조회
                ksic_content = await self._openAI_search_client.fetch(
                    user_prompt=self._generate_ksic_classification_prompt(idea),
                    system_prompt="You are a helpful assistant that provides accurate and detailed information.",
                    timeout_seconds=self._TIMEOUT_SECONDS,
                    temperature=self._TEMPERATURE,
                    max_tokens=self._MAX_TOKENS,
                )
                ksic_category = _KsicCategory.model_validate(json.loads(validate_json(ksic_content)))

                (domestic_content, global_content) = await asyncio.gather(
                    self._openAI_search_client.fetch(
                        user_prompt=self._generate_domestic_market_research_prompt(idea, issues, features, method, ksic_category),
                        system_prompt="You are a market research assistant that provides detailed and accurate market analysis.",
                        timeout_seconds=self._TIMEOUT_SECONDS,
                        temperature=self._TEMPERATURE,
                        max_tokens=self._MAX_TOKENS,
                    ),
                    self._openAI_search_client.fetch(
                        user_prompt=self._generate_global_market_research_prompt(idea, issues, features, method),
                        system_prompt="You are a market research assistant that provides detailed and accurate market analysis.",
                        timeout_seconds=self._TIMEOUT_SECONDS,
                        temperature=self._TEMPERATURE,
                        max_tokens=self._MAX_TOKENS,
                    ),
                )

                domestic_market_research = _DomesticMarketData.model_validate(json.loads(validate_json(domestic_content)))
                global_market_research = _GlobalMarketData.model_validate(json.loads(validate_json(global_content)))

                return MarketResearchServiceResponse(
                    domestic_market_research=domestic_market_research,
                    global_market_research=global_market_research,
                    ksic_category=ksic_category,
                )

            return await retry(
                function=operation,
                max_attempts=self._MAX_ATTEMPTS,
            )

        except JSONValidationError as exception:
            raise JSONValidationError(f"시장 조사 JSON 형식 검증 오류가 발생했습니다: {str(exception)}") from exception
        except ValidationError as exception:
            raise ModelValidationError(f"시장 조사 모델 검증 오류가 발생했습니다: {str(exception)}") from exception
        except ExternalAPIError:
            raise
        except Exception as exception:
            raise AnalysisServiceError(f"시장 조사 서비스에서 오류가 발생했습니다: {str(exception)}") from exception

    def _generate_ksic_classification_prompt(
        self,
        idea: str,
    ) -> str:
        return dedent(
            f"""
            다음 형식으로 정확히 응답해주세요:
            {{
                "large": {{"code": "A", "name": "대분류명"}},
                "medium": {{"code": "A1", "name": "중분류명"}},
                "small": {{"code": "A11", "name": "소분류명"}},
                "detail": {{"code": "A111", "name": "세분류명"}}
            }}

            한국표준산업분류 11차 개정판 기준으로 다음 비즈니스 아이디어에 해당하는 가장 적합한 산업분류를 위 JSON 형식으로 응답해주세요.
            비즈니스 아이디어: {idea}
            반드시 실제 한국표준산업분류 코드와 명칭을 사용하고, 11차 개정판 기준(최신)으로 작성해주세요.
            출처를 포함해 정확하게 응답해주세요.
            """
        ).strip()

    def _generate_domestic_market_research_prompt(
        self,
        idea: str,
        issues: List[str],
        features: List[str],
        method: str,
        ksic_category: _KsicCategory,
    ) -> str:
        return dedent(
            f"""
            다음 비즈니스 아이디어에 대한 국내 시장 분석을 JSON 형식으로 제공해주세요:
            비즈니스 아이디어: {idea}
            해결하고자 하는 문제: {issues}
            핵심 기능/요소: {features}
            방법론: {method}
            한국표준산업분류(KSIC) 정보:
            - 대분류: {ksic_category.large.name} ({ksic_category.large.code})
            - 중분류: {ksic_category.medium.name} ({ksic_category.medium.code})
            - 소분류: {ksic_category.small.name} ({ksic_category.small.code})
            - 세분류: {ksic_category.detail.name} ({ksic_category.detail.code})

            다음 JSON 형식으로 응답해주세요 (모든 필드 반드시 포함):
            {{
                "ksicCode": "{ksic_category.detail.code}",
                "ksicCategory": "{ksic_category.detail.name}",
                "marketSizeByYear": [
                    {{"year": 2020, "size": "숫자만 입력(단위 없이, 예: 10,000,000)", "growthRate": "숫자만 입력(%, 기호 없이)"}},
                    {{"year": 2021, "size": "숫자만 입력(단위 없이, 예: 10,000,000)", "growthRate": "숫자만 입력(%, 기호 없이)"}},
                    {{"year": 2022, "size": "숫자만 입력(단위 없이, 예: 10,000,000)", "growthRate": "숫자만 입력(%, 기호 없이)"}},
                    {{"year": 2023, "size": "숫자만 입력(단위 없이, 예: 10,000,000)", "growthRate": "숫자만 입력(%, 기호 없이)"}},
                    {{"year": 2024, "size": "숫자만 입력(단위 없이, 예: 10,000,000)", "growthRate": "숫자만 입력(%, 기호 없이)"}},
                    {{"year": 2025, "size": "숫자만 입력(단위 없이, 예: 10,000,000)(예상)", "growthRate": "숫자만 입력(%, 기호 없이)"}}
                ],
                "averageRevenue": "숫자만 입력(단위 없이, 예: 10,000,000)",
                "averageRevenueSource": "출처 정보(반드시 구체적 기관명 또는 보고서명 포함)",
                "competitionLevel": "높음/중간/낮음",
                "keyCompetitors": ["경쟁사1", "경쟁사2", "경쟁사3"],
                "marketTrends": ["트렌드1", "트렌드2", "트렌드3"],
                "sources": ["출처1", "출처2", "출처3"]
            }}

            응답은 반드시 위 형식의 JSON 객체만 포함하고, 시장 규모와 성장률은 최근 5년(2020-2025) 데이터를 모두 포함해야 합니다.
            평균 매출에는 반드시 구체적인 출처(기관명, 보고서명 등)를 명시해주세요.
            모든 정보는 실제 시장 데이터를 기반으로 작성하고, 응답은 한국어로 해주세요.
            """
        ).strip()

    def _generate_global_market_research_prompt(
        self,
        idea: str,
        issues: List[str],
        features: List[str],
        method: str,
    ) -> str:
        return dedent(
            f"""
            다음 비즈니스 아이디어에 대한 글로벌 시장 분석을 JSON 형식으로 제공해주세요:
            비즈니스 아이디어: {idea}
            해결하고자 하는 문제: {issues}
            핵심 기능/요소: {features}
            방법론: {method}

            다음 JSON 형식으로 응답해주세요 (모든 필드 반드시 포함):
            {{
                "marketSizeByYear": [
                    {{"year": 2020, "size": "숫자만 입력(단위 없이, 예: 10,000,000)", "growthRate": "숫자만 입력(%, 기호 없이)"}},
                    {{"year": 2021, "size": "숫자만 입력(단위 없이, 예: 10,000,000)", "growthRate": "숫자만 입력(%, 기호 없이)"}},
                    {{"year": 2022, "size": "숫자만 입력(단위 없이, 예: 10,000,000)", "growthRate": "숫자만 입력(%, 기호 없이)"}},
                    {{"year": 2023, "size": "숫자만 입력(단위 없이, 예: 10,000,000)", "growthRate": "숫자만 입력(%, 기호 없이)"}},
                    {{"year": 2024, "size": "숫자만 입력(단위 없이, 예: 10,000,000)", "growthRate": "숫자만 입력(%, 기호 없이)"}},
                    {{"year": 2025, "size": "숫자만 입력(단위 없이, 예: 10,000,000)(예상)", "growthRate": "숫자만 입력(%, 기호 없이)"}}
                ],
                "averageRevenue": "숫자만 입력(단위 없이, 예: 10,000,000)",
                "averageRevenueSource": "출처 정보(반드시 구체적 기관명 또는 보고서명 포함)",
                "competitionLevel": "높음/중간/낮음",
                "keyCompetitors": ["경쟁사1", "경쟁사2", "경쟁사3"],
                "marketTrends": ["트렌드1", "트렌드2", "트렌드3"],
                "sources": ["출처1", "출처2", "출처3"]
            }}

            응답은 반드시 위 형식의 JSON 객체만 포함하고, 시장 규모와 성장률은 최근 5년(2020-2025) 데이터를 모두 포함해야 합니다.
            평균 매출에는 반드시 구체적인 출처(기관명, 보고서명 등)를 명시해주세요.
            모든 정보는 실제 시장 데이터를 기반으로 작성하고, 응답은 한국어로 해주세요.
            """
        ).strip()
