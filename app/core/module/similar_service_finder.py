from typing import List, Dict, Any, Optional
import json
import logging
import re
import requests
from .base_client import BaseAnalyzer

logger = logging.getLogger(__name__)

class SimilarServiceFinder(BaseAnalyzer):
    """유사 서비스 분석 모듈"""
    
    def __init__(self):
        super().__init__()
    
    async def find(self, idea: str, core_elements: str = '') -> List[Dict]:
        try:
            query = (
                f"다음 비즈니스 아이디어와 유사한 서비스를 JSON 형식으로 제공해주세요:\n"
                f"비즈니스 아이디어: {idea}\n"
                f"핵심 기능/요소: {core_elements}\n\n"
                f"요구사항:\n"
                f"1. 실제 존재하는 서비스 중 유사도가 높은 상위 5개만 선별해주세요.\n"
                f"2. 다음 JSON 형식으로 응답해주세요:\n\n"
                f"[\n"
                f"  {{\n"
                f"    \"name\": \"서비스 이름\",\n"
                f"    \"url\": \"https://www.example.com\",\n"
                f"    \"description\": \"500자 이상의 서비스 상세 설명 - 핵심 기능, 특징, 사용 방법 등 포함\",\n"
                f"    \"targetAudience\": \"주요 타겟층 - 연령, 성별, 직업 등 구체적 명시\",\n"
                f"    \"tags\": [\"태그1\", \"태그2\", \"태그3\", \"태그4\", \"태그5\"],\n"
                f"    \"summary\": \"30자 내외의 서비스 한줄 요약\",\n"
                f"    \"similarity\": 85\n"
                f"  }}\n"
                f"]\n\n"
                f"응답은 위 형식의 JSON 배열만 포함해주세요.\n"
                f"서비스의 URL은 실제 존재하는 URL이어야 합니다.\n"
                f"description은 500자 이상의 상세 설명으로, 해당 서비스의 핵심 기능과 특징을 자세히 설명해야 합니다.\n"
                f"summary는 30자 내외의 간결한 한줄 요약입니다.\n"
                f"similarity는 코사인 유사도(70%)와 자카드 유사도(30%)를 가중평균하여 100점 만점으로 계산한 값입니다.\n"
                f"응답은 한국어로 작성해주세요."
            )
            
            logger.debug(f"유사 서비스 검색 쿼리: {query[:100]}...")
            response = await self.analyze(query)
            
            services = self._parse_services(response)
            return services[:5]  # 최대 5개까지만
            
        except Exception as e:
            logger.error(f"유사 서비스 검색 실패: {str(e)}")
            return [{"name": "검색 오류", "error": str(e), "url": "", "description": "서비스 검색 중 오류 발생", "tags": ["오류"], "summary": "오류", "similarity": 0}]
    
    def _parse_services(self, data: dict) -> List[Dict]:
        """서비스 정보 파싱 개선"""
        try:
            if not data or 'choices' not in data:
                logger.error("유효하지 않은 응답 데이터")
                return []
                
            # API 응답 구조 확인 및 처리 (핵심 수정 부분)
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
                logger.error(f"예상치 못한 API 응답 구조: {data['choices']}")
                return []
            
            if not content:
                logger.error("응답 콘텐츠 없음")
                return []
                
            # JSON 파싱 시도
            try:
                # 코드 블록 제거
                clean_content = content.strip()
                if clean_content.startswith("``````"):
                    clean_content = clean_content[3:-3].strip()
                    if clean_content.startswith("json"):
                        clean_content = clean_content[4:].strip()
                
                # JSON 파싱
                parsed_data = json.loads(clean_content)
                
                # 배열 또는 객체 처리
                if isinstance(parsed_data, list):
                    return self._validate_services(parsed_data)
                elif isinstance(parsed_data, dict):
                    return self._validate_services([parsed_data])
                else:
                    raise ValueError("예상치 못한 JSON 구조")
                    
            except json.JSONDecodeError:
                # JSON 추출 실패 시 정규식 기반 파싱
                return self._extract_services_from_text(content)
                
        except Exception as e:
            logger.error(f"서비스 파싱 실패: {str(e)}")
            return []
    
    def _validate_services(self, services: List[Dict]) -> List[Dict]:
        """서비스 데이터 검증 및 보완"""
        valid_services = []
        
        for service in services:
            # 필수 필드 확인
            if not service.get('name'):
                continue
                
            # 필드 보완
            if not service.get('description'):
                service['description'] = f"{service.get('name')}는 사용자에게 가치를 제공하는 서비스입니다."
            
            if not service.get('summary'):
                # description이 있으면 축약해서 summary 생성
                desc = service.get('description', '')
                service['summary'] = desc[:30] + ('...' if len(desc) > 30 else '')
            
            if not service.get('tags') or not isinstance(service.get('tags'), list):
                service['tags'] = ["정보 없음"]
            
            if not service.get('url'):
                service['url'] = f"https://www.google.com/search?q={service.get('name').replace(' ', '+')}"
            
            if not service.get('targetAudience'):
                service['targetAudience'] = "일반 사용자"
            
            if not service.get('similarity') or not isinstance(service.get('similarity'), (int, str)):
                service['similarity'] = "70"
            
            # 유사도 점수가 문자열이면 정수로 변환
            if isinstance(service.get('similarity'), str):
                try:
                    service['similarity'] = int(service['similarity'])
                except ValueError:
                    service['similarity'] = 70
            
            valid_services.append(service)
        
        return valid_services
    
    def _extract_services_from_text(self, text: str) -> List[Dict]:
        """텍스트에서 서비스 정보 추출"""
        services = []
        # 서비스 구분 패턴
        service_patterns = [
            r'^\d+\.\s*(.+?)(?=\n)',  # "1. 서비스명" 형식
            r'^\*\s*(.+?)(?=\n)',     # "* 서비스명" 형식
            r'^\-\s*(.+?)(?=\n)'      # "- 서비스명" 형식
        ]
        
        # 서비스 이름 추출
        service_names = []
        for pattern in service_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            service_names.extend([match.strip() for match in matches if match.strip()])
        
        # 각 서비스에 대한 정보 추출
        for name in service_names:
            service = {
                'name': name,
                'url': f"https://www.google.com/search?q={name.replace(' ', '+')}",
                'description': f"{name}은(는) 사용자에게 가치를 제공하는 서비스입니다.",
                'targetAudience': "일반 사용자",
                'tags': ["정보 없음"],
                'summary': name,
                'similarity': 70
            }
            services.append(service)
        
        return services
