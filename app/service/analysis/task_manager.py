import asyncio
import datetime
import json
import uuid
from typing import Dict, Any, AsyncGenerator

from app.util.task_status import TaskStatus

class TaskManager:
    def __init__(self):
        self._tasks: Dict[str, Dict] = {}

    def create_task(self, data: Dict[str, Any]) -> str:
        """새로운 태스크를 생성하고 task_id를 반환합니다."""
        task_id = str(uuid.uuid4())
        self._tasks[task_id] = {
            'status': TaskStatus.PENDING,
            'progress': 0,
            'message': '분석 대기 중...',
            'start_time': datetime.datetime.now(),
            'data': data
        }
        return task_id

    def update_task(self, task_id: str, updates: Dict[str, Any]):
        """태스크 정보를 업데이트합니다."""
        if task_id not in self._tasks:
            raise KeyError(f"Task not found: {task_id}")
        
        self._tasks[task_id].update(updates)

    def complete_task(self, task_id: str, result: Dict[str, Any]):
        """태스크를 완료 상태로 변경하고 결과를 저장합니다."""
        self.update_task(task_id, {
            'status': TaskStatus.COMPLETED,
            'progress': 1.0,
            'message': "분석 완료",
            'result': result
        })

    def fail_task(self, task_id: str, error: str):
        """태스크를 실패 상태로 변경하고 에러를 저장합니다."""
        self.update_task(task_id, {
            'status': TaskStatus.FAILED,
            'message': f"분석 실패: {error}",
            'error': error
        })

    def get_task_info(self, task_id: str) -> Dict[str, Any]:
        """태스크 정보를 조회합니다."""
        if task_id not in self._tasks:
            raise KeyError(f"Task not found: {task_id}")
        return self._tasks[task_id].copy()

    def is_task_processing(self, task_id: str) -> bool:
        """태스크가 처리 중인지 확인합니다."""
        if task_id not in self._tasks:
            return False
        return self._tasks[task_id]['status'] == TaskStatus.PROCESSING

    async def generate_status_events(self, task_id: str) -> AsyncGenerator[str, None]:
        """태스크 상태를 SSE 형식으로 생성하는 제너레이터 함수"""
        if task_id not in self._tasks:
            yield f"data: {json.dumps({'error': '존재하지 않는 작업 ID'})}\n\n"
            return

        try:
            # 초기 상태 전송
            task_info = self._tasks[task_id].copy()
            response_data = self._create_status_response(task_info)
            yield f"data: {json.dumps(response_data, ensure_ascii=False)}\n\n"

            # 작업이 완료 또는 실패 상태가 아니면 계속 업데이트 전송
            if task_info['status'] not in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                previous_progress = task_info.get('progress', 0)
                previous_message = task_info.get('message', '')

                while True:
                    try:
                        await asyncio.sleep(5)  # 5초마다 업데이트
                        
                        if task_id not in self._tasks:
                            yield f"data: {json.dumps({'error': '작업이 삭제되었습니다'})}\n\n"
                            return
                        
                        current_info = self._tasks[task_id].copy()
                        
                        # 완료 또는 실패 시 즉시 업데이트
                        if current_info['status'] in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                            current_response = self._create_status_response(current_info)
                            yield f"data: {json.dumps(current_response, ensure_ascii=False)}\n\n"
                            return

                        # 진행률이 5% 이상 변경되었거나, 메시지가 변경된 경우에만 업데이트
                        current_progress = current_info.get('progress', 0)
                        current_message = current_info.get('message', '')
                        
                        progress_change_significant = abs(current_progress - previous_progress) >= 0.05
                        message_changed = current_message != previous_message
                        
                        if progress_change_significant or message_changed:
                            current_response = self._create_status_response(current_info)
                            yield f"data: {json.dumps(current_response, ensure_ascii=False)}\n\n"
                            
                            previous_progress = current_progress
                            previous_message = current_message

                    except asyncio.CancelledError:
                        break
                    except Exception as e:
                        logger.error(f"상태 스트림 생성 중 오류 발생: {str(e)}")
                        yield f"data: {json.dumps({'error': str(e)})}\n\n"
                        break

        except Exception as e:
            logger.error(f"상태 스트림 초기화 중 오류 발생: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    def _create_status_response(self, task_info: Dict[str, Any]) -> Dict[str, Any]:
        """태스크 상태 응답 데이터를 생성합니다."""
        response_data = {
            "is_complete": task_info['status'] in [TaskStatus.COMPLETED, TaskStatus.FAILED]
        }
        
        if 'progress' in task_info:
            response_data["progress"] = task_info['progress']
        
        if 'message' in task_info:
            response_data["message"] = task_info['message']
        
        if task_info['status'] == TaskStatus.COMPLETED and 'result' in task_info:
            response_data["result"] = task_info['result']
        
        return response_data 