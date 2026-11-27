import os, re, json, random, datetime, urllib.parse, requests
from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, FollowEvent, TextMessage,
    TextSendMessage, FlexSendMessage, BubbleContainer, CarouselContainer,
    BoxComponent, TextComponent, ButtonComponent, URIAction, MessageAction
)

app = FastAPI()
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")

# ⚠️ 1. 請填入「典藏書房與深度長文閱讀館資料庫」的 Google Apps Script /exec 網址
GOOGLE_SHEET_API = "https://script.google.com/macros/s/AKfycbxoe98yMHG5yioZyXV-8yN-xY4XuosoLRTWuvvwPWCHMiw8I_GHpgT4XoKupgZnpRlZ/exec"
# ⚠️ 2. 請填入這個閱讀機器人的 LINE 官方帳號 ID（包含 @ 符號，例如 @123abcde）
LINE_BOT_BASIC_ID = "@849zyixj"
# ⚠️ 3. 請填入這個閱讀機器人的 Render 公開網址（結尾不要加斜線）
RENDER_BASE_URL = "https://taiwan-classic-reading-salon-bot.onrender.com"
BOOK_AFFILIATE_URL = "https://books.com.tw"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 軌道 A：每日自動蒐集的新文章（由 API 動態抓取完整長文，與經典長文完全不重複）
DAILY_FRESH_ARTICLES = []

# 軌道 B：傳世經典長文原典館（完整原文 ＋ 深度逐段白話解析）
CLASSIC_LONG_ARTICLES = [
    {
        "id": "CL01", "track": "經典長文", "cat": "兵法謀略", "title": "《孫子兵法・謀攻篇》完整原典與現代戰略深解",
        "author": "孫武（春秋時期）",
        "quote": "「故百戰百勝，非善之善者也；不戰而屈人之兵，善之善者也。」",
        "content": "【完整原典】\n孫子曰：凡用兵之法，全國為上，破國次之；全軍為上，破軍次之；全旅為上，破旅次之；全卒為上，破卒次之；全伍為上，破伍次之。是故百戰百勝，非善之善者也；不戰而屈人之兵，善之善者也。\n\n故上兵伐謀，其次伐交，其次伐兵，其下攻城。攻城之法，為不得已。修櫓轒轀，具器械，三月而後成；距闉，又三月而後已。將不勝其忿而蟻附之，殺士三分之一而城不拔者，此攻之災也。\n\n故善用兵者，屈人之兵而非戰也，拔人之城而非攻也，毀人之國而非久也，必以全爭於天下，故兵不頓而利可全，此謀攻之法也。\n\n故用兵之法，十則圍之，五則攻之，倍則分之，敵則能戰之，少則能逃之，不若則能避之。故小敵之堅，大敵之擒也。\n\n夫將者，國之輔也。輔周則國必強，輔隙則國必弱。故君之所以患於軍者三：不知軍之不可以進而謂之進，不知軍之不可以退而謂之退，是謂縻軍；不知三軍之事，而同三軍之政者，則軍士惑矣；不知三軍之權，而同三軍之任，則軍士疑矣。三軍既惑且疑，則諸侯之難至矣，是謂亂軍引勝。\n\n故知勝有五：知可以戰與不可以戰者勝，識眾寡之用者勝，上下同欲者勝，以虞待不虞者勝，將能而君不御者勝。此五者，知勝之道也。\n\n故曰：知彼知己，百戰不殆；不知彼而知己，一勝一負；不知彼，不知己，每戰必殆。\n\n【現代商業與人生深度解析】\n本篇核心在於「全勝思維」與「成本意識」。真正的頂尖決策者，不會把精力耗費在硬碰硬的價格戰或消耗戰（攻城），而是從更高維度的商業模式設計（伐謀）與跨界聯盟（伐交）解決問題。在投入任何重大專案前，務必以「知勝五事」檢視：時機是否成熟、資源配置是否得當、團隊目標是否一致、是否做好風險預案，以及授權是否充分。",
        "url": BOOK_AFFILIATE_URL
    },
    {
        "id": "CL02", "track": "經典長文", "cat": "山水散文", "title": "蘇軾《前赤壁賦》完整原典與生命哲學賞析",
        "author": "蘇軾（北宋）",
        "quote": "「蓋將自其變者而觀之，則天地曾不能以一瞬；自其不變者而觀之，則物與我皆無盡也。」",
        "content": "【完整原典】\n壬戌之秋，七月既望，蘇子與客泛舟遊於赤壁之下。清風徐來，水波不興。舉酒屬客，誦明月之詩，歌窈窕之章。少焉，月出於東山之上，徘徊於斗牛之間。白露橫江，水光接天。縱一葦之所如，凌萬頃之茫然。浩浩乎如馮虛御風，而不知其所止；飄飄乎如遺世獨立，羽化而登仙。\n\n於是飲酒樂甚，扣舷而歌之。歌曰：「桂棹兮蘭槳，擊空明兮溯流光。渺渺兮予懷，望美人兮天一方。」客有吹洞簫者，倚歌而和之。其聲嗚嗚然，如怨如慕，如泣如訴，餘音嫋嫋，不絕如縷。舞幽壑之潛蛟，泣孤舟之嫠婦。\n\n蘇子愀然，正襟危坐而問客曰：「何為其然也？」客曰：「『月明星稀，烏鵲南飛』，此非曹孟德之詩乎？西望夏口，東望武昌，山川相繆，鬱乎蒼蒼，此非孟德之困於周郎者乎？方其破荊州，下江陵，順流而東也，舳艫千里，旌旗蔽空，釃酒臨江，橫槊賦詩，固一世之雄也，而今安在哉？況吾與子漁樵於江渚之上，侶魚蝦而友麋鹿，駕一葉之扁舟，舉匏樽以相屬。寄蜉蝣於天地，渺滄海之一粟。哀吾生之須臾，羨長江之無窮。挾飛仙以遨遊，抱明月而長終。知不可乎驟得，託遺響於悲風。」\n\n蘇子曰：「客亦知夫水與月乎？逝者如斯，而未嘗往也；盈虛者如彼，而卒莫消長也。蓋將自其變者而觀之，則天地曾不能以一瞬；自其不變者而觀之，則物與我皆無盡也，而又何羨乎！且夫天地之間，物各有主，苟非吾之所有，雖一毫而莫取。惟江上之清風，與山間之明月，耳得之而為聲，目遇之而成色，取之無禁，用之不竭，是造物者之無盡藏也，而吾與子之所共適。」\n\n客喜而笑，洗盞更酌。肴核既盡，杯盤狼藉。相與枕藉乎舟中，不知東方之既白。\n\n【哲學與心境深解】\n蘇軾在人生最低谷（烏臺詩案貶謫黃州）寫下此篇。面對歷史英雄的消逝與生命的短暫，他提出「變與不變」的雙重視角：若執著於外在名利與得失（變者），萬物瞬息萬變令人焦慮；若從宇宙運行與精神本質（不變者）來看，清風明月、內心平靜皆為無盡寶藏，無須羨慕外物，只需全心享受當下。",
        "url": BOOK_AFFILIATE_URL
    },
    {
        "id": "CL03", "track": "經典長文", "cat": "道家智慧", "title": "老子《道德經》核心精選十章完整原典與處世心法",
        "author": "老子（春秋時期）",
        "quote": "「上善若水。水善利萬物而不爭，處眾人之所惡，故幾於道。」",
        "content": "【完整原典精編】\n第一章：道可道，非常道。名可名，非常名。無名天地之始；有名萬物之母。故常無欲，以觀其妙；常有欲，以觀其徼。此兩者，同出而異名，同謂之玄。玄之又玄，眾妙之門。\n\n第八章：上善若水。水善利萬物而不爭，處眾人之所惡，故幾於道。居善地，心善淵，與善仁，言善信，正善治，事善能，動善時。夫唯不爭，故無尤。\n\n第十二章：五色令人目盲；五音令人耳聾；五味令人口爽；馳騁畋獵，令人心發狂；難得之貨，令人行妨。是以聖人為腹不為目，故去彼取此。\n\n第三十三章：知人者智，自知者明。勝人者有力，自勝者強。知足者富。強行者有志。不失其所者久。死而不亡者壽。\n\n第六十三章：為無為，事無事，味無味。大小多少，報怨以德。圖難於其易，為大於其細；天下難事，必作於易，天下大事，必作於細。是以聖人終不為大，故能成其大。\n\n第六十四章：其安易持，其未兆易謀。其脆易泮，其微易散。為之於未有，治之於未亂。合抱之木，生於毫末；九層之臺，起於累土；千里之行，始於足下。\n\n【現代生活應用】\n《道德經》教導我們「減法哲學」與「積累智慧」：外在聲色資訊過多（五色、五音）只會消耗心神，回歸內在真實需求（為腹不為目）才能獲得寧靜；同時所有偉大的成就都始於微小的日常積累（合抱之木生於毫末），在問題尚未惡化前提前佈局（治之於未亂），便是最高明的處世之道。",
        "url": BOOK_AFFILIATE_URL
    }
]
def fetch_full_wiki_text(title: str):
    try:
        u = f"https://wikipedia.org{urllib.parse.quote(title)}&format=json"
        headers = {"User-Agent": "ClassicReadingSalonBot/3.0"}
        pages = requests.get(u, headers=headers, timeout=6).json().get("query", {}).get("pages", {})
        for pid, pinfo in pages.items():
            txt = pinfo.get("extract", "").strip()
            if len(txt) >= 300:
                return txt
    except Exception:
        pass
    return ""

def fetch_daily_articles():
    try:
        today = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
        today_tag = today.strftime("%Y-%m-%d")
        if any(x.get("date_tag") == today_tag for x in DAILY_FRESH_ARTICLES) and len(DAILY_FRESH_ARTICLES) >= 10:
            return
        u = f"https://wikipedia.org{today.year}/{today.month:02d}/{today.day:02d}"
        headers = {"User-Agent": "ClassicReadingSalonBot/3.0"}
        j = requests.get(u, headers=headers, timeout=6).json()
        candidates = []
        tfa_title = j.get("tfa", {}).get("titles", {}).get("normalized", "")
        if tfa_title:
            candidates.append(tfa_title)
        for art in j.get("mostread", {}).get("articles", []):
            at = art.get("titles", {}).get("normalized", "")
            if at and "Wikipedia" not in at and ":" not in at and at not in candidates:
                candidates.append(at)
            if len(candidates) >= 14:
                break

        added = 0
        for raw_title in candidates:
            if added >= 10:
                break
            if any(raw_title in x.get("title", "") for x in DAILY_FRESH_ARTICLES):
                continue
            full_txt = fetch_full_wiki_text(raw_title)
            if len(full_txt) >= 450:
                added += 1
                clean_full = full_txt[:3600] + ("\n\n（……以上為完整深度知識長文精編）" if len(full_txt) > 3600 else "")
                first_sent = next(iter([s.strip() for s in clean_full.split("。") if len(s.strip()) > 15]), clean_full[:60])
                DAILY_FRESH_ARTICLES.append({
                    "id": f"DY{today.strftime('%m%d')}_{added}",
                    "date_tag": today_tag,
                    "track": "每日文章",
                    "cat": "今日深度百科",
                    "title": f"【今日長文 #{added}】{raw_title}",
                    "author": f"{today_tag} 全球華語熱讀深度長文",
                    "quote": f"「{first_sent}。」",
                    "content": clean_full,
                    "url": f"https://wikipedia.org{urllib.parse.quote(raw_title)}"
                })
    except Exception:
        pass

def call_sheet(payload: dict):
    try:
        r = requests.post(GOOGLE_SHEET_API, json=payload, timeout=12)
        return r.json()
    except Exception:
        return {}

def get_user_name(uid: str):
    try:
        return line_bot_api.get_profile(uid).display_name
    except Exception:
        return "典藏愛書人"

@app.api_route("/", methods=["GET", "HEAD"])
def root():
    return {"status": "Online", "service": "Taiwan Classic & Daily Full-Text Audio Reader Pro 3.0"}

@app.post("/api/article_add")
async def web_article_add(
    track: str = Form("每日文章"),
    cat: str = Form("深度長文"),
    title: str = Form("私藏完整長文"),
    author: str = Form("典藏書房讀者"),
    quote: str = Form("閱讀是隨身攜帶的避難所。"),
    content: str = Form("這是一篇完整收錄的深度長文。"),
    url: str = Form("")
):
    target_list = DAILY_FRESH_ARTICLES if track == "每日文章" else CLASSIC_LONG_ARTICLES
    bid = f"USR{len(target_list) + 1:02d}"
    target_list.insert(0, {
        "id": bid,
        "track": track,
        "cat": cat.strip() or "深度長文",
        "title": title.strip() or "私藏長文",
        "author": author.strip() or "典藏讀者",
        "quote": quote.strip() or "「閱讀讓靈魂更自由。」",
        "content": content.strip() or "完整長文內容",
        "url": url.strip() if url.strip().startswith("http") else BOOK_AFFILIATE_URL
    })
    call_sheet({"action": "add_note", "rec_id": bid, "user_id": "web_reader", "user_name": author, "cat": track, "title": title, "author": author, "quote": quote})
    return RedirectResponse(url="/reader_app?msg=added", status_code=303)

@app.post("/api/note_add")
async def web_note_add(title: str = Form(...), quote: str = Form(...)):
    rid = f"N{int(datetime.datetime.utcnow().timestamp() * 1000)}"
    call_sheet({"action": "add_note", "rec_id": rid, "user_id": "web_reader", "user_name": "書房讀者", "cat": "心動金句", "title": title, "author": "個人筆記", "quote": quote})
    return {"status": "ok"}
@app.get("/reader_app", response_class=HTMLResponse)
def classic_reading_salon_app(msg: str = ""):
    fetch_daily_articles()
    S = chr(47)
    daily_json = json.dumps(DAILY_FRESH_ARTICLES, ensure_ascii=False)
    classic_json = json.dumps(CLASSIC_LONG_ARTICLES, ensure_ascii=False)
    daily_cnt = len(DAILY_FRESH_ARTICLES)
    classic_cnt = len(CLASSIC_LONG_ARTICLES)
    toast_html = '<div class="toast">📚 您的完整長文已成功收錄進對應館藏軌道囉！</div>' if msg == "added" else ""

    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no"/>
    <title>📚 雙軌典藏書房 ＆ 完整長文有聲閱讀館 Pro</title>
    <style>
      * {{ box-sizing: border-box; -webkit-tap-highlight-color: transparent; }}
      body {{ margin: 0; padding: 0 0 92px 0; font-family: "Noto Serif TC", "Songti TC", Georgia, serif; background: #F7F3EA; color: #2C241E; min-height: 100vh; transition: 0.25s; }}
      body.dark {{ background: #1B1815; color: #EAE0D5; }}
      .topbar {{ background: rgba(247, 243, 234, 0.94); backdrop-filter: blur(14px); padding: 14px 18px; position: sticky; top: 0; z-index: 100; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(139, 108, 66, 0.25); }}
      body.dark .topbar {{ background: rgba(27, 24, 21, 0.94); border-bottom-color: rgba(212, 175, 55, 0.25); }}
      .topbar h1 {{ margin: 0; font-size: 16px; font-weight: 900; color: #1E3A2F; letter-spacing: 0.5px; }}
      body.dark .topbar h1 {{ color: #E5C158; }}
      .wrap {{ max-width: 580px; margin: 0 auto; padding: 14px; }}
      .toast {{ background: #E6F0EC; border: 1px solid #1E3A2F; color: #1E3A2F; padding: 12px; border-radius: 12px; font-size: 13px; font-weight: 700; margin-bottom: 12px; text-align: center; }}
      .hero-box {{ background: linear-gradient(135deg, #1E3A2F, #142820); color: #F7F3EA; border-radius: 20px; padding: 16px; margin-bottom: 14px; box-shadow: 0 10px 24px rgba(30, 58, 47, 0.2); border: 1px solid rgba(212, 175, 55, 0.35); }}
      .track-switch {{ display: flex; gap: 8px; margin-bottom: 12px; font-family: -apple-system, sans-serif; }}
      .track-btn {{ flex: 1; padding: 12px 8px; border-radius: 14px; font-size: 13px; font-weight: 900; cursor: pointer; border: 1px solid rgba(139, 108, 66, 0.3); background: #EFE9DC; color: #4A3B2C; text-align: center; }}
      .track-btn.active {{ background: linear-gradient(135deg, #1E3A2F, #274C3E); color: #F7F3EA; border-color: #D4AF37; box-shadow: 0 4px 12px rgba(30, 58, 47, 0.25); }}
      body.dark .track-btn {{ background: #2A2520; color: #C8BBAE; }}
      body.dark .track-btn.active {{ background: linear-gradient(135deg, #D4AF37, #B8860B); color: #1B1815; }}
      .toc-box {{ background: #FFFDF9; border: 1px solid rgba(139, 108, 66, 0.24); border-radius: 18px; padding: 14px; margin-bottom: 14px; }}
      body.dark .toc-box {{ background: #25211D; border-color: rgba(212, 175, 55, 0.22); }}
      .toc-item {{ display: block; padding: 6px 0; font-size: 13px; color: #1E3A2F; text-decoration: none; border-bottom: 1px dashed rgba(139, 108, 66, 0.18); font-weight: 700; cursor: pointer; }}
      body.dark .toc-item {{ color: #E5C158; }}
      .book-card {{ background: #FFFDF9; border: 1px solid rgba(139, 108, 66, 0.22); border-radius: 20px; padding: 18px; margin-bottom: 16px; box-shadow: 0 6px 20px rgba(44, 36, 30, 0.06); }}
      body.dark .book-card {{ background: #25211D; border-color: rgba(212, 175, 55, 0.2); }}
      .quote-box {{ background: #F4EFE4; border-left: 3px solid #B8860B; padding: 10px 12px; border-radius: 8px; font-size: 13px; color: #4A3B2C; margin: 10px 0; line-height: 1.6; font-style: italic; }}
      body.dark .quote-box {{ background: #1E1A17; color: #D8CBB8; border-left-color: #E5C158; }}
      .full-article {{ font-size: 16px; line-height: 1.95; white-space: pre-line; margin-top: 12px; padding-top: 12px; border-top: 1px dashed rgba(139, 108, 66, 0.28); letter-spacing: 0.4px; }}
      .btn-row {{ display: flex; gap: 8px; margin-top: 14px; font-family: -apple-system, sans-serif; }}
      .btn {{ flex: 1; text-align: center; text-decoration: none; padding: 10px 6px; border-radius: 12px; font-size: 12px; font-weight: 800; cursor: pointer; border: none; }}
      .btn-emerald {{ background: #1E3A2F; color: #F7F3EA; }}
      .btn-gold {{ background: linear-gradient(135deg, #D4AF37, #B8860B); color: #1B1815; }}
      .btn-paper {{ background: #EFE9DC; color: #4A3B2C; border: 1px solid rgba(139, 108, 66, 0.25); }}
      body.dark .btn-paper {{ background: #332E29; color: #EAE0D5; }}
      .field {{ width: 100%; background: #FFFDF9; border: 1px solid rgba(139, 108, 66, 0.3); color: #2C241E; padding: 12px; border-radius: 12px; font-size: 14px; margin-top: 8px; font-family: -apple-system, sans-serif; }}
      body.dark .field {{ background: #25211D; color: #EAE0D5; }}
      .page {{ display: none; }}
      .page.active {{ display: block; }}
      .tabbar {{ position: fixed; bottom: 0; left: 0; right: 0; background: rgba(247, 243, 234, 0.96); backdrop-filter: blur(14px); border-top: 1px solid rgba(139, 108, 66, 0.25); display: flex; padding: 8px 8px 14px; z-index: 120; font-family: -apple-system, sans-serif; }}
      body.dark .tabbar {{ background: rgba(27, 24, 21, 0.96); }}
      .tab {{ flex: 1; text-align: center; color: #6B5846; font-size: 12px; font-weight: 800; cursor: pointer; padding-top: 4px; }}
      .tab.active {{ color: #1E3A2F; }}
      body.dark .tab.active {{ color: #E5C158; }}
      .tab-cta {{ background: #1E3A2F; color: #F7F3EA; padding: 8px 12px; border-radius: 20px; font-size: 12px; }}
    </style></head><body>
    <div class="topbar">
      <h1>📚 雙軌長文有聲閱讀館</h1>
      <div style="display:flex;gap:6px;">
        <button type="button" onclick="changeFont(-1)" style="background:#EFE9DC;border:1px solid #B8860B;color:#2C241E;padding:4px 8px;border-radius:12px;font-size:11px;font-weight:800;cursor:pointer;">A-</button>
        <button type="button" onclick="changeFont(1)" style="background:#EFE9DC;border:1px solid #B8860B;color:#2C241E;padding:4px 8px;border-radius:12px;font-size:11px;font-weight:800;cursor:pointer;">A+</button>
        <button type="button" onclick="toggleTheme()" style="background:#EFE9DC;border:1px solid #B8860B;color:#2C241E;padding:4px 8px;border-radius:12px;font-size:11px;font-weight:800;cursor:pointer;">🌓</button>
      </div>
    </div>
    <div id="page-lib" class="page active"><div class="wrap">
      {toast_html}
      <div class="hero-box">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <span style="font-size:12px;color:#E5C158;font-weight:800;">🕯️ 雙軌獨立長文館 · 完整全文直讀</span>
          <span id="read-stat" style="font-size:11px;background:rgba(212,175,55,0.2);color:#F7F3EA;padding:3px 10px;border-radius:12px;font-weight:700;">已聽讀 0 篇</span>
        </div>
        <div id="track-desc" style="font-size:14px;font-weight:900;margin-top:8px;line-height:1.5;">📅【今日每日長文軌道】每日自動蒐集最新完整知識長文（與經典原典完全不同），支援台灣中文語音連播！</div>
        <div class="btn-row" style="margin-top:10px;">
          <button type="button" class="btn btn-gold" id="radio-btn" onclick="toggleRadio()">📻 本館有聲書連續朗讀</button>
          <button type="button" class="btn btn-paper" style="max-width:110px;" id="rate-btn" onclick="cycleRate()">🎚️ 1.0x 語速</button>
        </div>
      </div>

      <div class="track-switch">
        <button type="button" id="btn-track-daily" class="track-btn active" onclick="switchTrack('daily')">📅 今日每日長文（{daily_cnt} 篇完整）</button>
        <button type="button" id="btn-track-classic" class="track-btn" onclick="switchTrack('classic')">🏛️ 傳世經典原典（{classic_cnt} 篇完整）</button>
      </div>

      <div class="toc-box">
        <div id="toc-title" style="font-size:13px;font-weight:900;color:#1E3A2F;margin-bottom:6px;">📑 今日每日長文・全文快速跳轉目錄：</div>
        <div id="toc-list" style="max-height:150px;overflow-y:auto;"></div>
      </div>

      <input id="search-in" class="field" placeholder="🔍 在本軌道內搜尋標題、作者或全文關鍵字..." oninput="renderBooks()" style="margin-bottom:12px;"/>
      <div id="book-box"></div>
    </div></div>

    <div id="page-notes" class="page"><div class="wrap">
      <div class="book-card">
        <div style="font-size:17px;font-weight:900;color:#1E3A2F;margin-bottom:4px;">🔖 我的隨身金句與閱讀靈感筆記</div>
        <input id="note-title" class="field" placeholder="📖 文章標題或原典出處"/>
        <textarea id="note-quote" class="field" rows="3" placeholder="✍️ 寫下觸動你的段落或心得..."></textarea>
        <button type="button" class="btn btn-emerald" style="width:100%;margin-top:10px;padding:12px;" onclick="saveManualNote()">💾 存入我的雲端書摘筆記本</button>
      </div>
      <div id="notes-list"></div>
    </div></div>

    <div id="page-add" class="page"><div class="wrap">
      <div class="book-card">
        <div style="font-size:17px;font-weight:900;color:#1E3A2F;margin-bottom:4px;">➕ 投稿收錄完整長文（雙軌自選）</div>
        <form action="{S}api{S}article_add" method="post">
          <select name="track" class="field">
            <option value="每日文章">📅 收錄至「今日每日長文」軌道</option>
            <option value="經典長文">🏛️ 收錄至「傳世經典原典」軌道</option>
          </select>
          <input name="cat" class="field" placeholder="🏷️ 分類標籤（如：歷史長文、哲學原典、深度評論）" value="深度長文"/>
          <input name="title" class="field" placeholder="📚 文章完整標題" required/>
          <input name="author" class="field" placeholder="✍️ 作者姓名" value="典藏書房嚴選"/>
          <input name="quote" class="field" placeholder="💡 核心金句摘要" required/>
          <textarea name="content" class="field" rows="6" placeholder="📜 貼上完整長文全文（自動支援台灣中文語音朗讀）..." required></textarea>
          <input name="url" class="field" placeholder="🔗 相關購書或原文連結（選填）"/>
          <button type="submit" class="btn btn-emerald" style="width:100%;margin-top:12px;padding:14px;">📖 立即上架至指定長文館</button>
        </form>
      </div>
    </div></div>

    <div class="tabbar">
      <div class="tab active" onclick="switchTab('lib', this)">📚 雙軌全文與聽書</div>
      <div class="tab" onclick="switchTab('notes', this)">🔖 靈感書摘本</div>
      <div class="tab" onclick="switchTab('add', this)"><span class="tab-cta">➕ 收錄長文</span></div>
    </div>
    <script>
      const DAILY_LIST = {daily_json};
      const CLASSIC_LIST = {classic_json};
      let curTrack = 'daily', fontSize = 16, speakingIdx = -1, radioMode = false, speechRate = 1.0;

      function getActiveList() {{ return curTrack === 'daily' ? DAILY_LIST : CLASSIC_LIST; }}

      function updateReadStat() {{
        const doneList = JSON.parse(localStorage.getItem('read_done_ids') || '[]');
        document.getElementById('read-stat').innerText = '已聽讀 ' + doneList.length + ' 篇';
      }}

      function markDoneById(id) {{
        let doneList = JSON.parse(localStorage.getItem('read_done_ids') || '[]');
        if (!doneList.includes(id)) doneList.push(id);
        localStorage.setItem('read_done_ids', JSON.stringify(doneList));
        updateReadStat();
      }}

      function toggleTheme() {{ document.body.classList.toggle('dark'); }}

      function changeFont(delta) {{
        fontSize = Math.min(24, Math.max(13, fontSize + delta));
        document.querySelectorAll('.full-article').forEach(el => el.style.fontSize = fontSize + 'px');
      }}

      function cycleRate() {{
        speechRate = speechRate === 1.0 ? 1.25 : (speechRate === 1.25 ? 0.85 : 1.0);
        document.getElementById('rate-btn').innerText = '🎚️ ' + speechRate.toFixed(2).replace('.00','.0') + 'x 語速';
      }}

      function stopAllSpeech() {{
        if ('speechSynthesis' in window) window.speechSynthesis.cancel();
        speakingIdx = -1;
        radioMode = false;
        const rbtn = document.getElementById('radio-btn');
        if (rbtn) rbtn.innerText = '📻 本館有聲書連續朗讀';
        document.querySelectorAll('.tts-single-btn').forEach(b => b.innerText = '🎧 語音聽書');
      }}

      function switchTrack(t) {{
        stopAllSpeech();
        curTrack = t;
        document.getElementById('btn-track-daily').classList.toggle('active', t === 'daily');
        document.getElementById('btn-track-classic').classList.toggle('active', t === 'classic');
        document.getElementById('track-desc').innerText = t === 'daily'
          ? '📅【今日每日長文軌道】每日自動蒐集最新完整知識長文（與經典原典完全不同），支援台灣中文語音連播！'
          : '🏛️【傳世經典原典軌道】精選千古名篇完整原文與深度賞析，支援台灣中文語音連播！';
        document.getElementById('toc-title').innerText = t === 'daily'
          ? '📑 今日每日長文・全文快速跳轉目錄：'
          : '📑 傳世經典原典・全文快速跳轉目錄：';
        renderToc();
        renderBooks();
      }}

      function playBookAt(idx, autoNext) {{
        if (!('speechSynthesis' in window)) {{ alert('此瀏覽器不支援中文語音朗讀'); return; }}
        window.speechSynthesis.cancel();
        const list = getActiveList();
        if (idx >= list.length) {{ stopAllSpeech(); return; }}
        const b = list[idx];
        speakingIdx = idx;
        radioMode = autoNext;
        document.querySelectorAll('.tts-single-btn').forEach(btn => btn.innerText = '🎧 語音聽書');
        const curBtn = document.getElementById('tts-btn-' + idx);
        if (curBtn) curBtn.innerText = '⏹️ 停止朗讀';
        const rbtn = document.getElementById('radio-btn');
        if (rbtn) rbtn.innerText = autoNext ? `⏹️ 連播中 (${{idx+1}}/${{list.length}})` : '📻 本館有聲書連續朗讀';
        const utter = new SpeechSynthesisUtterance(b.title + '。' + b.quote + '。' + b.content);
        utter.lang = 'zh-TW';
        utter.rate = speechRate;
        utter.onend = () => {{
          markDoneById(b.id);
          if (radioMode && idx + 1 < list.length) {{
            playBookAt(idx + 1, true);
          }} else {{
            stopAllSpeech();
          }}
        }};
        window.speechSynthesis.speak(utter);
      }}

      function toggleRadio() {{
        if (radioMode) {{ stopAllSpeech(); return; }}
        playBookAt(0, true);
      }}

      function speakBook(idx) {{
        if (speakingIdx === idx && !radioMode) {{ stopAllSpeech(); return; }}
        playBookAt(idx, false);
      }}

      function jumpToBook(idx) {{
        const el = document.getElementById('book-card-' + idx);
        if (el) el.scrollIntoView({{behavior: 'smooth', block: 'start'}});
      }}

      function renderToc() {{
        const list = getActiveList();
        document.getElementById('toc-list').innerHTML = list.map((b, idx) =>
          `<div class="toc-item" onclick="jumpToBook(${{idx}})">📖 ${{idx + 1}}. ${{b.title}} <span style="color:#B8860B;font-size:11px;">(${{b.cat}})</span></div>`
        ).join('');
      }}

      function renderBooks() {{
        const list = getActiveList();
        const kw = (document.getElementById('search-in').value || '').trim().toLowerCase();
        document.getElementById('book-box').innerHTML = list.map((b, idx) => {{
          if (kw && !(b.title + b.author + b.quote + b.content).toLowerCase().includes(kw)) return '';
          const wordCnt = (b.content || '').length;
          return `<div id="book-card-${{idx}}" class="book-card">
            <div style="display:flex;justify-content:space-between;align-items:center;font-family:-apple-system,sans-serif;">
              <span style="font-size:11px;font-weight:800;background:#EFE9DC;color:#1E3A2F;padding:3px 10px;border-radius:10px;">${{b.track}} · ${{b.cat}}</span>
              <span style="font-size:11px;color:#B8860B;font-weight:800;">📜 全文約 ${{wordCnt}} 字</span>
            </div>
            <div style="font-size:19px;font-weight:900;margin-top:8px;line-height:1.45;">${{b.title}}</div>
            <div style="font-size:12px;color:#6B5846;margin-top:4px;">✍️ ${{b.author}}</div>
            <div class="quote-box">${{b.quote}}</div>
            <div class="full-article" style="font-size:${{fontSize}}px;">${{b.content}}</div>
            <div class="btn-row">
              <button type="button" id="tts-btn-${{idx}}" class="btn btn-gold tts-single-btn" onclick="speakBook(${{idx}})">🎧 語音聽書</button>
              <button type="button" class="btn btn-paper" onclick="quickSaveQuote(${{idx}}, this)">🔖 收藏金句</button>
              <a class="btn btn-emerald" href="${{b.url}}" target="_blank">🔗 延伸與購書</a>
            </div>
          </div>`;
        }}).join('');
      }}

      async function quickSaveQuote(idx, btn) {{
        const b = getActiveList()[idx];
        if (!b) return;
        markDoneById(b.id);
        btn.innerText = '✅ 已收進筆記';
        let notes = JSON.parse(localStorage.getItem('my_book_notes') || '[]');
        notes.unshift({{title: b.title, quote: b.quote}});
        localStorage.setItem('my_book_notes', JSON.stringify(notes));
        renderNotes();
        const fd = new FormData();
        fd.append('title', b.title);
        fd.append('quote', b.quote);
        await fetch('{S}api{S}note_add', {{method:'POST', body: fd}});
      }}

      async function saveManualNote() {{
        const t = document.getElementById('note-title').value.trim() || '隨身閱讀隨筆';
        const q = document.getElementById('note-quote').value.trim();
        if (!q) return;
        let notes = JSON.parse(localStorage.getItem('my_book_notes') || '[]');
        notes.unshift({{title: t, quote: q}});
        localStorage.setItem('my_book_notes', JSON.stringify(notes));
        document.getElementById('note-quote').value = '';
        renderNotes();
        const fd = new FormData();
        fd.append('title', t);
        fd.append('quote', q);
        await fetch('{S}api{S}note_add', {{method:'POST', body: fd}});
      }}

      function renderNotes() {{
        const notes = JSON.parse(localStorage.getItem('my_book_notes') || '[]');
        document.getElementById('notes-list').innerHTML = notes.map(n => `<div class="book-card">
          <div style="font-size:13px;font-weight:900;color:#B8860B;">📖 ${{n.title}}</div>
          <div class="quote-box" style="margin-bottom:0;">${{n.quote}}</div>
        </div>`).join('');
      }}

      function switchTab(t, el) {{ document.querySelectorAll('.page').forEach(x => x.classList.remove('active')); document.querySelectorAll('.tab').forEach(x => x.classList.remove('active')); document.getElementById('page-' + t).classList.add('active'); el.classList.add('active'); }}
      updateReadStat();
      renderToc();
      renderBooks();
      renderNotes();
    </script></body></html>"""
    return HTMLResponse(content=html)
def make_reading_salon_card():
    S = chr(47)
    app_uri = f"{RENDER_BASE_URL}/reader_app?openExternalBrowser=1"
    daily_top = next(iter(DAILY_FRESH_ARTICLES), {})
    classic_top = next(iter(CLASSIC_LONG_ARTICLES), {})
    d_title = str(daily_top.get("title", "今日全球熱讀深度長文")) if isinstance(daily_top, dict) else "今日全球熱讀深度長文"
    c_quote = str(classic_top.get("quote", "「不戰而屈人之兵，善之善者也。」")) if isinstance(classic_top, dict) else "「閱讀讓靈魂更自由。」"

    share_msg = urllib.parse.quote(f"📚【雙軌典藏書房 ＆ 完整長文有聲閱讀館】\n📅 今日新文：{d_title}\n🏛️ 經典名句：{c_quote}\n🎧 打開即享完整長文全文 ＋ 台灣中文語音連續聽書！\n👉 立即進入書房：\n{app_uri}")
    share_uri = f"https:{S}{S}line.me{S}R{S}share?text={share_msg}"

    bubble_1 = BubbleContainer(
        size="mega",
        header=BoxComponent(layout="vertical", background_color="#1E3A2F", padding_all="16px", contents=[
            TextComponent(text="📚 雙軌典藏書房 ＆ 長文閱讀館", weight="bold", size="md", color="#F7F3EA", wrap=True),
            TextComponent(text="今日每日長文 · 傳世經典原典 · 中文語音聽書", size="xs", color="#E5C158", weight="bold", wrap=True, margin="xs")
        ]),
        body=BoxComponent(layout="vertical", spacing="sm", background_color="#FFFDF9", contents=[
            TextComponent(text=f"📅 今日新文：{d_title}", size="xs", color="#1E3A2F", weight="bold", wrap=True),
            BoxComponent(layout="vertical", background_color="#F4EFE4", corner_radius="12px", padding_all="12px", contents=[
                TextComponent(text=f"🏛️ 經典原典：{c_quote}", size="xs", color="#4A3B2C", wrap=True)
            ])
        ]),
        footer=BoxComponent(layout="vertical", spacing="sm", background_color="#FFFDF9", contents=[
            ButtonComponent(style="primary", color="#1E3A2F", height="sm", action=URIAction(label="📖 開啟雙軌完整長文 ＆ 中文聽書", uri=app_uri)),
            BoxComponent(layout="horizontal", spacing="sm", contents=[
                ButtonComponent(style="primary", color="#B8860B", height="sm", action=MessageAction(label="📅 每日長文", text="每日長文")),
                ButtonComponent(style="secondary", height="sm", action=MessageAction(label="🏛️ 經典原典", text="經典長文"))
            ]),
            BoxComponent(layout="horizontal", spacing="sm", contents=[
                ButtonComponent(style="secondary", height="sm", action=MessageAction(label="🎲 抽金句", text="每日金句")),
                ButtonComponent(style="secondary", height="sm", action=MessageAction(label="📜 看目錄", text="雙軌目錄"))
            ])
        ])
    )

    bubble_2 = BubbleContainer(
        size="mega",
        header=BoxComponent(layout="vertical", background_color="#142820", padding_all="16px", contents=[
            TextComponent(text="🔖 分享長文 ＆ 購書收藏直達", weight="bold", size="md", color="#F7F3EA", wrap=True),
            TextComponent(text="一鍵分享好文給好友、收藏實體與電子書", size="xs", color="#E5C158", weight="bold", wrap=True, margin="xs")
        ]),
        body=BoxComponent(layout="vertical", spacing="xs", background_color="#FFFDF9", contents=[
            TextComponent(text="👈 向左滑動返回「雙軌完整長文與中文聽書館」", size="xxs", color="#6B5846", weight="bold")
        ]),
        footer=BoxComponent(layout="vertical", spacing="sm", background_color="#FFFDF9", contents=[
            ButtonComponent(style="primary", color="#B8860B", height="sm", action=URIAction(label="🛒 前往博客來／讀墨收藏好書", uri=BOOK_AFFILIATE_URL)),
            ButtonComponent(style="primary", color="#1E3A2F", height="sm", action=URIAction(label="💌 分享今日長文給 LINE 好友", uri=share_uri))
        ])
    )
    return CarouselContainer(contents=[bubble_1, bubble_2])
@app.post("/callback")
async def callback(request: Request):
    sig = request.headers.get("X-Line-Signature", "")
    body = await request.body()
    try:
        handler.handle(body.decode("utf-8"), sig)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    return "OK"

@handler.add(FollowEvent)
def on_follow(event):
    fetch_daily_articles()
    card = make_reading_salon_card()
    line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="📚 雙軌典藏書房 ＆ 完整長文有聲閱讀館已啟動", contents=card))

@handler.add(MessageEvent, message=TextMessage)
def on_text(event):
    uid = event.source.user_id
    txt = event.message.text.strip()
    app_uri = f"{RENDER_BASE_URL}/reader_app?openExternalBrowser=1"
    fetch_daily_articles()

    try:
        if txt == "每日長文":
            lines = ["📅【今日自動蒐集・完整深度長文目錄（與經典原典完全不同）】"]
            for idx, b in enumerate(DAILY_FRESH_ARTICLES[:10], 1):
                lines.append(f"\n{idx}. {b.get('title','')}（約 {len(b.get('content',''))} 字）")
            lines.append(f"\n🎧 點擊開啟護眼閱讀器，馬上全文直讀＋台灣中文語音連播：\n{app_uri}")
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="\n".join(lines)))
            return

        if txt == "經典長文":
            lines = ["🏛️【傳世經典原典館・完整原文與賞析目錄】"]
            for idx, b in enumerate(CLASSIC_LONG_ARTICLES, 1):
                lines.append(f"\n{idx}. {b.get('title','')}（約 {len(b.get('content',''))} 字）\n   ✍️ {b.get('author','')}")
            lines.append(f"\n🎧 點擊開啟護眼閱讀器，馬上全文直讀＋台灣中文語音連播：\n{app_uri}")
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="\n".join(lines)))
            return

        if txt == "雙軌目錄":
            msg = (
                f"📚【雙軌典藏書房・目前館藏統計】\n"
                f"• 📅 今日每日長文軌道：共 {len(DAILY_FRESH_ARTICLES)} 篇完整知識長文\n"
                f"• 🏛️ 傳世經典原典軌道：共 {len(CLASSIC_LONG_ARTICLES)} 篇千古名篇全文\n\n"
                f"👉 點擊進入雙軌閱讀館自由切換軌道與聽書：\n{app_uri}"
            )
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
            return

        if txt == "每日金句":
            pool = DAILY_FRESH_ARTICLES + CLASSIC_LONG_ARTICLES
            b = random.choice(pool) if pool else {}
            msg = (
                f"🎲【今日長文精選靈感】\n\n"
                f"{b.get('quote','')}\n"
                f"—— {b.get('author','')}《{b.get('title','')}》\n\n"
                f"📖 點擊進入閱讀器精讀完整全文與台灣中文語音聽書：\n{app_uri}"
            )
            card = make_reading_salon_card()
            line_bot_api.reply_message(event.reply_token, [
                TextSendMessage(text=msg),
                FlexSendMessage(alt_text="📚 雙軌典藏書房 ＆ 長文閱讀館", contents=card)
            ])
            return

        matched = [b for b in (DAILY_FRESH_ARTICLES + CLASSIC_LONG_ARTICLES) if any(k in txt for k in ["孫子", "兵法", "赤壁", "蘇軾", "道德經", "老子"])]
        if matched:
            b = next(iter(matched), {})
            msg = (
                f"🔍 為您找到傳世經典原典：\n\n"
                f"🏛️ {b.get('title','')}\n"
                f"✍️ {b.get('author','')}（全文約 {len(b.get('content',''))} 字）\n\n"
                f"{b.get('quote','')}\n\n"
                f"👉 立即開啟護眼閱讀器精讀完整原文＋台灣中文語音聽書：\n{app_uri}"
            )
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
            return

        card = make_reading_salon_card()
        line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="📚 雙軌典藏書房 ＆ 長文閱讀館", contents=card))
    except Exception as e:
        line_bot_api.push_message(uid, TextSendMessage(text=f"📚 書房小提示：{str(e)[:80]}"))
@app.post("/callback")
async def callback(request: Request):
    sig = request.headers.get("X-Line-Signature", "")
    body = await request.body()
    try:
        handler.handle(body.decode("utf-8"), sig)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    return "OK"

@handler.add(FollowEvent)
def on_follow(event):
    fetch_daily_articles()
    card = make_reading_salon_card()
    line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="📚 雙軌典藏書房 ＆ 完整長文有聲閱讀館已啟動", contents=card))

@handler.add(MessageEvent, message=TextMessage)
def on_text(event):
    uid = event.source.user_id
    txt = event.message.text.strip()
    app_uri = f"{RENDER_BASE_URL}/reader_app?openExternalBrowser=1"
    fetch_daily_articles()

    try:
        if txt == "每日長文":
            lines = ["📅【今日自動蒐集・完整深度長文目錄（與經典原典完全不同）】"]
            for idx, b in enumerate(DAILY_FRESH_ARTICLES[:10], 1):
                lines.append(f"\n{idx}. {b.get('title','')}（約 {len(b.get('content',''))} 字）")
            lines.append(f"\n🎧 點擊開啟護眼閱讀器，馬上全文直讀＋台灣中文語音連播：\n{app_uri}")
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="\n".join(lines)))
            return

        if txt == "經典長文":
            lines = ["🏛️【傳世經典原典館・完整原文與賞析目錄】"]
            for idx, b in enumerate(CLASSIC_LONG_ARTICLES, 1):
                lines.append(f"\n{idx}. {b.get('title','')}（約 {len(b.get('content',''))} 字）\n   ✍️ {b.get('author','')}")
            lines.append(f"\n🎧 點擊開啟護眼閱讀器，馬上全文直讀＋台灣中文語音連播：\n{app_uri}")
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="\n".join(lines)))
            return

        if txt == "雙軌目錄":
            msg = (
                f"📚【雙軌典藏書房・目前館藏統計】\n"
                f"• 📅 今日每日長文軌道：共 {len(DAILY_FRESH_ARTICLES)} 篇完整知識長文\n"
                f"• 🏛️ 傳世經典原典軌道：共 {len(CLASSIC_LONG_ARTICLES)} 篇千古名篇全文\n\n"
                f"👉 點擊進入雙軌閱讀館自由切換軌道與聽書：\n{app_uri}"
            )
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
            return

        if txt == "每日金句":
            pool = DAILY_FRESH_ARTICLES + CLASSIC_LONG_ARTICLES
            b = random.choice(pool) if pool else {}
            msg = (
                f"🎲【今日長文精選靈感】\n\n"
                f"{b.get('quote','')}\n"
                f"—— {b.get('author','')}《{b.get('title','')}》\n\n"
                f"📖 點擊進入閱讀器精讀完整全文與台灣中文語音聽書：\n{app_uri}"
            )
            card = make_reading_salon_card()
            line_bot_api.reply_message(event.reply_token, [
                TextSendMessage(text=msg),
                FlexSendMessage(alt_text="📚 雙軌典藏書房 ＆ 長文閱讀館", contents=card)
            ])
            return

        matched = [b for b in (DAILY_FRESH_ARTICLES + CLASSIC_LONG_ARTICLES) if any(k in txt for k in ["孫子", "兵法", "赤壁", "蘇軾", "道德經", "老子"])]
        if matched:
            b = next(iter(matched), {})
            msg = (
                f"🔍 為您找到傳世經典原典：\n\n"
                f"🏛️ {b.get('title','')}\n"
                f"✍️ {b.get('author','')}（全文約 {len(b.get('content',''))} 字）\n\n"
                f"{b.get('quote','')}\n\n"
                f"👉 立即開啟護眼閱讀器精讀完整原文＋台灣中文語音聽書：\n{app_uri}"
            )
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
            return

        card = make_reading_salon_card()
        line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="📚 雙軌典藏書房 ＆ 長文閱讀館", contents=card))
    except Exception as e:
        line_bot_api.push_message(uid, TextSendMessage(text=f"📚 書房小提示：{str(e)[:80]}"))
