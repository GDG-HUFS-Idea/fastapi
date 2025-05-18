from typing import Dict, Any

class ProjectOverviewValidator:
    @staticmethod
    def validate(data: Dict[str, Any]) -> bool:
        """
        요청 데이터의 유효성을 검증합니다.
        """
        required_fields = ['problem', 'motivation', 'features', 'method', 'deliverable']
        
        # 필수 필드 존재 여부 확인
        for field in required_fields:
            if field not in data or not data[field]:
                return False
            
        # 각 필드의 값이 문자열인지 확인
        for field in required_fields:
            if not isinstance(data[field], str):
                return False
            
        # 각 필드의 최소 길이 확인
        min_lengths = {
            'problem': 10,
            'motivation': 5,
            'features': 10,
            'method': 10,
            'deliverable': 5
        }
        
        for field, min_length in min_lengths.items():
            if len(data[field]) < min_length:
                return False
                
        return True

class ReportValidator:
    @staticmethod
    def validate(report: Dict[str, Any]) -> bool:
        """
        보고서의 유효성을 검증합니다.
        """
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
        for field, required in required_fields.items():
            if field not in report:
                return False
            if not check_nested_fields(report[field], required):
                return False

        # scores 필드 검증
        if "scores" in report:
            scores = report["scores"]
            required_scores = ["market", "opportunity", "similarService", "risk", "total"]
            for score in required_scores:
                if score not in scores or not isinstance(scores[score], (int, float)):
                    return False

        return True 