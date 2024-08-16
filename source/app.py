from fastapi import FastAPI
from fastapi.responses import UJSONResponse
from starlette.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse
from starlette_admin import BaseAdmin, DropDown
from tortoise.contrib.fastapi import register_tortoise
from uvicorn import run
from admin import UserView, RankView, ActivityView, RewardsView, StatsView
from components.admin.auth import CustomAuthProvider
from config import TORTOISE_CONFIG, ADMIN_MW_SECRET_KEY
from db_models.api import User, Rank, Stats, Activity, Reward
from init import init
from routers import authentication, synchronization, mining, rewarding, leaderboard, tasks

# Используемые базы данных Redis
# db10 - Кеш fastapi_cache

app = FastAPI(default_response_class=UJSONResponse)

# Подключаем Tortoise ORM
register_tortoise(app=app,
                  config=TORTOISE_CONFIG,
                  generate_schemas=True,
                  add_exception_handlers=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["POST", "GET", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization"],
)

# Инициализируем все
app.add_event_handler("startup", init)

# Подключаем роутеры
app.include_router(authentication.router)
app.include_router(synchronization.router)
app.include_router(mining.router)
app.include_router(rewarding.router)
app.include_router(leaderboard.router)
app.include_router(tasks.router)


# Настраиваем админку
@app.get("/")
async def redirect_admin() -> RedirectResponse:
    return RedirectResponse(url="/docs")


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
    run("app:app", workers=8)
