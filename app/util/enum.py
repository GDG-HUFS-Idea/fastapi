from enum import Enum


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
