from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.reflection import Inspector


Base = declarative_base()

class Metrics(Base):

    __tablename__ = "metrics_test"

    id = Column(String, primary_key=True)
    systime = Column(Float)
    usertime = Column(Float)
    elapsed = Column(String)
    cpu = Column(Float)
    max_resident_time = Column(Float)

    def __repr__(self):
        return "<Metrics(systime='%d', usertime='%d', elapsed='%s', cpu='%d', max_resident_time='%d'>" %(self.systime,
                self.usertime, self.elapsed, self.cpu, self.max_resident_time)


def db_connect(database):
    """performs database connection"""

    return create_engine(URL(**database))

def create_table(engine):

    #check if a table for metrics exists and create one if it doesn't.
    inspector = Inspector.from_engine(engine)
    tables = set(inspector.get_table_names())
    print(inspector.get_table_names())
    if 'metrics_test' not in tables:
        Base.metadata.create_all(engine)


def add_metrics(config, uuid, sys, user, elap, cpu_use, resident):

    DATABASE = {
        'drivername': 'postgres',
        'host' : 'pgreadwrite.osdc.io',
        'port' : '5432',
        'username': config['username'],
        'password' : config['password'],
        'database' : 'prod_bioinfo'
    }


    engine = db_connect(DATABASE)

    Session = sessionmaker()
    Session.configure(bind=engine)
    session = Session()

    create_table(engine)
    metrics_object = Metrics(id=uuid, systime=sys, usertime=user, elapsed=elap, cpu=cpu_use, max_resident_time=resident)

    session.add(metrics_object)
    session.commit()
    session.close()
