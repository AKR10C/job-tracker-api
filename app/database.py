import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

#DATABASE_URL = os.getenv("DATABASE_URL")         # use this when we want to deploy on internet   
DATABASE_URL = "mysql+pymysql://jobuser:Job%40123@127.0.0.1:3306/job_tracker"   #it is to run it on local sql server 


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
