from typing import Optional
from fastapi import FastAPI,Request,Depends,Response,status
from sqlalchemy import and_
from sqlalchemy.orm import Session
from database import SessionLocal,engine,Base
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import schema as sch
import models as mod
import yfinance as yf
import datetime as dt
import pandas as pd
from patterns import candlestick_patterns
import talib
import mplfinance as mpf
from nsetools import Nse
import json

app = FastAPI()

app.mount("/static",StaticFiles(directory="static"),name="static")
templates =Jinja2Templates(directory='templates')

Base.metadata.create_all(bind=engine)

def get_db():
    try:
        db=SessionLocal()
        yield db
    finally:
        db.close()

def addStockPrice(s):
    price_data=yf.download(s,(dt.datetime.today()-dt.timedelta(days=20)).strftime("%Y-%m-%d"),(dt.datetime.today()-dt.timedelta(days=2)).strftime("%Y-%m-%d"))
    price_data['Date']=price_data.index

    d=price_data['Date'].to_list()
    date=[]
    for i in d:
        dt_obj=i.to_pydatetime()
        date.append(dt_obj.strftime("%Y-%m-%d"))
    o=price_data['Open'].to_list()
    h=price_data['High'].to_list()
    l=price_data['Low'].to_list()
    c=price_data['Close'].to_list()
    v=price_data['Volume'].to_list()
    l1=[(str(s),date[j],o[j],h[j],l[j],c[j],v[j]) for j in range(0,len(date))]
    return l1

def addextrainfo(stock):
    nse=Nse()
    try: 
        q=nse.get_quote(stock)
        return(stock+".NS",q['securityVar'],q['varMargin'],q['high52'],q['low52'],float(q['pChange']),float(q['change']),q['applicableMargin'])
    except Exception as e:
        print(stock," details not found")
    

def filltable():
    db=SessionLocal()
    tickers = pd.read_html('https://ournifty.com/stock-list-in-nse-fo-futures-and-options.html#:~:text=NSE%20F%26O%20Stock%20List%3A%20%20%20%20SL,%20%201000%20%2052%20more%20rows%20')[0]
    n=tickers['F&O STOCKS NAME'].to_list()
    s=tickers['SYMBOL'].to_list()
    s=[i+".NS" for i in s]

    l=[(n[i],s[i]) for i in range(0,len(n))]
    d=[dict(name=t[0],symbol=t[1]) for t in l]
    if(db.query(mod.stock_class).first() == None):
        db.bulk_insert_mappings(mod.stock_class,d)
        db.commit()
    if(db.query(mod.ohlcv_class).first() == None):
        dict2=[]
        for i in s:
            l1=addStockPrice(i)
            dict1=[dict(symbol=list1[0],date=list1[1],open=float(list1[2]),high=float(list1[3]),low=float(list1[4]),close=float(list1[5]),vol=int(list1[6])) for list1 in l1]
            for j in dict1:
                dict2.append(j)

        db.bulk_insert_mappings(mod.ohlcv_class,dict2)
        db.commit()
    
    if(db.query(mod.extrainfo_class).first() == None):
        l3=[]
        for i in s:
            i=i.split('.')[0]
            l2=addextrainfo(i)
            if l2 is not None:
                l3.append(l2)
        print(l3)
        dict3=[dict(symbol=list2[0],secvar=list2[1],varmargin=list2[2],high52=list2[3],low52=list2[4],change1=list2[5],change2=list2[6],amr=list2[7]) for list2 in l3]
        
        db.bulk_insert_mappings(mod.extrainfo_class,dict3)
        db.commit()

    return {'message':"successfully added"}

@app.get('/')
def index(request: Request):
    return templates.TemplateResponse('home.html',{"request":request})

@app.get('/login')
def base(request: Request):
    return templates.TemplateResponse("login.html",{"request":request})

@app.get('/signup')
def base(request: Request):
    return templates.TemplateResponse("signup.html",{"request":request})

@app.get('/market')
async def base(request: Request,db:Session=Depends(get_db)):
    print("hello world")
    filltable()
    st=db.query(mod.ohlcv_class).filter(mod.ohlcv_class.date==((dt.datetime.today()-dt.timedelta(days=3)).strftime("%Y-%m-%d")))
    print(st)
    return templates.TemplateResponse("market.html",{"request":request,
    "stocks":st})

@app.post('/')
def displaystockdetails(stock_req:sch.stocks_model,db:Session=Depends(get_db)):
    st=db.query(mod.ohlcv_class).filter(
        and_(
            mod.ohlcv_class.symbol==stock_req.st_name.upper(),
            mod.ohlcv_class.date==((dt.datetime.today()-dt.timedelta(days=2)).strftime("%Y-%m-%d"))
            )
        ).first()
    print(st)
    return {"symbol":st.symbol,"date":st.date}

@app.post('/signup')
async def signingup(response:Response,user_req: sch.signup_model,db:Session=Depends(get_db)):
    if (db.query(mod.user_class).filter(mod.user_class.uname==user_req.username).first())==None:
        user = mod.user_class()
        user.uname = user_req.username
        user.uemail = user_req.email
        user.upassword = user_req.password

        db.add(user)
        db.commit()
    else:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {'detail': 'User already exists'}

    return {"code":"success",
            "message":"new user added"}
        
@app.post('/login')
async def loggingin(response:Response,user_req:sch.login_model,db:Session=Depends(get_db)):
    user = db.query(mod.user_class).filter(mod.user_class.uname==user_req.username).first()
    print(user.uname," ",user.upassword)
    if(user.upassword != user_req.password):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {'detail': 'User does not exist'}
    return {"message": "login successful"}

def fetch_stock_data(symbol):
    db=SessionLocal()

    stock=db.query(mod.ohlcv_class).filter(
        and_(
            mod.ohlcv_class.symbol==symbol,
            mod.ohlcv_class.date==((dt.datetime.today()-dt.timedelta(days=2)).strftime("%Y-%m-%d"))
            )
        ).first()
    print(stock)
    return {"open":float(stock.open),"high":float(stock.high),"low":float(stock.low),"close":float(stock.close),"vol":float(stock.vol)}

@app.get('/login/watchlist/')
async def getwatchlist(request:Request,name:str):
    sql_query = pd.read_sql_query('''
                                SELECT symbol FROM watchlist_table where uname='{}' '''.format(name),engine)
    stocksym=pd.DataFrame(sql_query,columns=['symbol'])
    stockdata={}
    for i in stocksym['symbol']:
        print(i)
        j=fetch_stock_data(i)
        stockdata[i]=j

    return templates.TemplateResponse("watchlist.html",{"request":request,"user":json.dumps(name),"stocks":stockdata})

@app.post('/login/watchlist/')
async def getstocks(stock_req:sch.stock_model,name:str,db:Session=Depends(get_db)):
    sym=mod.watchlist_class()
    sym.uname=name
    sym.symbol=stock_req.symbol

    db.add(sym)
    db.commit()

    return {'code':"success","message":"added to watchlist"}

@app.delete("/login/watchlist/")
def deletestock(stock_del:sch.stock_model,name:str,db:Session=Depends(get_db)):
    st=db.query(mod.watchlist_class).filter(and_(mod.watchlist_class.uname==name,
                                                mod.watchlist_class.symbol==stock_del.symbol)).first()
    db.delete(st)
    db.commit()
    return {"message":"deleted","user":json.dumps(name)}

@app.get('/market/{name}')
async def getextradetails(request:Request,name:str,db:Session=Depends(get_db)):
    st1=db.query(mod.extrainfo_class).filter(mod.extrainfo_class.symbol==name).first()
    st2=db.query(mod.stock_class).filter(mod.stock_class.symbol==name).first()
    st3=db.query(mod.ohlcv_class).filter(
        and_(
            mod.ohlcv_class.symbol==name,
            mod.ohlcv_class.date==((dt.datetime.today()-dt.timedelta(days=1)).strftime("%Y-%m-%d"))
            )
        ).first()
    st2.symbol=st2.symbol.split(".")[0]
    return templates.TemplateResponse("individual.html",{"request":request,"stock1":st1, "stock2":st2, "stock3":st3})


def getstockname():
    sql_query=pd.read_sql_query('''
                                SELECT symbol,name FROM stock_table''',engine)
    stocksym=pd.DataFrame(sql_query,columns=['symbol','name'])
       
    return stocksym

def getgraph(df,i):
    filename = '/media/nikitha/Data/DBMS project/static/{}.png'.format(i)
    df['ema25']=talib.EMA(df['close'],25)
    df['sma25']=talib.SMA(df['close'],25)
    sma=mpf.make_addplot(df['sma25'],color='lime',width=1.25)
    ema=mpf.make_addplot(df['ema25'],color='black',width=1.25)
    mpf.plot(df,type="candle",style="yahoo",addplot=[sma,ema],mav=(10,20),figratio=(10,6),savefig=filename)

@app.get('/screener/')
async def getscreener(request:Request,pattern:Optional[str]=None):
    stocks={}
    stock_symbol=getstockname()
    for i in stock_symbol['symbol']:
        b=i.split('.')
        a=b[0]
        stocks[a]={'company':stock_symbol.loc[stock_symbol['symbol']==i,'name'].item()}
    if pattern:
         for i in stock_symbol['symbol']:
            sql_query= pd.read_sql_query('''SELECT date,open,high,low,close from ohlcv_table where symbol = '{}' '''.format(i),engine)
            df=pd.DataFrame(sql_query,columns = ['date','open','high','low','close'])
            df.index=pd.to_datetime(df['date'])
            b=i.split('.')
            a=b[0]
            symbol = a
            pattern_function = getattr(talib, pattern)
            
            try:
                results = pattern_function(df['open'], df['high'], df['low'], df['close'])
                last = results.tail(1).values[0]
                if not(df.empty):
                    getgraph(df,a)

                if last > 0:
                    stocks[symbol][pattern] = 'bullish'
                elif last < 0:
                    stocks[symbol][pattern] = 'bearish'
                else:
                    stocks[symbol][pattern] = None

            except Exception as e:
                print('failed on filename: ',i)
           
                
    return templates.TemplateResponse("screener.html",{"request":request,"candlestick_patterns":candlestick_patterns,"stocks":stocks,"pattern":pattern})





    






    