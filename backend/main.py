from fastapi import FastAPI, Form, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from jinja2 import Environment, FileSystemLoader
from uuid import uuid4
from base64 import b64encode
import pdfkit
import json
import os

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
    """
    Принимает JSON (строкой в поле form-data 'data') + опционально фото профиля.
    Генерирует PDF-резюме.
    """
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

    # Сохраняем PDF
    os.makedirs("resumes", exist_ok=True)
    filename = f"resumes/{uuid4().hex}.pdf"
    pdfkit.from_string(html_content, filename, configuration=PDFKIT_CONFIG)

    return FileResponse(path=filename, media_type="application/pdf", filename="resume.pdf")
