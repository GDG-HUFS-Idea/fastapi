from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.service.analysis.project_analyzer import ProjectAnalyzer
from app.util.enum import TaskStatus
import logging
import traceback
import json

router = APIRouter()
logger = logging.getLogger(__name__)

class AnalysisRequest(BaseModel):
    """분석 요청 데이터 모델"""
    problem: Dict[str, Any]
    solution: Dict[str, Any]

class AnalysisResponse(BaseModel):
    """분석 응답 데이터 모델"""
    task_id: str
    status: str
    message: str

def get_project_analyzer() -> ProjectAnalyzer:
    """ProjectAnalyzer 싱글톤 인스턴스를 제공하는 의존성"""
    return ProjectAnalyzer.get_instance()

@router.post("/test/analyze")
async def test_project_analysis(
    request: AnalysisRequest,
    project_analyzer: ProjectAnalyzer = Depends(get_project_analyzer)
):
    """
    프로젝트 분석 테스트 엔드포인트
    
    이 엔드포인트는 ProjectAnalyzer의 analyze_project 메서드를 테스트합니다.
    실제 분석 서비스의 동작을 확인하기 위한 용도입니다.
    SSE(Server-Sent Events)를 통해 실시간으로 분석 상태를 전송합니다.
    """
    try:
        logger.info(f"분석 요청 수신: {request.dict()}")
        
        # 요청 데이터를 하나의 딕셔너리로 통합
        analysis_data = {
            "problem": request.problem,
            "solution": request.solution
        }
        
        # 분석 요청
        task_id = await project_analyzer.analyze_project(data=analysis_data)
        
        async def event_generator():
            try:
                # 초기 상태 전송
                task = project_analyzer.task_manager.get_task_info(task_id)
                initial_data = {
                    'task_id': task_id,
                    'status': task['status'],
                    'message': task['message']
                }
                yield f"data: {json.dumps(initial_data, ensure_ascii=False)}\n\n"
                
                # 상태 업데이트 스트림
                async for event in project_analyzer.get_task_status_stream(task_id):
                    yield event
                    
            except Exception as e:
                logger.error(f"이벤트 스트림 생성 중 오류 발생: {str(e)}")
                error_data = {'error': f'스트림 오류: {str(e)}'}
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        error_detail = f"프로젝트 분석 중 오류 발생: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_detail)
        raise HTTPException(
            status_code=500,
            detail=f"프로젝트 분석 실패: {str(e)}"
        )

@router.get("/test/analyze/{task_id}")
async def get_analysis_result(
    task_id: str,
    project_analyzer: ProjectAnalyzer = Depends(get_project_analyzer)
):
    """
    분석 결과 조회 엔드포인트
    
    task_id를 사용하여 이전에 요청한 프로젝트 분석의 결과를 조회합니다.
    """
    try:
        task = project_analyzer.task_manager.get_task_info(task_id)
        return {
            "task_id": task_id,
            "status": task["status"],
            "message": task["message"],
            "result": task.get("result", None),
            "error": task.get("error", None)
        }
        
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail="해당 태스크를 찾을 수 없습니다."
        )
    except Exception as e:
        logger.error(f"결과 조회 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"결과 조회 실패: {str(e)}"
        )

@router.get("/test/analyze/{task_id}/stream")
async def get_analysis_status_stream(
    task_id: str,
    project_analyzer: ProjectAnalyzer = Depends(get_project_analyzer)
):
    """
    분석 상태 스트림 엔드포인트
    
    task_id에 대한 분석 상태를 Server-Sent Events(SSE) 형식으로 스트리밍합니다.
    """
    try:
        async def event_generator():
            async for event in project_analyzer.get_task_status_stream(task_id):
                yield event
                
        return event_generator()
        
    except Exception as e:
        logger.error(f"상태 스트림 생성 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"상태 스트림 생성 실패: {str(e)}"
        ) 