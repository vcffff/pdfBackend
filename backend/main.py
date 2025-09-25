import platform
from fastapi import FastAPI, Form, UploadFile, File, Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from jinja2 import Environment, FileSystemLoader
from uuid import uuid4
from base64 import b64encode
import pdfkit
import json
import os
import asyncpg

system = platform.system()
print("Running on:", system)
from dotenv import load_dotenv

load_dotenv()
if platform.system() == "Windows":
    PDFKIT_CONFIG = pdfkit.configuration(
        wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    )
else:
   PDFKIT_CONFIG = pdfkit.configuration(
        wkhtmltopdf="/usr/bin/wkhtmltopdf"
    )

SQLALCHEMY_DATABASE_URL=os.getenv('SQL_ALCHEMY_URL') 


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

env = Environment(loader=FileSystemLoader("templates"))

PDFKIT_CONFIG = pdfkit.configuration(
    wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
)

@app.post("/generate-pdf")
async def generate_pdf(data: str = Form(...), profile_image: UploadFile = File(None)):
    parsed = json.loads(data)

    name = parsed.get("name", "No Name")
    title = parsed.get("title", "No Title")
    summary = parsed.get("summary", "")
    skills = parsed.get("skills", [])
    projects = parsed.get("projects", [])

    profile_image_b64 = None
    if profile_image:
        image_bytes = await profile_image.read()
        profile_image_b64 = b64encode(image_bytes).decode("utf-8")

    template = env.get_template("resume_template.html")
    html_content = template.render(
        name=name,
        title=title,
        summary=summary,
        skills=skills,
        projects=projects,
        profile_image=profile_image_b64,
    )

    os.makedirs("resumes", exist_ok=True)
    filename = f"resumes/{uuid4().hex}.pdf"
    pdfkit.from_string(html_content, filename, configuration=PDFKIT_CONFIG)

    return FileResponse(path=filename, media_type="application/pdf", filename="resume.pdf")


@app.get("/tasks")
async def get_tasks(
    vacancy: str = Query(...),
    level: str = Query(None)
):
    conn = await asyncpg.connect(SQLALCHEMY_DATABASE_URL,server_settings={"client_encoding": "UTF8"})
    if level:
        rows = await conn.fetch(
            "SELECT id, title, link, type, vacancy, level, task FROM resources WHERE vacancy = $1 AND level = $2",
            vacancy, level
        )
    else:
        rows = await conn.fetch(
            "SELECT id, title, link, type, vacancy, level, task FROM resources WHERE vacancy = $1",
            vacancy
        )
    await conn.close()
    return [dict(r) for r in rows]
