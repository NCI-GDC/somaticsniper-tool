from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy import exc
from sqlalchemy.dialects.postgresql import ARRAY

Base = declarative_base()

class ToolTypeMixin(object):

    id = Column(Integer, primary_key=True)
    #case_id = Column(String)
    #tool = Column(String)
    files = Column(ARRAY(String))
    systime = Column(Float)
    usertime = Column(Float)
    elapsed = Column(String)
    cpu = Column(Float)
    max_resident_time = Column(Float)

    def __repr__(self):
        return "<ToolTypeMixin(systime='%d', usertime='%d', elapsed='%s', cpu='%d', max_resident_time='%d'>" %(self.systime,
                self.usertime, self.elapsed, self.cpu, self.max_resident_time)

class SomaticSniper(ToolTypeMixin, Base):

    __tablename__ = 'somaticsniper'

def db_connect(database):
    """performs database connection"""

    return create_engine(URL(**database))

def create_table(engine, tool):
    """ checks if a table for metrics exists and create one if it doesn't """

    inspector = Inspector.from_engine(engine)
    tables = set(inspector.get_table_names())
    print(inspector.get_table_names())
    if tool.__tablename__ not in tables:
        Base.metadata.create_all(engine)


def add_metrics(config, tool, uuid, sys, user, elap, cpu_use, resident, logger):
    """ add provided metrics to database """

    if 'username' not in config:
        raise Exception("username for logging into the database not found")
    if 'password' not in config:
        raise Exception("password for logging into the database not found")

    DATABASE = {
        'drivername': 'postgres',
        'host' : 'pgreadwrite.osdc.io',
        'port' : '5432',
        'username': config['username'],
        'password' : config['password'],
        'database' : 'prod_bioinfo'
    }


    print uuid
    engine = db_connect(DATABASE)

    Session = sessionmaker()
    Session.configure(bind=engine)
    session = Session()

    if tool=='somaticsniper':
        metrics = SomaticSniper(files=[uuid], systime=sys, usertime=user, elapsed=elap, cpu=cpu_use, max_resident_time=resident)

    create_table(engine, metrics)

    try:
        session.add(metrics)
        session.commit()
    except exc.IntegrityError:
        session.rollback()
        raise Exception("An entry for universal id: %s for tool %s already present." %(metrics.id, tool))
    else:
        logger.info("Added entry for universal id: %s in table %s." %(metrics.id, metrics.__tablename__))

    session.close()
