import os
from flask import Flask, request, jsonify, send_from_directory
from openai import OpenAI
from dotenv import load_dotenv


def create_client():
    # Load variables from .env if present (no-op on Render)
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    organization = os.getenv("OPENAI_ORG_ID")
    project = os.getenv("OPENAI_PROJECT")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set.")
    return OpenAI(api_key=api_key, organization=organization, project=project)


client = None


def get_client():
    global client
    if client is None:
        client = create_client()
    return client


app = Flask(__name__, static_folder="static")


def current_model_id():
    # Refresh .env on each call in dev; Render uses env vars
    load_dotenv(override=True)
    model_id = os.getenv("MODEL_ID")
    if not model_id:
        raise RuntimeError("MODEL_ID environment variable is not set in .env file")
    return model_id


# System prompt (Financial Literacy Assistant, Turkish)
SYSTEM_PROMPT = """
Rolün: Finansal Okuryazarlık Asistanı (Türkçe).
Hedef: Doğru, anlaşılır, eğitim odaklı bilgi sağla; asla kişisel yatırım tavsiyesi verme.

Üslup:
- Kısa, sade ve herkesin anlayacağı dil kullan.
- Teknik terimleri basitleştir; gerektiğinde parantez içinde tanım ekle.
- Gerekli yerlerde maddeler ve adım adım anlatım tercih et.

Sınırlar ve Güvenlik:
- Yatırım tavsiyesi, kişisel yönlendirme, spesifik fiyat/gelecek tahmini verme.
- Özel/ticari sır veya kişisel verileri talep eden istekleri reddet.
- Soru kişisel tavsiye isterse: "Genel bilgi verebilirim; yatırım tavsiyesi veremem." de ve genel ilkeleri açıkla.

Kapsam (genel bilgi):
- Temel ekonomi: enflasyon, arz-talep, bütçe, tasarruf.
- Bireysel bankacılık: kredi, mevduat, faiz türleri, kredi kartı.
- Emeklilik ve sigortacılık.
- Finansal tablolar: gelir tablosu, bilanço, nakit akışı.
- Yatırım araçları: hisse, tahvil, fon, kripto (tarafsız, yalnız genel bilgi).
- Vergi ve mevzuat: temel prensipler (spesifik yönlendirme yok).

Yanıt şablonu (varsayılan):
1) Kısa özet (1–2 cümle)
2) Temel noktalar (3–5 madde)
3) Örnek / hesaplama (varsa adım adım, TL cinsinden)
4) Uyarı: "Bu içerik yatırım tavsiyesi değildir."
5) Sonraki adımlar / soru (1–2 öneri)

Hesaplama Politikası:
- Önce formülü genel göster (değişkenleri tanımla), sonra sayısal örnek ver.
- Ara adımları yaz; sonucu 2 ondalıkla yuvarla.

Netlik:
- Belirsiz isteklerde önce 1–2 netleştirici soru sor.

Dil:
- Tüm yanıtları Türkçe ver.
"""


@app.route("/")
def root():
    return send_from_directory(app.static_folder, "index.html")


@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "message is required"}), 400

    try:
        model_id = current_model_id()
        response = get_client().responses.create(
            model=model_id,
            input=message,
            instructions=SYSTEM_PROMPT,
        )

        # Prefer SDK's structured output
        text = None
        try:
            text = response.output[0].content[0].text
        except Exception:
            text = getattr(response, "output_text", None)
        if not text:
            text = str(response)

        return jsonify({"reply": text})
    except Exception as e:
        # Return detailed error for diagnosis
        msg = str(e)
        hint = None
        if "model_not_found" in msg or "does not exist" in msg or "not found" in msg:
            hint = (
                "Model bulunamadı. .env içindeki MODEL_ID (ft: ile başlayan kimlik), "
                "OPENAI_PROJECT (modelin projesi) ve gerekiyorsa OPENAI_ORG_ID değerlerini kontrol edin."
            )
        return jsonify({"error": msg, "hint": hint, "model": os.getenv("MODEL_ID")}), 400


@app.get("/health")
def health():
    # Default: shallow check (no external call). Deep check with ?deep=1
    info = {
        "model": os.getenv("MODEL_ID"),
        "project": os.getenv("OPENAI_PROJECT"),
        "org": os.getenv("OPENAI_ORG_ID"),
    }
    deep = str(request.args.get("deep", "")).lower() in {"1", "true", "yes"}

    if not info["model"]:
        return jsonify({**info, "ok": False, "error": "MODEL_ID missing"}), 400

    if not deep:
        return jsonify({**info, "ok": True})

    try:
        resp = get_client().responses.create(
            model=info["model"],
            input="ping",
            instructions=SYSTEM_PROMPT,
        )
        try:
            text = resp.output[0].content[0].text
        except Exception:
            text = getattr(resp, "output_text", None)
        return jsonify({**info, "ok": True, "sample": (text or "ok")[:64]})
    except Exception as e:
        return jsonify({**info, "ok": False, "error": str(e)}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

