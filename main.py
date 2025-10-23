from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import sqlite3
import google.generativeai as genai
import time
from typing import Optional
import re


def extract_keywords(text: str):

    words = re.findall(r"[\wآ-ی]+", text)
    return [w for w in words if len(w) > 2]


load_dotenv()

app = FastAPI(title="Salona Instagram Bot - Gemini LLM Connected")



class SimulateDMIn(BaseModel):
    sender_id: str
    message_id: str
    text: str



class SimulateDMOut(BaseModel):
    reply: str



def search_products(query: str, limit: int = 5):
    
    db_path = os.path.join(os.getcwd(), "db", "app_data.sqlite")

    if not os.path.exists(db_path):
        print("❌ Database not found at:", db_path)
        return []

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    keywords = extract_keywords(query)
    if not keywords:
        conn.close()
        return []

    sql = "SELECT name, description, price FROM products WHERE "
    sql += " OR ".join(["name LIKE ? OR description LIKE ?"] * len(keywords))
    params = []
    for k in keywords:
        like = f"%{k}%"
        params.extend([like, like])

    sql += f" LIMIT {limit}"

    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()

    products = [
        {"name": r[0], "description": r[1], "price": r[2]}
        for r in rows
    ]
    return products



LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")


if LLM_PROVIDER == "gemini":
    genai.configure(api_key=GEMINI_API_KEY)


def send_prompt_to_llm(prompt: str, max_retries: int = 3) -> Optional[str]:

    attempt = 0
    while attempt < max_retries:
        try:
            if LLM_PROVIDER == "gemini":
                model = genai.GenerativeModel(GEMINI_MODEL)
                response = model.generate_content(prompt)
                text = response.text if hasattr(response, "text") else str(response)
                return text
            else:
                raise RuntimeError(f"LLM_PROVIDER غیرمجاز: {LLM_PROVIDER}")
        except Exception as e:
            attempt += 1
            time.sleep(min(2 ** attempt, 8))
            if attempt >= max_retries:
                raise RuntimeError(f"برقراری ارتباط با Gemini API ناموفق بود: {e}")
    return None




def build_prompt_for_generation(user_text: str, retrieved_products: list):

    intro = (
        "شما یک ربات فروشنده هستید. فقط به زبان فارسی و به صورت خلاصه و مودبانه پاسخ بدهید.\n"
        "با استفاده از اطلاعات زیر درباره محصولات، به سؤال کاربر پاسخ دهید:\n\n"
    )

    products_text = ""
    if retrieved_products:
        products_text += "محصولات یافت‌شده:\n"
        for p in retrieved_products:
            products_text += f"- {p['name']} — {p['description']} — {p['price']} تومان\n"
        products_text += "\n"

    question = f"سؤال کاربر: {user_text}\n\nپاسخ:"
    prompt = intro + products_text + question
    return prompt



@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/products_test")
async def get_products_test():
    db_path = os.path.join(os.path.dirname(__file__), "db", "app_data.sqlite")

    if not os.path.exists(db_path):
        return {"error": f"Database not found at: {db_path}"}

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT name, price FROM products LIMIT 5")
        rows = cur.fetchall()
        conn.close()
        return {"sample_products": rows}
    except Exception as e:
        return {"error": str(e)}


@app.post("/simulate_dm", response_model=SimulateDMOut)
async def simulate_dm(payload: SimulateDMIn):
    """
    دریافت پیام کاربر، جستجو در دیتابیس، ارسال پرامپت به LLM و بازگرداندن پاسخ نهایی.
    """
    try:
        results = search_products(payload.text)

        if not results:
            return {"reply": "❌ محصولی با این مشخصات پیدا نشد."}

        prompt = build_prompt_for_generation(payload.text, results)

        try:
            llm_response = send_prompt_to_llm(prompt)
        except Exception as err:
            print("❌ خطا در فراخوانی Gemini:", err)
            llm_response = None

        if llm_response:
            return {"reply": llm_response.strip()}

       
        reply_message = "📦 محصولات پیشنهادی:\n"
        for p in results:
            reply_message += f"- {p['name']} ({p['price']} تومان)\n"
        return {"reply": reply_message}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    import webbrowser
    import socket
    import threading
    import time

    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    print(f"🚀 Server is running at:")
    print(f" - Localhost: http://localhost:8000/docs")
    print(f" - LAN IP:   http://{local_ip}:8000/docs") 

    def open_browser():
        time.sleep(1) 
        webbrowser.open("http://localhost:8000/docs")  

    threading.Thread(target=open_browser).start()

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)




