import asyncio
import json
import logging
import re
from typing import Callable, TypeVar, Awaitable

from app.common.exceptions import JSONValidationError

logger = logging.getLogger(__name__)

T = TypeVar('T')


async def retry(
    function: Callable[[], Awaitable[T]],
    max_attempts: int,
) -> T:
    last_exception = None

    for attempt in range(max_attempts):
        try:
            return await function()

        except Exception as exception:
            logger.warning(f"시도 {attempt + 1}/{max_attempts} 실패: {str(exception)}")
            last_exception = exception

            if attempt < max_attempts - 1:
                wait_time = attempt**2
                await asyncio.sleep(wait_time)
                continue

    assert last_exception is not None
    raise last_exception


def validate_json(
    content: str,
) -> str:
    try:
        content = content.strip()

        # Markdown 코드 블록 제거
        if content.startswith("```json"):
            content = content.removeprefix("```json").strip()
        if content.startswith("```"):
            content = content.removeprefix("```").strip()
        if content.endswith("```"):
            content = content.removesuffix("```").strip()

        # Trailing comma 제거
        content = re.sub(r",\s*[}\]]", lambda m: m.group(0)[:-1] + m.group(0)[-1], content)

        # 전체 JSON 파싱 시도
        try:
            json.loads(content)
            return content
        except json.JSONDecodeError:
            pass

        # JSON 부분 추출 시도 (배열 우선)
        for pattern in [r"\[[\s\S]*\]", r"\{[\s\S]*\}"]:
            match = re.search(pattern, content)
            if match:
                extracted = match.group(0)
                try:
                    json.loads(extracted)
                    return extracted
                except json.JSONDecodeError:
                    # 배열인 경우 복구 시도
                    if extracted.startswith('['):
                        # 마지막 쉼표 제거하고 닫기
                        if extracted.rstrip().endswith(','):
                            repaired = extracted.rstrip().rstrip(',') + ']'
                        # 불완전한 객체 제거하고 닫기
                        elif not extracted.rstrip().endswith(']'):
                            # 마지막 완전한 } 찾기
                            brace_count = 0
                            last_complete = -1
                            in_string = False

                            for i, char in enumerate(extracted):
                                if char == '"' and (i == 0 or extracted[i - 1] != '\\'):
                                    in_string = not in_string
                                elif not in_string:
                                    if char == '{':
                                        brace_count += 1
                                    elif char == '}':
                                        brace_count -= 1
                                        if brace_count == 0:
                                            last_complete = i

                            repaired = extracted[: last_complete + 1] + ']' if last_complete > 0 else extracted
                        else:
                            repaired = extracted

                        try:
                            json.loads(repaired)
                            return repaired
                        except json.JSONDecodeError:
                            continue

        raise JSONValidationError(f"유효한 JSON 구조를 찾을 수 없습니다: {content[:200]}...")

    except JSONValidationError:
        raise
    except Exception as exception:
        raise JSONValidationError(f"JSON 검증 중 오류: {str(exception)}") from exception
