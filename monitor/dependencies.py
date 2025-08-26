from models import db
from sqlalchemy.orm import sessionmaker



def init_session():
    """Initialize a new database session.

    Returns:
        _type_: _description_
    """
    Session = sessionmaker(bind=db)
    return Session()

