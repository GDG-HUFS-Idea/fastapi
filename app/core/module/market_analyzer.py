from .base_client import BaseAnalyzer
from .ksicclassifier import KSICClassifier
import logging
import json
import re

logger = logging.getLogger(__name__)

class MarketAnalyzer(BaseAnalyzer):
    """국내외 시장 분석 모듈"""
    
    def __init__(self):
        super().__init__()
    
    async def analyze(self, idea: str, problem: dict = None, solution: dict = None) -> dict:
        # KSIC 정보를 가져오기 위해 분류기 사용
        ksic_classifier = KSICClassifier()
        ksic_data = await ksic_classifier.classify(idea)
        
        # 컨텍스트 정보 추출
        issues = ' '.join(problem.get('identifiedIssues', [])) if problem else ''
        core_elements = ' '.join(solution.get('coreElements', [])) if solution else ''
        methodology = solution.get('methodology', '') if solution else ''
        
        # 구조화된 응답 요청 - KSIC 코드와 카테고리 명시적 포함
        domestic_query = (
            f"다음 비즈니스 아이디어에 대한 국내 시장 분석을 JSON 형식으로 제공해주세요:\n"
            f"비즈니스 아이디어: {idea}\n"
            f"해결하고자 하는 문제: {issues}\n"
            f"핵심 기능/요소: {core_elements}\n"
            f"방법론: {methodology}\n\n"
            f"한국표준산업분류(KSIC) 정보:\n"
            f"- 대분류: {ksic_data.get('large', {}).get('name', '정보 없음')} ({ksic_data.get('large', {}).get('code', '정보 없음')})\n"
            f"- 중분류: {ksic_data.get('medium', {}).get('name', '정보 없음')} ({ksic_data.get('medium', {}).get('code', '정보 없음')})\n"
            f"- 소분류: {ksic_data.get('small', {}).get('name', '정보 없음')} ({ksic_data.get('small', {}).get('code', '정보 없음')})\n"
            f"- 세분류: {ksic_data.get('detail', {}).get('name', '정보 없음')} ({ksic_data.get('detail', {}).get('code', '정보 없음')})\n\n"
            f"다음 JSON 형식으로 응답해주세요 (모든 필드 반드시 포함):\n"
            f"{{\n"
            f"  \"ksicCode\": \"{ksic_data.get('detail', {}).get('code', '')}\",\n"
            f"  \"ksicCategory\": \"{ksic_data.get('detail', {}).get('name', '')}\",\n"
            f"  \"marketSizeByYear\": [\n"
            f"    {{ \"year\": 2020, \"size\": \"숫자만 입력(단위 없이, 예: 10,000,000)\", \"growthRate\": \"숫자만 입력(%, 기호 없이)\" }},\n"
            f"    {{ \"year\": 2021, \"size\": \"숫자만 입력(단위 없이, 예: 10,000,000)\", \"growthRate\": \"숫자만 입력(%, 기호 없이)\" }},\n"
            f"    {{ \"year\": 2022, \"size\": \"숫자만 입력(단위 없이, 예: 10,000,000)\", \"growthRate\": \"숫자만 입력(%, 기호 없이)\" }},\n"
            f"    {{ \"year\": 2023, \"size\": \"숫자만 입력(단위 없이, 예: 10,000,000)\", \"growthRate\": \"숫자만 입력(%, 기호 없이)\" }},\n"
            f"    {{ \"year\": 2024, \"size\": \"숫자만 입력(단위 없이, 예: 10,000,000)\", \"growthRate\": \"숫자만 입력(%, 기호 없이)\" }},\n"
            f"    {{ \"year\": 2025, \"size\": \"숫자만 입력(단위 없이, 예: 10,000,000)(예상)\", \"growthRate\": \"숫자만 입력(%, 기호 없이)\" }}\n"
            f"  ],\n"
            f"  \"averageRevenue\": \"숫자만 입력(단위 없이, 예: 10,000,000)\",\n"
            f"  \"averageRevenueSource\": \"출처 정보(반드시 구체적 기관명 또는 보고서명 포함)\",\n"
            f"  \"competitionLevel\": \"높음/중간/낮음\",\n"
            f"  \"keyCompetitors\": [\"경쟁사1\", \"경쟁사2\", \"경쟁사3\"],\n"
            f"  \"marketTrends\": [\"트렌드1\", \"트렌드2\", \"트렌드3\"],\n"
            f"  \"sources\": [\"출처1\", \"출처2\", \"출처3\"]\n"
            f"}}\n\n"
            f"응답은 반드시 위 형식의 JSON 객체만 포함하고, 시장 규모와 성장률은 최근 5년(2020-2025) 데이터를 모두 포함해야 합니다.\n"
            f"평균 매출에는 반드시 구체적인 출처(기관명, 보고서명 등)를 명시해주세요.\n"
            f"모든 정보는 실제 시장 데이터를 기반으로 작성하고, 응답은 한국어로 해주세요."
        )
        
        # 글로벌 시장 쿼리도 유사하게 수정
        global_query = (
            f"다음 비즈니스 아이디어에 대한 글로벌 시장 분석을 JSON 형식으로 제공해주세요:\n"
            f"비즈니스 아이디어: {idea}\n"
            f"해결하고자 하는 문제: {issues}\n"
            f"핵심 기능/요소: {core_elements}\n"
            f"방법론: {methodology}\n\n"
            f"다음 JSON 형식으로 응답해주세요 (모든 필드 반드시 포함):\n"
            f"{{\n"
            f"  \"marketSizeByYear\": [\n"
            f"    {{ \"year\": 2020, \"size\": \"숫자만 입력(단위 없이, 예: 10,000,000)\", \"growthRate\": \"숫자만 입력(%, 기호 없이)\" }},\n"
            f"    {{ \"year\": 2021, \"size\": \"숫자만 입력(단위 없이, 예: 10,000,000)\", \"growthRate\": \"숫자만 입력(%, 기호 없이)\" }},\n"
            f"    {{ \"year\": 2022, \"size\": \"숫자만 입력(단위 없이, 예: 10,000,000)\", \"growthRate\": \"숫자만 입력(%, 기호 없이)\" }},\n"
            f"    {{ \"year\": 2023, \"size\": \"숫자만 입력(단위 없이, 예: 10,000,000)\", \"growthRate\": \"숫자만 입력(%, 기호 없이)\" }},\n"
            f"    {{ \"year\": 2024, \"size\": \"숫자만 입력(단위 없이, 예: 10,000,000)\", \"growthRate\": \"숫자만 입력(%, 기호 없이)\" }},\n"
            f"    {{ \"year\": 2025, \"size\": \"숫자만 입력(단위 없이, 예: 10,000,000)(예상)\", \"growthRate\": \"숫자만 입력(%, 기호 없이)\" }}\n"
            f"  ],\n"
            f"  \"averageRevenue\": \"숫자만 입력(단위 없이, 예: 10,000,000)\",\n"
            f"  \"averageRevenueSource\": \"출처 정보(반드시 구체적 기관명 또는 보고서명 포함)\",\n"
            f"  \"competitionLevel\": \"높음/중간/낮음\",\n"
            f"  \"keyCompetitors\": [\"경쟁사1\", \"경쟁사2\", \"경쟁사3\"],\n"
            f"  \"marketTrends\": [\"트렌드1\", \"트렌드2\", \"트렌드3\"],\n"
            f"  \"sources\": [\"출처1\", \"출처2\", \"출처3\"]\n"
            f"}}\n\n"
            f"응답은 반드시 위 형식의 JSON 객체만 포함하고, 시장 규모와 성장률은 최근 5년(2020-2025) 데이터를 모두 포함해야 합니다.\n"
            f"평균 매출에는 반드시 구체적인 출처(기관명, 보고서명 등)를 명시해주세요.\n"
            f"모든 정보는 실제 시장 데이터를 기반으로 작성하고, 응답은 한국어로 해주세요."
        )
        
        domestic_response = await self.analyze(domestic_query)
        global_response = await self.analyze(global_query)
        
        # 응답 파싱
        domestic_data = self._parse_structured(domestic_response)
        global_data = self._parse_structured(global_response)
        
        # KSIC 데이터가 응답에 없으면 분류기에서 얻은 데이터 추가
        if 'ksicCode' not in domestic_data or not domestic_data['ksicCode']:
            if isinstance(ksic_data, dict):
                domestic_data['ksicCode'] = ksic_data.get('detail', {}).get('code', '')
                domestic_data['ksicCategory'] = ksic_data.get('detail', {}).get('name', '')
            else:
                # 문자열인 경우 기본값 설정
                domestic_data['ksicCode'] = ''
                domestic_data['ksicCategory'] = ''
        
        # 성장률 및 평균 매출 데이터 검증 및 보완
        self._validate_market_data(domestic_data)
        self._validate_market_data(global_data)
        
        return {
            "domestic": domestic_data,
            "global": global_data,
            "ksic": ksic_data  # KSIC 데이터 전체 포함
        }
    
    def _clean_numeric_data(self, data: dict) -> dict:
        """숫자 데이터 정제 (단위 제거, 숫자만 표시)"""
        # marketSizeByYear 처리
        if 'marketSizeByYear' in data and isinstance(data['marketSizeByYear'], list):
            for item in data['marketSizeByYear']:
                if isinstance(item, dict):
                    # size 필드 정제
                    if 'size' in item:
                        item['size'] = self._extract_number(item['size'])
                    # growthRate 필드 정제
                    if 'growthRate' in item:
                        item['growthRate'] = self._extract_number(item['growthRate'])

        # averageRevenue 정제
        if 'averageRevenue' in data:
            data['averageRevenue'] = self._extract_number(data['averageRevenue'])

        return data

    def _extract_number(self, value) -> str:
        """문자열에서 숫자만 추출하는 함수"""
        if not isinstance(value, str):
            return str(value)

        # 숫자만 추출 (소수점, 콤마 포함)
        import re
        numbers = re.findall(r'[\d,\.]+', value)
        if numbers:
            # 콤마 제거
            return numbers[0].replace(',', '')

        return '0'

    
    def _validate_market_data(self, data: dict) -> None:
        """시장 데이터 검증 및 보완"""
        # 평균 매출 출처 확인
        if 'averageRevenue' in data and 'averageRevenueSource' not in data:
            data['averageRevenueSource'] = "업계 데이터 기반 추정"

        # growthRates에 출처 필드 확인
        if 'growthRates' in data and 'source' not in data.get('growthRates', {}):
            data.setdefault('growthRates', {})['source'] = "업계 데이터 기반 추정"

        # 연도별 데이터 확인
        if 'marketSizeByYear' not in data or not isinstance(data['marketSizeByYear'], list):
            data['marketSizeByYear'] = []
            # 기본 연도별 데이터 설정
            for year in range(2020, 2026):
                data['marketSizeByYear'].append({
                    "year": year,
                    "size": "데이터 없음",
                    "growthRate": "데이터 없음",
                    "source": "데이터 없음"
                })
        else:
            # 각 연도별 데이터에 출처 필드 확인
            for item in data['marketSizeByYear']:
                if isinstance(item, dict) and 'source' not in item:
                    item['source'] = "업계 데이터 기반 추정"

            # marketSizeByYear에 전체 출처 필드 확인
            if 'source' not in data:
                data['source'] = "업계 데이터 기반 추정"

        # 부족한 연도 데이터 보완
        years = {item['year'] for item in data['marketSizeByYear'] if isinstance(item, dict) and 'year' in item}
        for year in range(2020, 2026):
            if year not in years:
                data['marketSizeByYear'].append({
                    "year": year,
                    "size": "데이터 없음",
                    "growthRate": "데이터 없음",
                    "source": "데이터 없음"
                })
    
    def _parse_structured(self, data: dict) -> dict:
        """JSON 응답 파싱 개선"""
        try:
            if not data or 'choices' not in data:
                logger.error("유효하지 않은 응답 데이터")
                return {"error": "유효하지 않은 응답 데이터"}

            # API 응답 구조 확인 및 처리
            content = ""
            if isinstance(data['choices'], list):
                # OpenAI 형식 응답 처리
                if len(data['choices']) > 0 and 'message' in data['choices'][0]:
                    content = data['choices'][0]['message']['content']
            elif isinstance(data['choices'], dict):
                # Perplexity 형식 응답 처리
                if 'message' in data['choices']:
                    content = data['choices']['message']['content']
            else:
                logger.error("예상치 못한 API 응답 구조")
                return {"error": "예상치 못한 API 응답 구조"}

            if not content:
                return {"error": "응답 콘텐츠 없음"}

            # JSON 파싱 시도
            try:
                # 코드 블록 제거
                clean_content = content.strip()
                if clean_content.startswith("``````"):
                    clean_content = clean_content[3:-3].strip()
                    # json 접두어 제거
                    if clean_content.startswith("json"):
                        clean_content = clean_content[4:].strip()

                # JSON 파싱
                parsed_data = json.loads(clean_content)  # 1차 파싱

                # ▼▼▼ 추가된 정제 로직 ▼▼▼
                if isinstance(parsed_data, dict):
                    # 숫자 필드 정제
                    parsed_data = self._clean_numeric_data(parsed_data)
                    # 스키마 검증
                    validated_data = self._validate_schema(parsed_data)
                    return validated_data
                else:
                    logger.warning("파싱된 데이터가 딕셔너리 형식이 아님")
                    return {"rawContent": content, "error": "잘못된 데이터 형식"}
                # ▲▲▲ 정제 로직 종료 ▲▲▲

            except json.JSONDecodeError:
                # JSON 형식 추출 실패 시 원본 콘텐츠 반환
                return {"rawContent": content, "error": "JSON 파싱 실패"}

        except Exception as e:
            logger.error(f"시장 분석 응답 처리 오류: {str(e)}")
            return {"error": f"시장 분석 데이터 파싱 오류: {str(e)}"}
