from models import db
from sqlalchemy.orm import sessionmaker



def init_session():
    """_summary_

    Yields:
        _type_: _description_
    """
    Session = sessionmaker(bind=db)
    return Session()


