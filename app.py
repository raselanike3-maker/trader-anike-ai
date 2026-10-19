import base64
import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI

load_dotenv()
ROOT = Path(__file__).resolve().parent
MAX_BYTES = 5 * 1024 * 1024
MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

app = FastAPI(title="TRADER ANIKE AI")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@app.get("/")
def home():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/api/health")
def health():
    return {"ok": True, "api_key_configured": bool(os.getenv("OPENAI_API_KEY"))}


def extract_json(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            raise ValueError("AI did not return JSON")
        return json.loads(match.group(0))


@app.post("/api/analyze")
async def analyze(
    image: UploadFile = File(...),
    timeframe: str = Form("5 seconds"),
    asset: str = Form("Quotex chart"),
    current_price: str = Form(""),
):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY সেট করা নেই। README অনুযায়ী .env ফাইলে API key যোগ করুন।"
        )

    content_type = (image.content_type or "").lower()
    allowed = {"image/png", "image/jpeg", "image/webp"}
    if content_type not in allowed:
        raise HTTPException(status_code=415, detail="PNG, JPG/JPEG বা WEBP ছবি দিন।")

    raw = await image.read()
    if not raw:
        raise HTTPException(status_code=400, detail="ছবিটি খালি।")
    if len(raw) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="ছবির আকার ৫ MB-এর কম রাখুন।")

    data_url = f"data:{content_type};base64,{base64.b64encode(raw).decode('ascii')}"
    prompt = f"""
তুমি TRADER ANIKE AI, চার্ট-ছবি বিশ্লেষণের সহকারী। ব্যবহারকারী {asset} এর স্ক্রিনশট দিয়েছে।
টাইমফ্রেম: {timeframe}
ব্যবহারকারী লিখলে বর্তমান মূল্য: {current_price or "দেওয়া হয়নি"}

শুধু ছবিতে দৃশ্যমান তথ্য বিশ্লেষণ করো। ছবিতে ক্যান্ডেল/প্রাইস/টাইমফ্রেম পরিষ্কার না হলে signal=WAIT দাও।
পরের ক্যান্ডেলের দিক নিশ্চিতভাবে বলা যায় না। UP/DOWN percentage-কে কেবল ছবির ভিত্তিতে আনুমানিক subjective estimate হিসেবে দাও; এটি calibrated probability বা জয়ের হার নয়। তথ্য দুর্বল হলে 50/50-এর কাছাকাছি রাখো এবং WAIT দাও। কোনো বানানো দাম/লেভেল দেবে না।
Round-number level কেবল তখনই দেবে যখন ছবিতে প্রাইস-স্কেল/বর্তমান মূল্য পড়া যায়; না হলে null। Entry level নিশ্চিত নির্দেশ নয়; স্পষ্ট দাম পড়া না গেলে null।
কেবল নিচের keys সহ বৈধ JSON ফেরত দাও:
{{
 "signal":"UP|DOWN|WAIT",
 "up_percent": 0-100 integer,
 "down_percent": 0-100 integer,
 "entry_level":"string or null",
 "round_number":"string or null",
 "reason_bn":"বাংলায় সর্বোচ্চ 3টি ছোট বাক্য",
 "risk_bn":"বাংলায় এক বাক্যে সতর্কতা",
 "image_quality":"clear|partial|poor"
}}
up_percent + down_percent অবশ্যই 100 হবে। Signal UP/DOWN তখনই দেবে যখন ছবির প্রমাণ যথেষ্ট; নইলে WAIT।
"""
    try:
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=MODEL,
            input=[{
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": data_url, "detail": "high"}
                ]
            }],
            max_output_tokens=500,
        )
        result = extract_json(response.output_text)
    except Exception as exc:
        # Avoid returning API internals or secrets to the browser.
        print(f"Analysis error: {type(exc).__name__}: {exc}")
        raise HTTPException(status_code=502, detail="AI বিশ্লেষণ করা যায়নি। API key, model access ও internet connection পরীক্ষা করুন।")

    signal = result.get("signal", "WAIT")
    if signal not in {"UP", "DOWN", "WAIT"}:
        signal = "WAIT"
    try:
        up = max(0, min(100, int(result.get("up_percent", 50))))
        down = max(0, min(100, int(result.get("down_percent", 50))))
    except (TypeError, ValueError):
        up, down = 50, 50
    # Normalize percentages so they always total 100.
    total = up + down
    if total == 0:
        up, down = 50, 50
    else:
        up = round(up / total * 100)
        down = 100 - up

    return {
        "signal": signal,
        "up_percent": up,
        "down_percent": down,
        "entry_level": result.get("entry_level"),
        "round_number": result.get("round_number"),
        "reason_bn": str(result.get("reason_bn", "ছবির তথ্য সীমিত; পরিষ্কার চার্ট দিন।"))[:800],
        "risk_bn": str(result.get("risk_bn", "এটি নিশ্চিত পূর্বাভাস নয়; ডেমোতে যাচাই করুন।"))[:300],
        "image_quality": result.get("image_quality", "partial"),
        "model": MODEL,
        "disclaimer": "এই শতাংশ AI-এর আনুমানিক মতামত; পরীক্ষিত জয়ের হার নয়।"
    }
