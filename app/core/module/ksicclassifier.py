from .base_client import BaseAnalyzer
import json
import logging
import re

logger = logging.getLogger(__name__)

class KSICClassifier(BaseAnalyzer):
    """한국 표준 산업 분류기"""
    
    def __init__(self):
        super().__init__()
        
    async def classify(self, idea: str) -> dict:
        query = (
            f"다음 형식으로 정확히 응답해주세요:\n"
            "{\n"
            ' "large": {"code": "A", "name": "대분류명"},\n'
            ' "medium": {"code": "A1", "name": "중분류명"},\n'
            ' "small": {"code": "A11", "name": "소분류명"},\n'
            ' "detail": {"code": "A111", "name": "세분류명"}\n'
            "}\n\n"
            f"한국표준산업분류 11차 개정판 기준으로 다음 비즈니스 아이디어에 해당하는 가장 적합한 산업분류를 위 JSON 형식으로 응답해주세요.\n\n"
            f"비즈니스 아이디어: {idea}\n\n"
            f"반드시 실제 한국표준산업분류 코드와 명칭을 사용하고, 11차 개정판 기준(최신)으로 작성해주세요.\n"
            f"출처를 포함해 정확하게 응답해주세요."
        )
        
        response = await self.analyze(query)
        return self._parse(response)
        
    def _parse(self, data: str) -> dict:
        try:
            # JSON 문자열 추출을 위한 전처리
            json_str = data
            
            if '```json' in data:
                # 코드 블록에서 JSON 추출
                json_str = data.split('```json')[1].split('```')[0]
            elif '```' in data:
                # 일반 코드 블록에서 JSON 추출
                json_str = data.split('```')[1].split('```')[0]
                
            # 문자열 정리
            json_str = json_str.strip()
            
            # JSON 파싱
            parsed = json.loads(json_str)
            
            return {
                "large": {"code": parsed['large']['code'], "name": parsed['large']['name']},
                "medium": {"code": parsed['medium']['code'], "name": parsed['medium']['name']},
                "small": {"code": parsed['small']['code'], "name": parsed['small']['name']},
                "detail": {"code": parsed['detail']['code'], "name": parsed['detail']['name']}
            }
        except KeyError as e:
            logger.error(f"KSIC 응답 키 누락: {str(e)}")
            return {
                "large": {"code": "Unknown", "name": "Unknown"},
                "medium": {"code": "Unknown", "name": "Unknown"},
                "small": {"code": "Unknown", "name": "Unknown"},
                "detail": {"code": "Unknown", "name": "Unknown"}
            }
        except json.JSONDecodeError as e:
            logger.error(f"KSIC 유효하지 않은 JSON 응답: {str(e)}\n응답 내용: {data[:100]}...")
            return {
                "large": {"code": "Invalid", "name": "Invalid Format"},
                "medium": {"code": "Invalid", "name": "Invalid Format"},
                "small": {"code": "Invalid", "name": "Invalid Format"},
                "detail": {"code": "Invalid", "name": "Invalid Format"}
            }
