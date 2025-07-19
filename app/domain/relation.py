from sqlmodel import Relationship


def setup_relations():
    from app.domain.deletion_log import DeletionLog
    from app.domain.user import User
    from app.domain.project import Project
    from app.domain.project_idea import ProjectIdea
    from app.domain.overview_analysis import OverviewAnalysis
    from app.domain.market_research import MarketResearch
    from app.domain.market_trend import MarketTrend
    from app.domain.revenue_benchmark import RevenueBenchmark
    from app.domain.subscription import Subscription
    from app.domain.term import Term
    from app.domain.user_agreement import UserAgreement

    User.subscriptions = Relationship(back_populates="user")
    User.agreements = Relationship(back_populates="user")
    User.projects = Relationship(back_populates="user")

    Project.user = Relationship(back_populates="projects")
    Project.idea = Relationship(back_populates="project")

    ProjectIdea.project = Relationship(back_populates="idea")
    ProjectIdea.analyses = Relationship(back_populates="idea")

    OverviewAnalysis.project = Relationship(back_populates="analysis")
    OverviewAnalysis.idea = Relationship(back_populates="analyses")

    MarketResearch.trends = Relationship(back_populates="market")
    MarketResearch.benchmarks = Relationship(back_populates="market")

    MarketTrend.industry = Relationship(back_populates="trends")

    RevenueBenchmark.industry = Relationship(back_populates="benchmarks")

    Subscription.user = Relationship(back_populates="subscriptions")

    Term.agreements = Relationship(back_populates="term")

    UserAgreement.user = Relationship(back_populates="agreements")
    UserAgreement.term = Relationship(back_populates="agreements")
