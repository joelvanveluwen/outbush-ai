import os
from pathlib import Path
from typing import Optional

from fastapi import File, Form, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel

from gradio import Server

from outbush_ai.core import (
    ask_outbush,
    build_checklist,
    danger_cards,
    encyclopedia_search,
    first_aid_flow,
    health_status,
    identify_photo,
    weather_advice,
)
from outbush_ai.frontend import FRONTEND_HTML
from outbush_ai.vision import start_space_vision_warmup
from outbush_ai.weather import fetch_weather_pack


app = Server(
    title="Outbush AI",
    description="Offline-first bushwalking field assistant for Australian conditions.",
)
start_space_vision_warmup()


class ChatPayload(BaseModel):
    message: str
    region: str = "General Australia"


class TopicPayload(BaseModel):
    topic: str


class WeatherPayload(BaseModel):
    region: str = "General Australia"
    cloud_note: str = ""
    refresh_live: bool = False


class SearchPayload(BaseModel):
    query: str
    limit: int = 6


class WeatherPackPayload(BaseModel):
    region: str = "General Australia"
    refresh: bool = True


@app.get("/", response_class=HTMLResponse)
async def homepage() -> str:
    return FRONTEND_HTML


@app.get("/favicon.png")
async def favicon() -> FileResponse:
    return FileResponse(Path(__file__).with_name("Outbush_Favicon.png"))


@app.get("/assets/outbush-logo.png")
async def outbush_logo() -> FileResponse:
    return FileResponse(Path(__file__).with_name("Outbush_Logo.png"))


@app.get("/assets/outbush-field-photo.jpg")
async def outbush_field_photo() -> FileResponse:
    return FileResponse(Path(__file__).with_name("IMG_4103.jpg"))


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse(health_status())


@app.get("/api/health")
async def api_health() -> JSONResponse:
    return JSONResponse(health_status())


@app.post("/api/chat")
async def api_chat(payload: ChatPayload) -> JSONResponse:
    return JSONResponse(ask_outbush(payload.message, payload.region))


@app.post("/api/photo")
async def api_photo(
    image: Optional[UploadFile] = File(default=None),
    note: str = Form(default=""),
) -> JSONResponse:
    file_name = image.filename if image else ""
    content_type = image.content_type if image else ""
    image_bytes = await image.read() if image else None
    return JSONResponse(
        identify_photo(
            file_name=file_name,
            note=note,
            image_bytes=image_bytes,
            content_type=content_type or "",
        )
    )


@app.get("/api/dangers")
async def api_dangers() -> JSONResponse:
    return JSONResponse({"cards": danger_cards()})


@app.post("/api/firstaid")
async def api_firstaid(payload: TopicPayload) -> JSONResponse:
    return JSONResponse(first_aid_flow(payload.topic))


@app.get("/api/checklist")
async def api_checklist() -> JSONResponse:
    return JSONResponse(build_checklist())


@app.post("/api/encyclopedia")
async def api_encyclopedia(payload: SearchPayload) -> JSONResponse:
    return JSONResponse(encyclopedia_search(payload.query, payload.limit))


@app.post("/api/weather")
async def api_weather(payload: WeatherPayload) -> JSONResponse:
    return JSONResponse(weather_advice(payload.region, payload.cloud_note, payload.refresh_live))


@app.post("/api/weather-pack")
async def api_weather_pack(payload: WeatherPackPayload) -> JSONResponse:
    return JSONResponse(fetch_weather_pack(payload.region, payload.refresh))


@app.api(name="chat", concurrency_limit=1)
def gradio_chat(message: str, region: str = "General Australia") -> dict:
    return ask_outbush(message, region)


@app.api(name="photo_identify", concurrency_limit=1)
def gradio_photo_identify(file_name: str = "", note: str = "") -> dict:
    return identify_photo(file_name=file_name, note=note)


@app.api(name="first_aid", concurrency_limit=1)
def gradio_first_aid(topic: str) -> dict:
    return first_aid_flow(topic)


@app.api(name="checklist", concurrency_limit=1)
def gradio_checklist() -> dict:
    return build_checklist()


@app.api(name="encyclopedia", concurrency_limit=2)
def gradio_encyclopedia(query: str, limit: int = 6) -> dict:
    return encyclopedia_search(query, limit)


@app.api(name="weather", concurrency_limit=1)
def gradio_weather(region: str = "General Australia", cloud_note: str = "") -> dict:
    return weather_advice(region, cloud_note)


@app.api(name="health", concurrency_limit=4)
def gradio_health() -> dict:
    return health_status()


if __name__ == "__main__":
    host = os.getenv("OUTBUSH_HOST", "0.0.0.0")
    port = int(os.getenv("PORT", os.getenv("OUTBUSH_PORT", "7860")))
    favicon = Path(__file__).with_name("Outbush_Favicon.png")
    app.launch(
        server_name=host,
        server_port=port,
        show_error=True,
        favicon_path=str(favicon) if favicon.exists() else None,
    )
