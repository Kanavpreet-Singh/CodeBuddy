import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import asyncpg

_pool: Optional[asyncpg.Pool] = None


async def init_pool() -> None:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(dsn=os.environ["DATABASE_URL"], min_size=1, max_size=10)


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def _pool_or_raise() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("DB pool not initialized")
    return _pool


def _now() -> datetime:
    # Prisma's DateTime maps to `timestamp without time zone`, so store naive UTC.
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _new_id() -> str:
    return uuid.uuid4().hex


async def create_app(user_id: str, prompt: str) -> str:
    app_id = _new_id()
    pool = _pool_or_raise()
    await pool.execute(
        'INSERT INTO "App" ("id","userId","prompt","status","updatedAt") '
        'VALUES ($1,$2,$3,$4::"AppStatus",$5)',
        app_id,
        user_id,
        prompt,
        "PLANNING",
        _now(),
    )
    return app_id


async def save_plan(
    app_id: str,
    name: str,
    description: str,
    techstack: str,
    features: list[str],
) -> None:
    pool = _pool_or_raise()
    await pool.execute(
        'UPDATE "App" SET "name"=$2,"description"=$3,"techstack"=$4,'
        '"features"=$5::jsonb,"status"=$6::"AppStatus","updatedAt"=$7 WHERE "id"=$1',
        app_id,
        name,
        description,
        techstack,
        json.dumps(features),
        "ARCHITECTING",
        _now(),
    )


async def save_task_plan(app_id: str, task_plan: dict) -> None:
    pool = _pool_or_raise()
    await pool.execute(
        'UPDATE "App" SET "taskPlan"=$2::jsonb,"status"=$3::"AppStatus","updatedAt"=$4 WHERE "id"=$1',
        app_id,
        json.dumps(task_plan),
        "CODING",
        _now(),
    )


async def finalize_app(app_id: str, storage_path: str, files: list[tuple[str, Optional[str], int]]) -> None:
    pool = _pool_or_raise()
    async with pool.acquire() as conn:
        async with conn.transaction():
            for path, purpose, size in files:
                await conn.execute(
                    'INSERT INTO "GeneratedFile" ("id","appId","path","purpose","sizeBytes","updatedAt") '
                    "VALUES ($1,$2,$3,$4,$5,$6) "
                    'ON CONFLICT ("appId","path") DO UPDATE SET '
                    '"purpose"=EXCLUDED."purpose","sizeBytes"=EXCLUDED."sizeBytes","updatedAt"=EXCLUDED."updatedAt"',
                    _new_id(),
                    app_id,
                    path,
                    purpose,
                    size,
                    _now(),
                )
            await conn.execute(
                'UPDATE "App" SET "storagePath"=$2,"status"=$3::"AppStatus","updatedAt"=$4 WHERE "id"=$1',
                app_id,
                storage_path,
                "DONE",
                _now(),
            )


async def fail_app(app_id: str, message: str) -> None:
    pool = _pool_or_raise()
    await pool.execute(
        'UPDATE "App" SET "status"=$2::"AppStatus","errorMessage"=$3,"updatedAt"=$4 WHERE "id"=$1',
        app_id,
        "ERROR",
        message,
        _now(),
    )


async def list_apps(user_id: str) -> list[dict]:
    pool = _pool_or_raise()
    rows = await pool.fetch(
        'SELECT "id","name","description","techstack","status","createdAt" '
        'FROM "App" WHERE "userId"=$1 ORDER BY "createdAt" DESC',
        user_id,
    )
    return [dict(r) for r in rows]


async def get_app(app_id: str, user_id: str) -> Optional[dict]:
    pool = _pool_or_raise()
    row = await pool.fetchrow(
        'SELECT "id","name","description","techstack","features","status","errorMessage",'
        '"storagePath","createdAt" FROM "App" WHERE "id"=$1 AND "userId"=$2',
        app_id,
        user_id,
    )
    return dict(row) if row else None


async def get_app_files(app_id: str) -> list[dict]:
    pool = _pool_or_raise()
    rows = await pool.fetch(
        'SELECT "path","purpose","sizeBytes" FROM "GeneratedFile" WHERE "appId"=$1 ORDER BY "path"',
        app_id,
    )
    return [dict(r) for r in rows]


async def create_sandbox_run(
    app_id: str,
    sandbox_id: str,
    preview_url: Optional[str],
    status: str,
    ttl_seconds: int,
) -> datetime:
    pool = _pool_or_raise()
    expires_at = _now() + timedelta(seconds=ttl_seconds)
    await pool.execute(
        'INSERT INTO "SandboxRun" ("id","appId","sandboxId","previewUrl","status","expiresAt") '
        "VALUES ($1,$2,$3,$4,$5,$6)",
        _new_id(),
        app_id,
        sandbox_id,
        preview_url,
        status,
        expires_at,
    )
    return expires_at


async def mark_sandbox_stopped(sandbox_id: str) -> None:
    pool = _pool_or_raise()
    await pool.execute(
        'UPDATE "SandboxRun" SET "status"=$2,"stoppedAt"=$3 WHERE "sandboxId"=$1',
        sandbox_id,
        "STOPPED",
        _now(),
    )
