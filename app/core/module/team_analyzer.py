from .base_client import BaseAnalyzer
import logging
import hashlib
import functools
import time

# 로거 설정
logger = logging.getLogger(__name__)
logger.propagate = False  # 상위 로거로 전파하지 않음

# 결과 캐싱을 위한 딕셔너리
_TEAM_ANALYSIS_CACHE = {}
# 캐시 유효 시간 (초)
CACHE_TTL = 3600 * 24  # 24시간

class TeamAnalyzer(BaseAnalyzer):
    """팀 구성 분석 모듈"""
    
    def __init__(self):
        super().__init__()
        self.timeout = 60  # 분석에 최대 60초 제한
        
    async def analyze_team(self, idea: str, problem: dict = None, solution: dict = None) -> dict:
        """팀 분석을 수행하는 메서드"""
        # 캐시 키 생성
        cache_key = self._generate_cache_key(idea, problem, solution)
        
        # 캐시에서 결과 확인
        if cache_key in _TEAM_ANALYSIS_CACHE:
            cached_data, timestamp = _TEAM_ANALYSIS_CACHE[cache_key]
            if (time.time() - timestamp) < CACHE_TTL:
                logger.info("팀 분석: 캐시된 결과 사용")
                return cached_data
        
        # 문제와 해결책에서 추가 정보 추출
        issues = ' '.join(problem.get('identifiedIssues', [])) if problem else ''
        core_elements = ' '.join(solution.get('coreElements', [])) if solution else ''
        
        query = (
            f"다음 비즈니스 아이디어를 성공적으로 실현하기 위해 필요한 팀 구성을 상세히 분석해주세요:\n\n"
            f"비즈니스 아이디어: {idea}\n"
            f"해결하고자 하는 문제: {issues}\n"
            f"핵심 기능/요소: {core_elements}\n\n"
            f"다음 정보를 포함한 분석이 필요합니다:\n"
            f"1. 필요한 직책/역할(최소 3가지): 구체적인 직함과 역할\n"
            f"2. 각 역할별 필요 역량 및 경험: 구체적인 기술, 지식, 자격 요건\n"
            f"3. 담당해야 할 업무 범위: 상세한 업무 내용\n"
            f"4. 팀 구성의 우선순위: 초기 스타트업 단계에서 먼저 영입해야 할 역할 순서\n"
            f"최소 필요 인력부터 이상적인 팀 구성까지 단계별로 제안해주세요.\n"
            f"응답은 한국어로 작성하고, 출처를 포함해주세요."
        )
        
        # 타임아웃 처리
        start_time = time.time()
        try:
            logger.info("팀 분석: 새로운 분석 요청 시작")
            # 부모 클래스의 analyze 메서드 호출
            response = await super().analyze(query)
            result = self._parse(response)
            
            # 결과 캐싱
            _TEAM_ANALYSIS_CACHE[cache_key] = (result, time.time())
            logger.info("팀 분석: 분석 완료")
            return result
            
        except Exception as e:
            elapsed = time.time() - start_time
            if elapsed >= self.timeout:
                logger.error("팀 분석: 시간 초과 (60초)")
                return {"content": "팀 분석 시간 초과 (60초)"}
            logger.error("팀 분석: 분석 실패 - %s", str(e), exc_info=True)  # 스택 트레이스 추가
            return {"content": "팀 분석 데이터 없음"}
    
    def _generate_cache_key(self, idea: str, problem: dict = None, solution: dict = None) -> str:
        """입력 데이터로부터 캐시 키 생성"""
        key_str = idea
        
        if problem:
            key_str += str(problem.get('identifiedIssues', ''))
            
        if solution:
            key_str += str(solution.get('coreElements', ''))
            
        return hashlib.md5(key_str.encode('utf-8')).hexdigest()
        
    def _parse(self, data: dict | str) -> dict:
        try:
            # 문자열 응답 처리
            if isinstance(data, str):
                return {"content": data}
                
            # 딕셔너리 응답 처리
            if not isinstance(data, dict):
                logger.error("팀 분석: 응답 형식 오류 - %s 타입", type(data).__name__)  # lazy evaluation 사용
                return {"content": "팀 분석 데이터 없음"}
                
            if 'choices' not in data:
                logger.error("팀 분석: 응답 형식 오류 - 'choices' 키 없음")
                return {"content": "팀 분석 데이터 없음"}
                
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
                logger.error("팀 분석: 응답 형식 오류 - 예상치 못한 구조")
                return {"content": "팀 분석 데이터 없음"}
                
            if not content:
                logger.error("팀 분석: 응답 내용 없음")
                return {"content": "팀 분석 데이터 없음"}
                
            return {"content": content}
            
        except Exception as e:
            logger.error("팀 분석: 응답 처리 오류 - %s", str(e))  # lazy evaluation 사용
            return {"content": "팀 분석 데이터 없음"}
