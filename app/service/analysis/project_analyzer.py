import asyncio
import datetime
import logging
from typing import Dict, Any, AsyncGenerator
from starlette.concurrency import run_in_threadpool

from app.core.analysis.modules import reinitialize_modules
from app.service.analysis.report_generator import generate_report
from app.service.analysis.task_manager import TaskManager
from app.util.enum import TaskStatus
from app.core.analysis.validators import ReportValidator, ProjectOverviewValidator
from app.util.exception import ValidationException

logger = logging.getLogger(__name__)

class ProjectAnalyzer:
    def __init__(self):
        self.task_manager = TaskManager()

    async def analyze_project(self, data: Dict[str, Any]) -> str:
        """
        프로젝트 분석을 시작하고 task_id를 반환합니다.
        """
        try:
            # 데이터 검증
            if not self._validate_input_data(data):
                raise ValidationException("입력 데이터가 유효하지 않습니다.")

            # task_id 생성 및 초기화
            task_id = self.task_manager.create_task(data)
            logger.info(f"새 분석 작업 시작 (task_id: {task_id})")
            
            # 백그라운드에서 분석 실행
            asyncio.create_task(self._run_analysis_task(task_id, data))
            
            return task_id
            
        except Exception as e:
            logger.error(f"분석 작업 초기화 실패: {str(e)}")
            raise

    def _validate_input_data(self, data: Dict[str, Any]) -> bool:
        """입력 데이터 검증"""
        try:
            # 기본 형식 검증
            if not isinstance(data, dict):
                return False

            # problem 필드 검증
            problem = data.get('problem', {})
            if not isinstance(problem, dict):
                return False
            if not problem.get('identifiedIssues') or not problem.get('developmentMotivation'):
                return False
            if not isinstance(problem['identifiedIssues'], list) or not problem['identifiedIssues']:
                return False
            if not isinstance(problem['developmentMotivation'], str) or not problem['developmentMotivation'].strip():
                return False

            # solution 필드 검증
            solution = data.get('solution', {})
            if not isinstance(solution, dict):
                return False
            if not solution.get('coreElements') or not solution.get('methodology') or not solution.get('expectedOutcome'):
                return False
            if not isinstance(solution['coreElements'], list) or not solution['coreElements']:
                return False
            if not isinstance(solution['methodology'], str) or not solution['methodology'].strip():
                return False
            if not isinstance(solution['expectedOutcome'], str) or not solution['expectedOutcome'].strip():
                return False

            return True
        except Exception as e:
            logger.error(f"데이터 검증 중 오류 발생: {str(e)}")
            return False

    async def _run_analysis_task(self, task_id: str, data: Dict[str, Any]):
        """
        비동기로 분석 작업을 수행하고 결과를 저장합니다.
        """
        try:
            # 태스크 상태 업데이트
            self.task_manager.update_task(task_id, {
                'status': TaskStatus.PROCESSING,
                'progress': 0.05,
                'message': "분석 시스템 초기화 중... 입력 데이터 검증 및 분석 모듈 준비"
            })
            
            # 데이터가 이미 SparkLens 형식인지 확인하고 필요시 변환
            analysis_data = self._prepare_analysis_data(data)
            
            # 분석 모듈 초기화
            modules = await run_in_threadpool(reinitialize_modules)
            
            # 데이터 수집 단계
            results = await self._collect_analysis_data(task_id, analysis_data, modules)
            
            # 보고서 생성 단계
            report = await self._generate_analysis_report(task_id, results)
            
            # 분석 완료 및 결과 저장
            self.task_manager.complete_task(task_id, report)
            logger.info(f"분석 작업 완료 (task_id: {task_id})")
            
        except Exception as e:
            logger.error(f"분석 작업 실패 (task_id: {task_id}): {str(e)}")
            self.task_manager.fail_task(task_id, str(e))

    def _prepare_analysis_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """분석 데이터 준비"""
        if 'user_id' in data and 'problem' in data and 'solution' in data:
            logger.debug("전처리된 SparkLens 형식 데이터 사용")
            return data
        else:
            logger.debug("데이터를 분석 시스템 형식으로 변환")
            return self._convert_overview_to_analysis_format(data)

    def _convert_overview_to_analysis_format(self, overview_data: Dict) -> Dict:
        """오버뷰 요청 데이터를 분석 시스템 형식으로 변환"""
        if isinstance(overview_data.get('problem'), dict) and isinstance(overview_data.get('solution'), dict):
            return overview_data
        
        return {
            'problem': {
                'identifiedIssues': [overview_data.get('problem', '')],
                'developmentMotivation': overview_data.get('motivation', '')
            },
            'solution': {
                'coreElements': [overview_data.get('features', '')],
                'methodology': overview_data.get('method', ''),
                'expectedOutcome': overview_data.get('deliverable', '')
            }
        }

    async def _collect_analysis_data(self, task_id: str, analysis_data: Dict, modules: Dict) -> Dict:
        """분석 데이터 수집"""
        self.task_manager.update_task(task_id, {
            'progress': 0.1,
            'message': "외부 데이터 수집 시작... (산업 분류, 시장 분석, 유사 서비스 검색, 기회/한계점 분석)"
        })

        results = {
            'idea': analysis_data.get('idea', ''),
            'problem': analysis_data.get('problem', {}),
            'solution': analysis_data.get('solution', {}),
        }

        # 중간 진행 업데이트 함수
        async def update_collection_progress():
            progress_points = [0.15, 0.25, 0.35, 0.45]
            await asyncio.sleep(30)
            
            for progress in progress_points:
                if self.task_manager.is_task_processing(task_id):
                    self.task_manager.update_task(task_id, {'progress': progress})
                await asyncio.sleep(30)

        progress_task = asyncio.create_task(update_collection_progress())
        
        try:
            # 각 모듈의 올바른 메서드 호출
            tasks = [
                modules['classifier'].classify(results['idea']),
                modules['market'].analyze(results['idea'], results['problem'], results['solution']),
                modules['similar'].find(results['idea'], ' '.join(results['solution'].get('coreElements', []))),
                modules['opportunity'].find(results['idea'], results['problem'], results['solution']),
                modules['limitation'].analyze(results['idea'], results['problem'], results['solution']),
                modules['team'].analyze_team(results['idea'], results['problem'], results['solution'])  # analyze_team으로 수정
            ]
            
            # 모든 분석 작업을 병렬로 실행하고 예외 처리
            try:
                ksic, market, similar_services, opportunities, limitations, team = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 각 결과의 예외 처리
                results.update({
                    'ksic': ksic if not isinstance(ksic, Exception) else {"content": "산업 분류 분석 실패"},
                    'market': market if not isinstance(market, Exception) else {"content": "시장 분석 실패"},
                    'similar_services': similar_services if not isinstance(similar_services, Exception) else {"content": "유사 서비스 분석 실패"},
                    'opportunities': opportunities if not isinstance(opportunities, Exception) else {"content": "기회 분석 실패"},
                    'limitations': limitations if not isinstance(limitations, Exception) else {"content": "한계점 분석 실패"},
                    'team': team if not isinstance(team, Exception) else {"content": "팀 분석 실패"}
                })
                
            except Exception as e:
                logger.error(f"병렬 분석 실행 중 오류 발생: {str(e)}", exc_info=True)
                raise
            
            progress_task.cancel()
            return results
            
        except Exception as e:
            progress_task.cancel()
            logger.error(f"데이터 수집 중 오류 발생: {str(e)}", exc_info=True)
            raise

    async def _generate_analysis_report(self, task_id: str, results: Dict) -> Dict:
        """분석 보고서 생성"""
        self.task_manager.update_task(task_id, {
            'progress': 0.5,
            'message': "데이터 수집 완료. 보고서 작성을 시작합니다..."
        })
        
        report = await run_in_threadpool(lambda: generate_report(results, task_id))
        
        self.task_manager.update_task(task_id, {
            'progress': 0.9,
            'message': "보고서 최종 검증 중... 필수 항목 확인, 데이터 일관성 검사, 점수 산출 검증을 진행합니다"
        })
        
        await run_in_threadpool(ReportValidator.validate, report)
        return report

    def get_task_status(self, task_id: str) -> Dict:
        """태스크 상태 조회"""
        return self.task_manager.get_task_info(task_id)

    async def get_task_status_stream(self, task_id: str) -> AsyncGenerator[str, None]:
        """태스크 상태 스트림 생성"""
        async for event in self.task_manager.generate_status_events(task_id):
            yield event 