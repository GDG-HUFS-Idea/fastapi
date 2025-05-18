import enum

class TaskStatus(str, enum.Enum):
    """태스크 상태를 나타내는 enum"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed" 