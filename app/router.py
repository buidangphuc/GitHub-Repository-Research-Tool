#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastapi import APIRouter

# from app.admin.api.router import v1 as admin_v1
from app.research.api.v1 import router as research_v1
# from app.task.api.router import v1 as task_v1

router = APIRouter()

router.include_router(research_v1)
# router.include_router(admin_v1)
# router.include_router(task_v1)
