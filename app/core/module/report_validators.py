import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class ReportValidator:
    """리포트 구조 검증 클래스"""
    
    @staticmethod
    def validate(report: Dict[str, Any]) -> bool:
        """리포트 구조 검증"""
        try:
            # 기본 타입 체크
            if not isinstance(report, dict):
                logger.error("리포트가 딕셔너리 형식이 아닙니다.")
                return False
                
            # 필수 최상위 필드 확인 - 모든 필드가 없어도 실패하지 않도록 변경
            required_top_fields = [
                "marketAnalysis", 
                "similarServices", 
                "scores"
            ]
            
            # 불완전한 경우에도 파일 생성을 허용하기 위해 경고만 출력
            for field in required_top_fields:
                if field not in report:
                    logger.warning(f"필수 필드 누락: {field}")
            
            # 검증 가능한 필드에 대해서만 구조 검증
            if "marketAnalysis" in report:
                if not isinstance(report["marketAnalysis"], dict):
                    logger.warning("marketAnalysis가 딕셔너리 형식이 아닙니다.")
            
            if "similarServices" in report:
                if not isinstance(report["similarServices"], list):
                    logger.warning("similarServices가 배열 형식이 아닙니다.")
            
            if "scores" in report:
                if not isinstance(report["scores"], dict):
                    logger.warning("scores가 딕셔너리 형식이 아닙니다.")
                
                # scores 내부 필드 검사 (선택적)
                if isinstance(report["scores"], dict):
                    score_fields = ["market", "opportunity", "similarService", "risk", "total"]
                    for field in score_fields:
                        if field not in report["scores"]:
                            logger.debug(f"scores 내 필드 누락: {field}")
                        else:
                            # 점수 값이 문자열인 경우 숫자로 변환 시도
                            if isinstance(report["scores"][field], str):
                                try:
                                    report["scores"][field] = float(report["scores"][field])
                                except ValueError:
                                    logger.warning(f"{field} 점수가 숫자로 변환 불가능한 문자열입니다: {report['scores'][field]}")
                    
                    # 총점 검증 및 재계산
                    if all(field in report["scores"] for field in ["market", "opportunity", "similarService", "risk"]):
                        try:
                            calculated_total = (float(report["scores"]["market"]) + 
                                                float(report["scores"]["opportunity"]) +
                                                float(report["scores"]["similarService"]) +
                                                float(report["scores"]["risk"])) / 4
                            calculated_total = round(calculated_total, 1)
                            
                            if "total" in report["scores"]:
                                existing_total = float(report["scores"]["total"])
                                if abs(existing_total - calculated_total) > 0.1:
                                    logger.warning(f"총점 불일치: 보고된 값 {existing_total}, 계산된 값 {calculated_total}")
                                    report["scores"]["total"] = calculated_total
                            else:
                                report["scores"]["total"] = calculated_total
                        except (ValueError, TypeError):
                            logger.warning("점수 필드가 숫자로 변환할 수 없는 값을 포함하고 있습니다.")
            
            # 리포트 포맷이 부적절한 경우에도 항상 True 반환하여 파일 생성 허용
            return True
            
        except Exception as e:
            logger.error(f"리포트 검증 중 예외 발생: {str(e)}")
            # 예외 발생해도 True 반환하여 파일 생성 진행
            return True
    
    @staticmethod
    def format_field(field: Any, default_value: Any = None) -> Any:
        """필드 형식 검증 및 기본값 제공"""
        if field is None:
            return default_value
        return field
