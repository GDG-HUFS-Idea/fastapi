import json
import re
import logging
from typing import Dict, Any, Optional
from openai import OpenAI, APIError, AuthenticationError, RateLimitError
from app.core.config import env
from app.core.module.prompt_builder import PromptBuilder
from app.core.analysis.validators import ReportValidator

logger = logging.getLogger(__name__)

def generate_report(data: Dict[str, Any], task_id: str = None) -> Dict[str, Any]:
    """
    최종 보고서를 생성합니다.
    task_id가 제공되면 진행 상태를 업데이트합니다.
    """
    logger.info(f"OpenAI GPT 호출 시작 (task_id: {task_id})")
    openai_client = OpenAI(api_key=env.OPENAI_API_KEY)

    prompt = PromptBuilder.build(data)
    try:
        logger.debug(f"OpenAI API 호출 - {data.get('idea', '')[:30]}...")
        
        # 스트리밍 모드로 API 호출
        stream = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "당신은 비즈니스 분석 전문가입니다. "
                        "객관적인 데이터를 기반으로 사업 아이디어를 분석하고, 점수를 산출하세요."
                        "추가 설명이나 불필요한 문장은 포함하지 마세요. "
                        "반드시 중괄호 { }로 시작하는 순수 JSON을 반환해야 합니다."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            timeout=300,  # 5분 타임아웃
            max_tokens=4000,
            stream=True
        )
        
        logger.debug("OpenAI API 스트리밍 응답 수신 시작")
        
        # 스트리밍 응답을 모아서 처리
        content_chunks = []
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                content_part = chunk.choices[0].delta.content
                content_chunks.append(content_part)
        
        # 모든 청크를 합쳐 전체 내용 구성
        content = ''.join(content_chunks)
        logger.debug(f"OpenAI API 스트리밍 응답 수신 완료 (총 {len(content_chunks)}개 청크)")

        if not content or len(content.strip()) < 20:
            logger.error(f"API 응답이 비어있거나 너무 짧습니다 (task_id: {task_id})")
            return _create_fallback_report(data)

        logger.debug(f"원시 응답 데이터 (일부): {content[:200]}...")
        report = _extract_json_from_content(content)

        if not report or not isinstance(report, dict):
            logger.error(f"파싱된 리포트가 유효한 딕셔너리가 아닙니다 (task_id: {task_id})")
            return _create_fallback_report(data)

        report = _ensure_required_fields(report, data)
        logger.info(f"보고서 생성 완료 (task_id: {task_id})")
        return report

    except (APIError, AuthenticationError, RateLimitError) as oe:
        logger.error(f"OpenAI API 관련 오류 (task_id: {task_id}): {str(oe)}")
        return _create_fallback_report(data)
    except Exception as e:
        logger.error(f"리포트 생성 중 오류 발생 (task_id: {task_id}): {str(e)}")
        return _create_fallback_report(data)

def _extract_json_from_content(content: str) -> Dict:
    """응답 내용에서 JSON을 추출합니다."""
    try:
        cleaned = content.strip()
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    code_block_patterns = [
        r'```json([\s\S]*?)```',
        r'```([\s\S]*?)```'
    ]
    for pattern in code_block_patterns:
        matches = re.findall(pattern, content, re.DOTALL)
        for match in matches:
            match = match.strip()
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue

    json_start = content.find('{')
    json_end = content.rfind('}')
    if json_start != -1 and json_end != -1:
        json_str = content[json_start:json_end+1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

    logger.warning("JSON 파싱 실패, 텍스트 구조화 시도")
    return _structure_text_to_json(content)

def _structure_text_to_json(text: str) -> Dict:
    """텍스트를 JSON 구조로 변환합니다."""
    result = {"marketAnalysis": {}, "similarServices": [], "targetAudience": []}
    result["rawContent"] = text
    return result

def _ensure_required_fields(report: Dict, data: Dict) -> Dict:
    """필수 필드가 존재하는지 확인하고, 빈 값이 있는 경우 GPT에게 다시 요청합니다."""
    required_fields = {
        "marketAnalysis": {"domestic": {}, "global": {}},
        "similarServices": [],
        "targetAudience": [],
        "businessModel": {},
        "marketingStrategy": {},
        "opportunities": {},
        "limitations": {},
        "requiredTeam": [],
        "scores": {"market": 0, "opportunity": 0, "similarService": 0, "risk": 0, "total": 0},
    }

    def is_empty(value):
        """값이 비어있는지 확인하는 헬퍼 함수"""
        if value is None:
            return True
        if isinstance(value, (str, list, dict)):
            return len(value) == 0
        return False

    def check_nested_fields(obj, required):
        """중첩된 필드의 빈 값 확인"""
        if isinstance(required, dict):
            for key, sub_required in required.items():
                if key not in obj or is_empty(obj[key]):
                    return False
                if not check_nested_fields(obj[key], sub_required):
                    return False
        elif isinstance(required, list):
            if not obj or not all(not is_empty(item) for item in obj):
                return False
        return True

    # 필수 필드 존재 여부 확인
    for field, default_value in required_fields.items():
        if field not in report:
            report[field] = default_value

    # 빈 값이 있는지 확인
    has_empty_values = False
    for field, required in required_fields.items():
        if not check_nested_fields(report[field], required):
            has_empty_values = True
            break

    # 빈 값이 있으면 GPT에게 다시 요청
    if has_empty_values:
        logger.warning("보고서에 빈 값이 있어 GPT에게 다시 요청합니다")
        return generate_report(data)

    # scores 필드 처리
    if "scores" in report:
        for sf in ["market", "opportunity", "similarService", "risk"]:
            if sf not in report["scores"]:
                report["scores"][sf] = 0
        if "total" not in report["scores"]:
            sc = report["scores"]
            total = (
                float(sc["market"]) + 
                float(sc["opportunity"]) + 
                float(sc["similarService"]) + 
                float(sc["risk"])
            ) / 4
            report["scores"]["total"] = round(total, 1)

    return report

def _create_fallback_report(data: Dict) -> Dict:
    """오류 발생 시 기본 보고서를 생성합니다."""
    idea = data.get('idea', '아이디어 정보 없음')
    return {
        "idea": idea,
        "marketAnalysis": {
            "domestic": {"rawContent": "국내 시장 분석 실패"},
            "global": {"rawContent": "글로벌 시장 분석 실패"}
        },
        "similarServices": [],
        "targetAudience": [],
        "businessModel": {},
        "marketingStrategy": {},
        "opportunities": {},
        "limitations": {},
        "requiredTeam": [],
        "scores": {
            "market": 0, "opportunity": 0, "similarService": 0, "risk": 0, "total": 0
        }
    } 