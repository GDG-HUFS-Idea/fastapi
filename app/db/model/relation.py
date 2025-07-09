from sqlmodel import Relationship


def setup_relation():
    from app.db.model.deletion_log import DeletionLog
    from app.db.model.term import Term
    from app.db.model.term_agreement import TermAgreement
    from app.db.model.user import User

    User.term_agreements = Relationship(back_populates="user")

    Term.term_agreements = Relationship(back_populates="term")

    TermAgreement.user = Relationship(back_populates="term_agreements")
    TermAgreement.term = Relationship(back_populates="term_agreements")
