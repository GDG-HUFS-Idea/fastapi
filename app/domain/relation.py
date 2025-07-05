from sqlmodel import Relationship


def setup_relations():
    from app.domain.user import User
    from app.domain.subscription import Subscription
    from app.domain.term import Term
    from app.domain.user_agreement import UserAgreement

    User.subscriptions = Relationship(back_populates="user")
    User.agreements = Relationship(back_populates="user")
    User.projects = Relationship(back_populates="user")

    Subscription.user = Relationship(back_populates="subscriptions")

    Term.agreements = Relationship(back_populates="term")

    UserAgreement.user = Relationship(back_populates="agreements")
    UserAgreement.term = Relationship(back_populates="agreements")
