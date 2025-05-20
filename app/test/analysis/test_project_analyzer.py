import pytest
import asyncio
from typing import Dict, Any
from app.service.analysis.project_analyzer import ProjectAnalyzer
from app.util.exception import ValidationException

@pytest.fixture
def analyzer():
    return ProjectAnalyzer()

@pytest.fixture
def valid_analysis_data() -> Dict[str, Any]:
    return {
        "problem": {
            "identifiedIssues": [
                "SNS에서 창의적인 콘텐츠를 제작하기 어려움",
                "짧은 영상 콘텐츠 제작에 대한 부담이 큼"
            ],
            "developmentMotivation": "AI 기술을 활용해 누구나 쉽게 콘텐츠를 제작할 수 있도록 지원"
        },
        "solution": {
            "coreElements": [
                "AI 기반 이미지 및 영상 생성",
                "사용자 맞춤형 추천 시스템",
                "자동 해시태그 및 설명 생성"
            ],
            "methodology": "딥러닝 기반 생성 모델 활용 (GAN, Transformer)",
            "expectedOutcome": "사용자가 AI를 활용해 쉽게 영상 콘텐츠를 제작 및 공유할 수 있는 SNS 플랫폼"
        }
    }

@pytest.mark.asyncio
async def test_analyze_project_success(analyzer: ProjectAnalyzer, valid_analysis_data: Dict[str, Any]):
    """분석 요청이 성공적으로 처리되는지 테스트"""
    # Given
    data = valid_analysis_data
    
    # When
    task_id = await analyzer.analyze_project(data)
    
    # Then
    assert task_id is not None
    assert isinstance(task_id, str)
    assert len(task_id) > 0

@pytest.mark.asyncio
async def test_analyze_project_invalid_data(analyzer: ProjectAnalyzer):
    """잘못된 데이터로 분석 요청 시 예외가 발생하는지 테스트"""
    # Given
    invalid_data = {
        "problem": {
            "identifiedIssues": [],  # 빈 배열
            "developmentMotivation": ""  # 빈 문자열
        },
        "solution": {
            "coreElements": [],
            "methodology": "",
            "expectedOutcome": ""
        }
    }
    
    # When & Then
    with pytest.raises(ValidationException):
        await analyzer.analyze_project(invalid_data)

@pytest.mark.asyncio
async def test_analyze_project_complete_flow(analyzer: ProjectAnalyzer, valid_analysis_data: Dict[str, Any]):
    """전체 분석 프로세스가 정상적으로 동작하는지 테스트"""
    # Given
    data = valid_analysis_data
    
    # When
    task_id = await analyzer.analyze_project(data)
    
    # Then
    # 1. 초기 상태 확인
    initial_status = analyzer.get_task_status(task_id)
    assert initial_status['status'] == 'pending'
    assert initial_status['progress'] == 0
    
    # 2. 분석 완료 대기 (최대 5분)
    max_wait = 300
    while max_wait > 0:
        status = analyzer.get_task_status(task_id)
        if status['status'] in ['completed', 'failed']:
            break
        await asyncio.sleep(1)
        max_wait -= 1
    
    # 3. 최종 상태 확인
    final_status = analyzer.get_task_status(task_id)
    assert final_status['status'] == 'completed'
    assert final_status['progress'] == 1.0
    
    # 4. 결과 데이터 검증
    result = final_status['result']
    assert isinstance(result, dict)
    assert 'marketAnalysis' in result
    assert 'similarServices' in result
    assert 'targetAudience' in result
    assert 'businessModel' in result
    assert 'marketingStrategy' in result
    assert 'opportunities' in result
    assert 'limitations' in result
    assert 'requiredTeam' in result
    assert 'scores' in result

@pytest.mark.asyncio
async def test_get_task_status_stream(analyzer: ProjectAnalyzer, valid_analysis_data: Dict[str, Any]):
    """상태 스트림이 정상적으로 생성되는지 테스트"""
    # Given
    data = valid_analysis_data
    task_id = await analyzer.analyze_project(data)
    
    # When
    status_stream = analyzer.get_task_status_stream(task_id)
    
    # Then
    # 스트림에서 첫 번째 상태 확인
    first_status = await anext(status_stream)
    assert isinstance(first_status, str)
    assert 'data: ' in first_status
    
    # 스트림이 제너레이터인지 확인
    assert hasattr(status_stream, '__aiter__')
    assert hasattr(status_stream, '__anext__')

@pytest.mark.asyncio
async def test_get_nonexistent_task(analyzer: ProjectAnalyzer):
    """존재하지 않는 task_id로 조회 시 예외가 발생하는지 테스트"""
    # Given
    nonexistent_task_id = "nonexistent-task-id"
    
    # When & Then
    with pytest.raises(KeyError):
        analyzer.get_task_status(nonexistent_task_id)

@pytest.mark.asyncio
async def test_analyze_project_with_minimal_data(analyzer: ProjectAnalyzer):
    """최소한의 필수 데이터로도 분석이 가능한지 테스트"""
    # Given
    minimal_data = {
        "problem": {
            "identifiedIssues": ["테스트 이슈"],
            "developmentMotivation": "테스트 동기"
        },
        "solution": {
            "coreElements": ["테스트 요소"],
            "methodology": "테스트 방법론",
            "expectedOutcome": "테스트 결과"
        }
    }
    
    # When
    task_id = await analyzer.analyze_project(minimal_data)
    
    # Then
    assert task_id is not None
    status = analyzer.get_task_status(task_id)
    assert status['status'] in ['pending', 'processing', 'completed', 'failed'] 