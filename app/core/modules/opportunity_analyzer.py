from .base_client import BaseAnalyzer
import logging

logger = logging.getLogger(__name__)

class OpportunityAnalyzer(BaseAnalyzer):
    """기회 요인 분석 모듈"""
    
    def __init__(self):
        super().__init__()
        
    async def find(self, idea: str, problem: dict = None, solution: dict = None) -> dict:
        # 문제와 해결책에서 추가 정보 추출
        issues = ' '.join(problem.get('identifiedIssues', [])) if problem else ''
        core_elements = ' '.join(solution.get('coreElements', [])) if solution else ''
        
        query = (
            f"다음 비즈니스 아이디어의 기회 요인과 활용 가능한 지원 사업을 상세히 분석해주세요:\n\n"
            f"비즈니스 아이디어: {idea}\n"
            f"해결하고자 하는 문제: {issues}\n"
            f"핵심 기능/요소: {core_elements}\n\n"
            f"다음 정보를 포함한 분석이 필요합니다:\n"
            f"1. 시장 기회 요인(최소 3가지): 해당 아이디어가 시장에서 성공할 수 있는 외부 환경 요인\n"
            f"2. 활용 가능한 정부 지원 사업: 현재 지원 중이거나 곧 시작될 예정인 관련 지원 사업 정보\n"
            f"3. 공모전 및 액셀러레이터 프로그램: 참여 가능한 공모전, 스타트업 지원 프로그램 등\n"
            f"4. 각 지원 사업의 신청 시기 및 지원 내용: 구체적인 일정과 지원 금액\n\n"
            f"모든 정보는 최신 데이터를 기반으로 구체적으로 작성해주세요.\n"
            f"응답은 한국어로 작성하고, 출처를 포함해주세요."
        )
        
        response = await self.analyze(query)
        return self._parse(response)
        
    def _parse(self, data: dict) -> dict:
        try:
            content = data['choices'][0]['message']['content']
            return content
        except (KeyError, IndexError) as e:
            logger.error(f"기회 요인 분석 응답 형식 오류: {str(e)}")
            return "기회 요인 분석 데이터 없음"
