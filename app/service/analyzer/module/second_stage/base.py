from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Generic, TypeVar

TOut = TypeVar("TOut")


class InsufficientInputError(Exception):
    """블록 분석에 필요한 필드가 부족할 때 발생"""
    def __init__(self, block: str, fields: List[str]):
        self.block = block
        self.fields = fields
        super().__init__(f"[{block}] Missing fields: {fields}")


class BlockAnalyzer(ABC, Generic[TOut]):
    block_name: str

    @staticmethod
    @abstractmethod
    def required_fields(data: Dict[str, Any]) -> List[str]:
        """필수 입력 누락 필드 리스트 반환"""

    @abstractmethod
    async def analyze(self, data: Dict[str, Any]) -> TOut:
        """실제 분석 수행"""