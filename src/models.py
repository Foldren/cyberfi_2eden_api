from datetime import datetime, timedelta
from uuid import uuid4
from pytz import timezone
from tortoise import Model, Tortoise
from tortoise.contrib.pydantic import pydantic_model_creator, pydantic_queryset_creator
from tortoise.fields import BigIntField, DateField, CharEnumField, CharField, DatetimeField, \
    OnDelete, ForeignKeyField, OneToOneField, OneToOneRelation, ReverseRelation, FloatField, BooleanField
from tortoise_vector.field import VectorField
from components.enums import RankName, RewardTypeName, VisibilityType, ConditionType, QuestionStatus


class Rank(Model):  # В системе изначально создаются все 10 рангов
    id = BigIntField(pk=True)
    users: ReverseRelation["User"]
    league = BigIntField()
    name = CharEnumField(enum_type=RankName, default=RankName.ACOLYTE, description='Ранг')
    press_force = FloatField()
    max_energy = FloatField()
    energy_per_sec = FloatField()
    price = BigIntField()

    def __str__(self):
        return self.id


class User(Model):
    id = BigIntField(pk=True)  # = chat_id в телеграм
    rank = ForeignKeyField(model_name="models.Rank", on_delete=OnDelete.CASCADE, related_name="users", default=1)
    referrer = ForeignKeyField(model_name="models.User", on_delete=OnDelete.CASCADE, related_name="leads", null=True)
    leads: ReverseRelation["User"]
    stats: OneToOneRelation["Stats"]
    activity: OneToOneRelation["Activity"]
    rewards: ReverseRelation["Reward"]
    questions: OneToOneRelation["Question"]
    leader_place: OneToOneRelation["Leader"]
    country = CharField(max_length=50)  # -
    referral_code = CharField(max_length=40, default=uuid4, unique=True)

    def __str__(self):
        return self.id


class Activity(Model):
    id = BigIntField(pk=True)
    user = OneToOneField(model_name="models.User", on_delete=OnDelete.CASCADE, related_name="activity")
    reg_date = DateField(default=datetime.now())  # -
    last_login_date = DateField(default=datetime.now())
    last_daily_reward = DateField(default=(datetime.now(tz=timezone("Europe/Moscow")) - timedelta(hours=35)))
    last_sync_energy = DatetimeField(default=(datetime.now(tz=timezone("Europe/Moscow"))))
    next_inspiration = DatetimeField(default=(datetime.now(tz=timezone("Europe/Moscow")) - timedelta(days=1)))
    next_mining = DatetimeField(default=(datetime.now(tz=timezone("Europe/Moscow")) - timedelta(days=1)))
    is_active_mining = BooleanField(default=False)
    active_days = BigIntField(default=0)


class Stats(Model):
    id = BigIntField(pk=True)
    user = OneToOneField(model_name="models.User", on_delete=OnDelete.CASCADE, related_name="stats")
    coins = BigIntField(default=1000)
    energy = FloatField(default=2000)
    earned_week_coins = BigIntField(default=0)
    invited_friends = BigIntField(default=0)
    inspirations = BigIntField(default=0)
    replenishments = BigIntField(default=0)


class Reward(Model):
    id = BigIntField(pk=True)
    user = ForeignKeyField(model_name="models.User", on_delete=OnDelete.CASCADE, related_name="rewards")
    type_name = CharEnumField(enum_type=RewardTypeName, default=RewardTypeName.REFERRAL, description='Награда')
    amount = BigIntField(default=0)
    inspirations = BigIntField(default=0)
    replenishments = BigIntField(default=0)


class Leader(Model):
    place = BigIntField(pk=True)
    user = OneToOneField(model_name="models.User", on_delete=OnDelete.CASCADE, related_name="leader_place")
    earned_week_coins = BigIntField(default=0)


class Question(Model):
    id = BigIntField(pk=True)
    creator = ForeignKeyField('models.User', on_delete=OnDelete.CASCADE, related_name='questions')
    date_sent = DateField(auto_now_add=True)
    text = CharField(max_length=1000)
    answer = CharField(max_length=1000)
    embedding = VectorField(vector_size=384)
    secret = BooleanField(default=0)
    status = CharEnumField(enum_type=QuestionStatus, default=QuestionStatus.IN_PROGRESS, description='Статус')


# ------ Условия выполнения задач ------
class Condition(Model):
    id = BigIntField(pk=True)
    type = CharEnumField(enum_type=ConditionType, max_length=50)


class TgChannelCondition(Model):
    id = BigIntField(pk=True)
    condition = OneToOneField('models.Condition', related_name='tg_channel_condition')
    channel_id = CharField(max_length=100)  # ID телеграмм канала для подписки


class VisitLinkCondition(Model):
    id = BigIntField(pk=True)
    condition = OneToOneField('models.Condition', related_name='visit_link_condition')
    url = CharField(max_length=200)  # URL для посещения


# ------ Конец условий выполнения задач ------

# ------ Условия видимости задач ------
class Visibility(Model):
    id = BigIntField(pk=True)
    type = CharEnumField(enum_type=VisibilityType, max_length=50)


class AllwaysVisibility(Model):
    id = BigIntField(pk=True)
    visibility = OneToOneField('models.Visibility', related_name='allways_visibility')


class RankVisibility(Model):
    id = BigIntField(pk=True)
    visibility = OneToOneField('models.Visibility', related_name='rank_visibility')
    rank = ForeignKeyField('models.Rank', on_delete=OnDelete.CASCADE, related_name='rank_visibilities')


# ------ Конец условий видимости задач ------

class InstantReward(Model):
    id = BigIntField(pk=True)
    tokens = BigIntField(default=0)
    inspirations = BigIntField(default=0)
    replenishments = BigIntField(default=0)


# Задачи приложения
class Task(Model):
    id = BigIntField(pk=True)
    description = CharField(max_length=200)  # Название задачи
    reward = OneToOneField('models.InstantReward', related_name='tasks')
    condition = OneToOneField('models.Condition', related_name='tasks')  # Условие выполнения
    visibility = OneToOneField('models.Visibility', related_name='tasks')  # Условие видимости


# Задача, которую берет пользователь
class UserTask(Model):
    id = BigIntField(pk=True)
    user = ForeignKeyField('models.User', on_delete=OnDelete.CASCADE, related_name='user_tasks')  # ID пользователя
    task = ForeignKeyField('models.Task', on_delete=OnDelete.CASCADE, related_name='user_tasks')  # Связь с задачей
    create_time = DatetimeField(auto_now_add=True)  # Время создания
    completed_time = DatetimeField(null=True)  # Время выполнения (может быть пустым)

    @property
    def is_completed(self):  # todo: не задействованный метод
        return self.completed_time is not None


Tortoise.init_models(["models"], "api")
User_Pydantic = pydantic_model_creator(User, name="User")