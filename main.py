from fastapi import FastAPI
from routers import news,user
from fastapi.middleware.cors import CORSMiddleware

from utils.exception_handlers import register_exception_handlers

app=FastAPI()

#注册异常处理器
register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],#允许的源，默认为*
    allow_credentials=True,#允许携带cookie
    allow_methods=["*"],#允许的请求方法
    allow_headers=["*"]#允许的请求头
)
#挂载路由
app.include_router(news.router)
app.include_router(user.router )

@app.get("/")
async def root():
    return {"msg":"hello world"}

