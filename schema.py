from pydantic import BaseModel

class stocks_model(BaseModel):
    st_name : str

    class Config:
        orm_mode=True

class signup_model(BaseModel):
    email : str
    username : str
    password : str

    class Config:
        orm_mode=True

class login_model(BaseModel):
    username : str
    password : str

    class Config:
        orm_mode=True


class stock_model(BaseModel):
    symbol : str
    
    class Config:
        orm_mode=True