from enum import Enum


class OauthProvider(str, Enum):
    GOOGLE = "google"


class TermType(str, Enum):
    TERMS_OF_SERVICE = "terms_of_service"
    PRIVACY_POLICY = "privacy_policy"
    MARKETING = "marketing"


class UserRole(str, Enum):
    GENERAL = "general"
    ADMIN = "admin"


class PlanType(str, Enum):
    FREE = "free"
    PRO = "pro"


class TaskStatus(str, Enum):
    """태스크 상태를 나타내는 enum"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
