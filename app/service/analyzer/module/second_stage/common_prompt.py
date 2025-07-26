from textwrap import dedent


def wrap_json_instruction(output_schema_hint: str) -> str:
    return dedent(f"""
    아래 지침을 반드시 따르십시오.
    1. 결과는 반드시 **순수 JSON** 형태로만 출력하십시오. (주석/설명/코드블럭 금지)
    2. 스키마 예시는 구조만 참고하며, 키 이름은 그대로 사용합니다.
    3. 값이 없으면 null, 빈 배열([]), 빈 문자열("") 중 의미에 맞게 명시하십시오.
    4. 숫자는 숫자형으로, 불리는 boolean으로 출력하십시오.
    5. 한국어로 작성하십시오.
    ---
    JSON 스키마 힌트:
    {output_schema_hint}
    """)


def make_prompt(role_desc: str, user_context: str, output_schema_hint: str) -> str:
    return dedent(f"""
    당신은 {role_desc} 입니다. 아래 사용자 제공 정보를 바탕으로 분석을 수행한 뒤, 지침에 맞는 JSON만 출력하세요.

    [사용자 정보]
    {user_context}

    {wrap_json_instruction(output_schema_hint)}
    """)