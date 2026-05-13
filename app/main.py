from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import auth, feed, posts, profile, reactions, search, subscriptions


app = FastAPI(title=settings.app_name, debug=settings.app_debug)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(auth.router)
app.include_router(feed.router)
app.include_router(profile.router)
app.include_router(posts.router)
app.include_router(reactions.router)
app.include_router(search.router)
app.include_router(subscriptions.router)


@app.get("/")
async def root():
    return RedirectResponse("/feed")
