from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import UJSONResponse
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette_admin import BaseAdmin, DropDown
from tortoise.contrib.fastapi import register_tortoise
from uvicorn import run
from admin.auth import CustomAuthProvider
from db_models.api import User, Rank, Stats, Activity, Reward
from routers import synchronization, mining, rewarding, leaderboard, tasks
from admin.views import UserView, RankView, ActivityView, RewardsView, StatsView

try:
    from config import TORTOISE_CONFIG, ADMIN_MW_SECRET_KEY, PSQL_CPUS
except ImportError:
    from services.api.config import TORTOISE_CONFIG, ADMIN_MW_SECRET_KEY, PSQL_CPUS

try:
    from init import init
except ImportError:
    from services.api.init import init


# Используемые базы данных Redis
# db9 - Для asgi_limit
# db10 - Кеш fastapi_cache

# Ставим самый быстрый декодер Ujson
app = FastAPI(title="2Eden API - Swagger UI", default_response_class=UJSONResponse)


# Подключаем Tortoise ORM
register_tortoise(app=app,
                  config=TORTOISE_CONFIG,
                  generate_schemas=True,
                  add_exception_handlers=True)

# @app.exception_handler(HTTPException)
# async def http_exception_handler(request: Request, exc: HTTPException):
#     return CustomJSONResponse(message=exc.detail,
#                               status_code=exc.status_code)


# Добавляем cors middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["POST", "GET", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Инициализируем все
app.add_event_handler("startup", init)

# Подключаем роутеры
app.include_router(synchronization.router, prefix="/api")
app.include_router(mining.router, prefix="/api")
app.include_router(rewarding.router, prefix="/api")
app.include_router(leaderboard.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")

# Настраиваем админку
admin = BaseAdmin(title="2Eden Admin",
                  auth_provider=CustomAuthProvider(),
                  middlewares=[Middleware(SessionMiddleware, secret_key=ADMIN_MW_SECRET_KEY)])

admin.add_view(RankView(Rank))
admin.add_view(DropDown("Пользователи",
                        icon="fa fa-user",
                        views=[UserView(User), ActivityView(Activity),
                               StatsView(Stats), RewardsView(Reward)]))

admin.mount_to(app)

if __name__ == "__main__":
    # workers = число потоков (1 процесс = 1 поток)
    run(app="app:app",
        interface="asgi3",
        workers=max(PSQL_CPUS, 1),
        lifespan="on",
        host="0.0.0.0",
        proxy_headers=True,
        forwarded_allow_ips="*")