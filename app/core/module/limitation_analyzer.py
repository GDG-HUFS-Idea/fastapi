from .base_client import BaseAnalyzer
import logging

logger = logging.getLogger(__name__)

class LimitationAnalyzer(BaseAnalyzer):
    """한계점 분석 모듈"""
    
    def __init__(self):
        super().__init__()
        
    async def analyze(self, idea: str, problem: dict = None, solution: dict = None) -> dict:
        # 문제와 해결책에서 추가 정보 추출
        issues = ' '.join(problem.get('identifiedIssues', [])) if problem else ''
        core_elements = ' '.join(solution.get('coreElements', [])) if solution else ''
        
        query = (
            f"다음 비즈니스 아이디어의 사업화 과정에서 발생할 수 있는 잠재적 한계점과 위험 요소를 상세히 분석해주세요:\n\n"
            f"비즈니스 아이디어: {idea}\n"
            f"해결하고자 하는 문제: {issues}\n"
            f"핵심 기능/요소: {core_elements}\n\n"
            f"다음 정보를 포함한 분석이 필요합니다:\n"
            f"1. 법률적 규제 및 제약(구체적인 법률명과 조항 포함)\n"
            f"2. 특허 관련 이슈 및 지적재산권 문제(유사 특허 존재 여부)\n"
            f"3. 시장 진입 장벽(기존 경쟁사, 초기 투자 요구 등)\n"
            f"4. 기술적 제약 및 구현 난이도\n"
            f"5. 잠재적 고객 수용성 문제\n\n"
            f"각 항목별로 구체적인 사례와 데이터를 포함하여 분석해주세요.\n"
            f"응답은 한국어로 작성하고, 출처를 포함해주세요."
        )
        
        response = await self.analyze(query)
        return self._parse(response)
        
    def _parse(self, data: dict) -> dict:
        try:
            content = data['choices'][0]['message']['content']
            return content
        except (KeyError, IndexError) as e:
            logger.error(f"한계점 분석 응답 형식 오류: {str(e)}")
            return "한계점 분석 데이터 없음"
