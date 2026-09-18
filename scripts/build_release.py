"""Build the single HACS installation archive after release readiness passes."""

from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).parents[1]
SOURCE = ROOT / "custom_components" / "github_insights"
DIST = ROOT / "dist"
STAGING = DIST / "github_insights"
FRONTEND_BUILD = ROOT / "frontend" / "build" / "github-insights-cards.js"

if not FRONTEND_BUILD.is_file():
    raise SystemExit("Frontend production bundle is missing.")

if DIST.exists():
    shutil.rmtree(DIST)
shutil.copytree(SOURCE, STAGING)
frontend_target = STAGING / "frontend"
frontend_target.mkdir(exist_ok=True)
shutil.copy2(FRONTEND_BUILD, frontend_target / FRONTEND_BUILD.name)
shutil.make_archive(str(DIST / "github_insights"), "zip", DIST, "github_insights")
