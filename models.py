from sqlalchemy import Column,Integer,String,Numeric,Date,ForeignKeyConstraint,PrimaryKeyConstraint
from sqlalchemy.orm import relationship

from database import Base

class stock_class(Base):
    __tablename__ ='stock_table'

    sid = Column(Integer,index=True,primary_key=True,autoincrement=True)
    name = Column(String(30),index=True,unique=True)
    symbol = Column(String(30),index=True,primary_key=True)

class ohlcv_class(Base):
    __tablename__ ='ohlcv_table'
    symbol = Column(String(30),index=True,primary_key=True)
    date =Column(Date,index=True,primary_key=True)
    open = Column(Numeric(8,2))
    high = Column(Numeric(8,2))
    low = Column(Numeric(8,2))                                  
    close = Column(Numeric(8,2))
    vol =Column(Numeric(20,2))
    ForeignKeyConstraint(['symbol'],['stock_table.symbol'])

class extrainfo_class(Base):
    __tablename__='extrainfo_table'

    symbol = Column(String(30),index=True,primary_key=True)
    secvar=Column(Numeric(10,2))
    varmargin=Column(Numeric(10,2))
    high52=Column(Numeric(10,2))
    low52=Column(Numeric(10,2))
    change1=Column(Numeric(10,2))
    change2=Column(Numeric(10,2))
    amr=Column(Numeric(10,2))
    ForeignKeyConstraint(['symbol'],['stock_table.symbol'])  


class user_class(Base):
    __tablename__ ='user_table'

    uid = Column(Integer, primary_key=True,index=True,autoincrement=True)
    uname = Column(String(50),primary_key=True,unique=True,index=True)
    uemail = Column(String(50),unique=True,index=True)
    upassword = Column(String(50),index=True)

class watchlist_class(Base):
    __tablename__ ='watchlist_table'
    uname = Column(String(50), index=True,primary_key=True)
    symbol = Column(String(30),index=True,primary_key=True)
    ForeignKeyConstraint(
        ['symbol','uname'],['stock_table.symbol','user_table.uname'])
    
