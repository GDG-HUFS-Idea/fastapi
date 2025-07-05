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


class TaskStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class SubscriptionPlan(str, Enum):
    FREE = "free"
    PRO = "pro"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    ANALYZED = "analyzed"


class MarketScope(str, Enum):
    DOMESTIC = "domestic"
    GLOBAL = "global"


class Currency(str, Enum):
    KRW = "KRW"
    USD = "USD"


class RiskCategory(str, Enum):
    MARKET = "market"
    TECH = "tech"
    FINANCIAL = "financial"


class Impact(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
