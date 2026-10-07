from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class Login(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class ResetPassword(BaseModel):
    token: str = Field(min_length=1, max_length=256)
    password: str = Field(min_length=12, max_length=128)


class EmailAddress(BaseModel):
    email: EmailStr


class VerifyEmail(BaseModel):
    token: str = Field(min_length=1, max_length=256)


class ChangePassword(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=12, max_length=128)


class Title(BaseModel):
    title: str = Field(min_length=1, max_length=100)


class Prompt(BaseModel):
    content: str = Field(min_length=1, max_length=12000)
    request_key: str = Field(min_length=8, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    model: str = "default"


class BudgetEdit(BaseModel):
    daily_requests: int = Field(ge=1, le=10000)
    daily_units: int = Field(ge=100, le=10000000)
    max_concurrent: int = Field(ge=1, le=4)
    max_output: int = Field(ge=64, le=4096)
    model_enabled: bool


class UserEdit(BaseModel):
    role: Literal["user", "admin"]
    active: bool
    approved: bool
    daily_requests: int | None = Field(default=None, ge=1, le=10000)
    daily_units: int | None = Field(default=None, ge=100, le=10000000)
    max_concurrent: int | None = Field(default=None, ge=1, le=4)


class MfaChallengeInput(BaseModel):
    challenge: str = Field(min_length=1, max_length=256)


class MfaVerify(MfaChallengeInput):
    code: str = Field(min_length=1, max_length=64)


class MfaReplace(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    code: str = Field(default="", max_length=64)


class MfaCode(BaseModel):
    code: str = Field(min_length=1, max_length=64)


class ModelView(BaseModel):
    id: str
    name: str
    provider: str
    enabled: bool


class BudgetView(BudgetEdit):
    role: Literal["user", "admin"]


class ContainerMetric(BaseModel):
    name: str
    cpu: str
    memory: str
    status: str


class HostSample(BaseModel):
    at: float
    cpu_percent: float
    memory_used: int = 0
    memory_total: int = 0
    disk_used: int = 0
    disk_total: int = 0
    containers: list[ContainerMetric]


class BackupMetric(BaseModel):
    status: Literal["ok", "stale", "missing"]
    created_at: float | None = None
    received_at: float | None = None


class BackupMetrics(BaseModel):
    local: BackupMetric
    off_host: BackupMetric


class HostMetrics(BaseModel):
    status: str = "ok"
    samples: list[HostSample] = Field(default_factory=list)
    cpu: list[int] = Field(default_factory=list)
    backups: BackupMetrics | None = None


class AdminTotals(BaseModel):
    users: int
    active_streams: int
    failed_runs: int
    requests: int
    reserved_units: int
    email_pending: int
    email_failed: int
    email_sent: int


class AuditView(BaseModel):
    action: str
    target: str
    at: float


class AdminOverview(BaseModel):
    totals: AdminTotals
    host: HostMetrics
    audit: list[AuditView]
