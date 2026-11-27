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
# ⚠️ 4. 可填入您的博客來／Readmoo讀墨／金石堂聯盟分潤購書網址（未填預設導向博客來）
BOOK_AFFILIATE_URL = "https://books.com.tw"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

CLASSIC_LIBRARY = [
    {
        "id": "BK01", "cat": "習慣與效率", "read_min": "3 分鐘精讀", "title": "《原子習慣》：每天進步 1%，一年後強大 37 倍的複利系統",
        "author": "詹姆斯・克利爾（James Clear）",
        "quote": "「你並不會上升到你目標的高度，你會墜落到你系統的水平。」",
        "content": "多數人之所以無法養成好習慣，是因為把焦點放在「設定宏大目標」，卻忽略了「設計日常系統」。《原子習慣》揭示了行為改變的四大法則：\n\n1. 讓提示顯而易見：把想讀的書放在枕頭上，而不是收進書櫃深處；想喝水就把水壺放在書桌正中央。\n2. 讓吸引力增強：將「需要做的事」與「喜歡做的事」綁定，例如只有騎飛輪或散步時才允許自己聽最愛的 Podcast。\n3. 讓行動輕而易舉（兩分鐘法則）：任何新習慣的開始都不要超過兩分鐘——「每晚讀書一小時」先縮減為「每晚翻開書讀一頁」。\n4. 讓獎賞令人滿足：利用視覺化追蹤（如在日曆打勾或累積閱讀連勝天數），大腦會因為看見連續紀錄而產生強烈動力不願中斷。\n\n【今日立即行動】：今晚睡前把手機放在客廳充電，將一本實體書放在床頭櫃上，只讀兩頁就好。",
        "url": BOOK_AFFILIATE_URL
    },
    {
        "id": "BK02", "cat": "財富與思維", "read_min": "4 分鐘精讀", "title": "《納瓦爾寶典》：如何不靠運氣致富，打造睡覺時也能賺錢的槓桿",
        "author": "艾瑞克・喬根森（Eric Jorgenson）",
        "quote": "「追求財富，而不是金錢或地位。財富是指你在睡覺時仍能為你賺錢的資產。」",
        "content": "矽谷傳奇天使投資人納瓦爾（Naval Ravikant）指出，單純靠「出租自己的時間」永遠無法實現真正的財務自由，因為時間有上限且一旦停止工作收入就歸零。真正致富的核心公式是：\n\n1. 培養「專長知識（Specific Knowledge）」：這是無法透過短期培訓班教會的技能，它通常源自你內心真正的熱情與好奇心。對你來說像在玩耍，對別人來說卻像苦工的事，就是你的專長。\n2. 善用「無邊際複製成本的槓桿」：過去的槓桿需要資本或人力，但新時代最強大的槓桿是「程式碼（軟體工具）」與「自媒體內容（文章、影音、知識庫）」。寫好一套工具或一篇深度好文，複製給一萬人或一百萬人閱讀的邊際成本幾乎為零。\n3. 堅持「長期主義」：生命中所有的回報，無論是財富、人際關係還是知識，都來自複利效應。\n\n【今日立即行動】：寫下三件你做起來毫不費力、卻常被朋友請教的事，思考如何將它轉化為數位產品或系統。",
        "url": BOOK_AFFILIATE_URL
    },
    {
        "id": "BK03", "cat": "心理與人生", "read_min": "3 分鐘精讀", "title": "《被討厭的勇氣》：課題分離，斬斷 90% 人際內耗的阿德勒哲學",
        "author": "岸見一郎 ＆ 古賀史健",
        "quote": "「所有的煩惱，全都是人際關係的煩惱。而自由，就是被別人討厭的勇氣。」",
        "content": "我們之所以活得疲憊，往往是因為背負了太多「不屬於自己的課題」。阿德勒心理學提出最核心的解藥——「課題分離」：\n\n1. 區分「這是誰的課題」：判斷標準非常簡單——「這件事最終的後果由誰承擔？」例如：你認真寫出一篇真誠的文章，別人喜不喜歡、會不會批評，那是「別人的課題」，你無法控制；你唯一能控制的是「自己是否用心創作」。\n2. 停止尋求所有人的認可：如果你總是為了滿足別人的期待而活，等於把人生的方向盤交給他人。當你擁有「被討厭的勇氣」時，才真正獲得了做自己的自由。\n3. 活在「此時此刻」：人生不是一條必須爬到山頂才算成功的線，而是一連串「當下」的點。把聚光燈照在眼前的這一刻，專注做好手邊的事，過去與未來的焦慮自然消散。\n\n【今日立即行動】：遇到讓你焦慮的人際瑣事時，在心裡默念一句：「這是他的課題，不是我的課題。」",
        "url": BOOK_AFFILIATE_URL
    },
    {
        "id": "BK04", "cat": "財富與思維", "read_min": "4 分鐘精讀", "title": "《致富心態》：留有餘裕與長尾效應，普通人也能贏過華爾街的秘密",
        "author": "摩根・豪澤爾（Morgan Housel）",
        "quote": "「財富就是你沒花掉的那些錢。真正的富有，是擁有掌控自己時間的自由。」",
        "content": "理財的成敗，往往不取決於你懂多少複雜的財務公式，而是取決於你的「行為與心態」：\n\n1. 永遠為計畫預留「安全邊際（Room for Error）」：市場永遠會發生歷史上沒出現過的黑天鵝。不要把資金槓桿開到極限，留有足夠的緊急預備金，才能在暴跌時安穩睡覺，甚至逆勢撿便宜。\n2. 理解「長尾效應」：世界上絕大多數的成功，都來自極少數幾次關鍵決策。巴菲特一生買過四百多支股票，但絕大部分財富只來自其中不到十支。允許自己犯錯、持續留在牌桌上，等待屬於你的長尾爆發。\n3. 明確知道「什麼叫做足夠」：不要為了追求自己不需要的東西，去冒險賭上自己絕對不能失去的東西（家人、健康與平靜）。\n\n【今日立即行動】：檢視自己的資產配置，確保手邊永遠留有一筆能讓自己從容應對突發狀況的現金安全墊。",
        "url": BOOK_AFFILIATE_URL
    },
    {
        "id": "BK05", "cat": "深度長文", "read_min": "3 分鐘精讀", "title": "《心流（Flow）》：如何在資訊爆炸時代，進入忘我且高產出的巔峰狀態",
        "author": "米哈里・契克森米哈伊",
        "quote": "「一個人最美好的時刻，往往發生在身體或心智為了完成某件有挑戰性的事而發揮到極限之時。」",
        "content": "滑短影音雖然帶來短暫的多巴胺刺激，結束後卻常讓人感到空虛疲憊；唯有進入「心流（Flow）」狀態，才能帶來深層的幸福感與自我實現：\n\n1. 挑戰與技能的黃金平衡：當任務太簡單時，人會感到無聊；當任務太難時，人會感到焦慮。將難度設定在「比你現有能力高出 10%」的位置，最容易觸發心流。\n2. 單一任務與零干擾環境：大腦每次被手機通知打斷，平均需要 15 分鐘才能重新找回深度專注。設定一個 45 分鐘的「免打擾番茄鐘」，關閉所有彈窗，全神貫注只做一件事。\n3. 即時反饋機制：無論是寫程式看到畫面成功跑出來、騎單車看到碼表里程推進，還是閱讀完一篇長文，清晰的即時反饋會讓大腦自動鎖定專注。\n\n【今日立即行動】：現在就深呼吸三次，在接下來的 25 分鐘內不看任何通知，專心完成一件最重要的事。",
        "url": BOOK_AFFILIATE_URL
    }
]
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
    return {"status": "Online", "service": "Taiwan Classic Reading Salon & Longform Reader Pro 1.0"}

@app.post("/api/article_add")
async def web_article_add(
    cat: str = Form("深度長文"),
    title: str = Form("私藏經典好文"),
    author: str = Form("典藏書房讀者"),
    quote: str = Form("閱讀是隨身攜帶的避難所。"),
    content: str = Form("這是一篇值得反覆細讀的深度長文。"),
    url: str = Form("")
):
    bid = f"BK{len(CLASSIC_LIBRARY) + 1:02d}"
    mins = max(1, round(len(content) / 350))
    CLASSIC_LIBRARY.insert(0, {
        "id": bid,
        "cat": cat.strip() or "深度長文",
        "read_min": f"{mins} 分鐘精讀",
        "title": title.strip() or "私藏好文",
        "author": author.strip() or "典藏讀者",
        "quote": quote.strip() or "「閱讀讓靈魂更自由。」",
        "content": content.strip() or "經典長文內容",
        "url": url.strip() if url.strip().startswith("http") else BOOK_AFFILIATE_URL
    })
    call_sheet({
        "action": "add_note",
        "rec_id": bid,
        "user_id": "web_reader",
        "user_name": author.strip() or "書房投稿者",
        "cat": cat,
        "title": title,
        "author": author,
        "quote": quote
    })
    return RedirectResponse(url="/reader_app?msg=added", status_code=303)

@app.post("/api/note_add")
async def web_note_add(title: str = Form(...), quote: str = Form(...)):
    rid = f"N{int(datetime.datetime.utcnow().timestamp() * 1000)}"
    call_sheet({
        "action": "add_note",
        "rec_id": rid,
        "user_id": "web_reader",
        "user_name": "書房讀者",
        "cat": "心動金句",
        "title": title,
        "author": "個人筆記",
        "quote": quote
    })
    return {"status": "ok"}
@app.get("/reader_app", response_class=HTMLResponse)
def classic_reading_salon_app(msg: str = ""):
    S = chr(47)
    books_json = json.dumps(CLASSIC_LIBRARY, ensure_ascii=False)
    toast_html = '<div class="toast">📚 您的私藏好書／長文已成功收錄進典藏書房囉！</div>' if msg == "added" else ""

    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no"/>
    <title>📚 典藏書房 ＆ 深度長文閱讀館 Pro</title>
    <style>
      * {{ box-sizing: border-box; -webkit-tap-highlight-color: transparent; }}
      body {{ margin: 0; padding: 0 0 92px 0; font-family: "Noto Serif TC", "Songti TC", Georgia, serif; background: #F7F3EA; color: #2C241E; min-height: 100vh; transition: 0.25s; }}
      body.dark {{ background: #1B1815; color: #EAE0D5; }}
      .topbar {{ background: rgba(247, 243, 234, 0.94); backdrop-filter: blur(14px); padding: 14px 18px; position: sticky; top: 0; z-index: 100; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(139, 108, 66, 0.25); }}
      body.dark .topbar {{ background: rgba(27, 24, 21, 0.94); border-bottom-color: rgba(212, 175, 55, 0.25); }}
      .topbar h1 {{ margin: 0; font-size: 16px; font-weight: 900; color: #1E3A2F; letter-spacing: 0.5px; }}
      body.dark .topbar h1 {{ color: #E5C158; }}
      .wrap {{ max-width: 560px; margin: 0 auto; padding: 14px; }}
      .toast {{ background: #E6F0EC; border: 1px solid #1E3A2F; color: #1E3A2F; padding: 12px; border-radius: 12px; font-size: 13px; font-weight: 700; margin-bottom: 12px; text-align: center; }}
      .hero-box {{ background: linear-gradient(135deg, #1E3A2F, #142820); color: #F7F3EA; border-radius: 20px; padding: 16px; margin-bottom: 14px; box-shadow: 0 10px 24px rgba(30, 58, 47, 0.2); border: 1px solid rgba(212, 175, 55, 0.35); }}
      .chips {{ display: flex; gap: 8px; overflow-x: auto; padding-bottom: 12px; scrollbar-width: none; }}
      .chip {{ white-space: nowrap; background: #EFE9DC; border: 1px solid rgba(139, 108, 66, 0.25); color: #5C4938; padding: 7px 14px; border-radius: 20px; font-size: 12px; font-weight: 700; cursor: pointer; font-family: -apple-system, sans-serif; }}
      .chip.active {{ background: #1E3A2F; border-color: #D4AF37; color: #F7F3EA; }}
      body.dark .chip {{ background: #2A2520; color: #C8BBAE; }}
      body.dark .chip.active {{ background: #D4AF37; color: #1B1815; }}
      .book-card {{ background: #FFFDF9; border: 1px solid rgba(139, 108, 66, 0.22); border-radius: 20px; padding: 18px; margin-bottom: 14px; box-shadow: 0 6px 20px rgba(44, 36, 30, 0.06); }}
      body.dark .book-card {{ background: #25211D; border-color: rgba(212, 175, 55, 0.2); }}
      .quote-box {{ background: #F4EFE4; border-left: 3px solid #B8860B; padding: 10px 12px; border-radius: 8px; font-size: 13px; color: #4A3B2C; margin: 10px 0; line-height: 1.6; font-style: italic; }}
      body.dark .quote-box {{ background: #1E1A17; color: #D8CBB8; border-left-color: #E5C158; }}
      .btn-row {{ display: flex; gap: 8px; margin-top: 12px; font-family: -apple-system, sans-serif; }}
      .btn {{ flex: 1; text-align: center; text-decoration: none; padding: 10px 6px; border-radius: 12px; font-size: 12px; font-weight: 800; cursor: pointer; border: none; }}
      .btn-emerald {{ background: #1E3A2F; color: #F7F3EA; }}
      .btn-gold {{ background: linear-gradient(135deg, #D4AF37, #B8860B); color: #1B1815; }}
      .btn-paper {{ background: #EFE9DC; color: #4A3B2C; border: 1px solid rgba(139, 108, 66, 0.25); }}
      body.dark .btn-paper {{ background: #332E29; color: #EAE0D5; }}
      .reader-modal {{ display: none; position: fixed; inset: 0; background: #F7F3EA; z-index: 200; overflow-y: auto; padding: 18px 18px 90px; }}
      body.dark .reader-modal {{ background: #1B1815; }}
      .reader-modal.open {{ display: block; }}
      .reader-body {{ max-width: 600px; margin: 14px auto; font-size: 17px; line-height: 1.95; white-space: pre-line; letter-spacing: 0.4px; }}
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
    <div class="topbar"><h1>📚 典藏書房 ＆ 深度長文閱讀館</h1><button type="button" onclick="toggleTheme()" style="background:#EFE9DC;border:1px solid #B8860B;color:#2C241E;padding:4px 10px;border-radius:16px;font-size:11px;font-weight:800;cursor:pointer;">🌓 護眼日/夜</button></div>
    <div id="page-lib" class="page active"><div class="wrap">
      {toast_html}
      <div class="hero-box">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <span style="font-size:12px;color:#E5C158;font-weight:800;">🕯️ 每日沉浸閱讀 · 精神避風港</span>
          <span id="read-stat" style="font-size:11px;background:rgba(212,175,55,0.2);color:#F7F3EA;padding:3px 10px;border-radius:12px;font-weight:700;">已精讀 0 篇</span>
        </div>
        <div style="font-size:16px;font-weight:900;margin-top:8px;line-height:1.5;">「閱讀是隨身攜帶的避難所，隨時翻開一頁，與人類最偉大的靈魂對話。」</div>
        <div class="btn-row" style="margin-top:10px;">
          <button type="button" class="btn btn-gold" onclick="openRandomBook()">🎲 隨機盲抽今日必讀經典</button>
        </div>
      </div>

      <input id="search-in" class="field" placeholder="🔍 搜尋書名、作者或關鍵字（如：原子習慣、納瓦爾、心流）..." oninput="renderBooks()" style="margin-bottom:10px;"/>

      <div class="chips">
        <div class="chip active" onclick="filterCat('all', this)">📚 全部典藏館藏</div>
        <div class="chip" onclick="filterCat('習慣與效率', this)">⏳ 習慣與效率</div>
        <div class="chip" onclick="filterCat('財富與思維', this)">💎 財富與思維</div>
        <div class="chip" onclick="filterCat('心理與人生', this)">🌿 心理與人生</div>
        <div class="chip" onclick="filterCat('深度長文', this)">📜 深度長文</div>
      </div>
      <div id="book-box"></div>
    </div></div>

    <div id="page-notes" class="page"><div class="wrap">
      <div class="book-card">
        <div style="font-size:17px;font-weight:900;color:#1E3A2F;margin-bottom:4px;">🔖 我的隨身金句與閱讀靈感筆記</div>
        <div style="font-size:12px;color:#6B5846;margin-bottom:10px;">閱讀時點擊「收藏金句」，或在此記下觸動你的一句話：</div>
        <input id="note-title" class="field" placeholder="📖 書名或文章出處（如：《原子習慣》）"/>
        <textarea id="note-quote" class="field" rows="3" placeholder="✍️ 寫下觸動你的金句或閱讀心得..."></textarea>
        <button type="button" class="btn btn-emerald" style="width:100%;margin-top:10px;padding:12px;" onclick="saveManualNote()">💾 存入我的雲端書摘筆記本</button>
      </div>
      <div id="notes-list"></div>
    </div></div>

    <div id="page-add" class="page"><div class="wrap">
      <div class="book-card">
        <div style="font-size:17px;font-weight:900;color:#1E3A2F;margin-bottom:4px;">➕ 投稿收錄經典好書或深度長文</div>
        <div style="font-size:12px;color:#6B5846;">貼上您喜愛的好書精華或長文，立即上架至書房隨時點開閱讀與語音聽書：</div>
        <form action="{S}api{S}article_add" method="post">
          <select name="cat" class="field">
            <option value="習慣與效率">⏳ 習慣與效率</option>
            <option value="財富與思維">💎 財富與思維</option>
            <option value="心理與人生">🌿 心理與人生</option>
            <option value="深度長文">📜 深度長文</option>
          </select>
          <input name="title" class="field" placeholder="📚 書名與核心主題（如：《思考，快與慢》深度拆解）" required/>
          <input name="author" class="field" placeholder="✍️ 作者姓名" value="典藏書房嚴選"/>
          <input name="quote" class="field" placeholder="💡 最具代表性的一句金句" required/>
          <textarea name="content" class="field" rows="5" placeholder="📜 貼上完整精讀長文內容（支援自動計算閱讀時間與中文語音朗讀）..." required></textarea>
          <input name="url" class="field" placeholder="🔗 博客來／讀墨購書分潤連結（選填）"/>
          <button type="submit" class="btn btn-emerald" style="width:100%;margin-top:12px;padding:14px;">📖 立即上架至典藏書房</button>
        </form>
      </div>
    </div></div>

    <div class="tabbar">
      <div class="tab active" onclick="switchTab('lib', this)">📚 典藏閱讀館</div>
      <div class="tab" onclick="switchTab('notes', this)">🔖 靈感書摘本</div>
      <div class="tab" onclick="switchTab('add', this)"><span class="tab-cta">➕ 收錄好文</span></div>
    </div>
    <div id="reader-modal" class="reader-modal">
      <div style="max-width:600px;margin:0 auto;">
        <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid rgba(139,108,66,0.25);padding-bottom:12px;">
          <button type="button" class="btn btn-paper" style="max-width:95px;" onclick="closeReader()">⬅️ 返回書房</button>
          <div style="display:flex;gap:6px;">
            <button type="button" class="btn btn-paper" style="padding:8px 12px;" onclick="changeFont(-2)">A-</button>
            <button type="button" class="btn btn-paper" style="padding:8px 12px;" onclick="changeFont(2)">A+</button>
            <button type="button" class="btn btn-gold" id="tts-btn" style="padding:8px 12px;" onclick="toggleSpeech()">🎧 語音聽書</button>
          </div>
        </div>
        <div id="rd-cat" style="font-size:12px;color:#B8860B;font-weight:800;margin-top:16px;"></div>
        <h2 id="rd-title" style="font-size:22px;line-height:1.4;margin:6px 0;"></h2>
        <div id="rd-author" style="font-size:13px;color:#6B5846;margin-bottom:12px;"></div>
        <div id="rd-quote" class="quote-box"></div>
        <div id="rd-body" class="reader-body"></div>
        <div class="btn-row" style="margin-top:24px;">
          <button type="button" class="btn btn-emerald" id="done-btn" onclick="markReadDone()">✅ 標記已精讀完成</button>
          <a id="rd-buy" class="btn btn-gold" href="{BOOK_AFFILIATE_URL}" target="_blank">🛒 收藏實體／電子書</a>
        </div>
      </div>
    </div>

    <script>
      const BOOKS = {books_json};
      const NL = String.fromCharCode(10);
      let curCat = 'all', curBook = null, fontSize = 17, speaking = false;

      function updateReadStat() {{
        const doneList = JSON.parse(localStorage.getItem('read_done_ids') || '[]');
        document.getElementById('read-stat').innerText = '已精讀 ' + doneList.length + ' 篇';
      }}

      function toggleTheme() {{ document.body.classList.toggle('dark'); }}

      function changeFont(delta) {{
        fontSize = Math.min(24, Math.max(14, fontSize + delta));
        document.getElementById('rd-body').style.fontSize = fontSize + 'px';
      }}

      function toggleSpeech() {{
        if (!('speechSynthesis' in window)) {{ alert('此瀏覽器不支援語音朗讀'); return; }}
        const btn = document.getElementById('tts-btn');
        if (speaking) {{
          window.speechSynthesis.cancel();
          speaking = false;
          btn.innerText = '🎧 語音聽書';
          return;
        }}
        if (!curBook) return;
        const utter = new SpeechSynthesisUtterance(curBook.title + '。' + curBook.quote + '。' + curBook.content);
        utter.lang = 'zh-TW';
        utter.rate = 1.02;
        utter.onend = () => {{ speaking = false; btn.innerText = '🎧 語音聽書'; }};
        window.speechSynthesis.speak(utter);
        speaking = true;
        btn.innerText = '⏹️ 停止朗讀';
      }}

      function openReader(idx) {{
        curBook = BOOKS[idx];
        if (!curBook) return;
        document.getElementById('rd-cat').innerText = curBook.cat + ' · ' + curBook.read_min;
        document.getElementById('rd-title').innerText = curBook.title;
        document.getElementById('rd-author').innerText = '作者：' + curBook.author;
        document.getElementById('rd-quote').innerText = curBook.quote;
        document.getElementById('rd-body').innerText = curBook.content;
        document.getElementById('rd-buy').href = curBook.url || '{BOOK_AFFILIATE_URL}';
        document.getElementById('done-btn').innerText = '✅ 標記已精讀完成';
        document.getElementById('reader-modal').classList.add('open');
      }}

      function openRandomBook() {{
        if (BOOKS.length > 0) openReader(Math.floor(Math.random() * BOOKS.length));
      }}

      function closeReader() {{
        if (speaking && 'speechSynthesis' in window) {{ window.speechSynthesis.cancel(); speaking = false; }}
        document.getElementById('tts-btn').innerText = '🎧 語音聽書';
        document.getElementById('reader-modal').classList.remove('open');
      }}

      function markReadDone() {{
        if (!curBook) return;
        let doneList = JSON.parse(localStorage.getItem('read_done_ids') || '[]');
        if (!doneList.includes(curBook.id)) doneList.push(curBook.id);
        localStorage.setItem('read_done_ids', JSON.stringify(doneList));
        updateReadStat();
        document.getElementById('done-btn').innerText = '🎉 已納入精讀成就！';
      }}

      function filterCat(c, el) {{
        curCat = c;
        document.querySelectorAll('#page-lib .chips .chip').forEach(x => x.classList.remove('active'));
        el.classList.add('active');
        renderBooks();
      }}

      function renderBooks() {{
        const kw = (document.getElementById('search-in').value || '').trim().toLowerCase();
        document.getElementById('book-box').innerHTML = BOOKS.map((b, idx) => {{
          if (curCat !== 'all' && b.cat !== curCat) return '';
          if (kw && !(b.title + b.author + b.quote + b.content).toLowerCase().includes(kw)) return '';
          return `<div class="book-card">
            <div style="display:flex;justify-content:space-between;align-items:center;font-family:-apple-system,sans-serif;">
              <span style="font-size:11px;font-weight:800;background:#EFE9DC;color:#1E3A2F;padding:3px 10px;border-radius:10px;">${{b.cat}}</span>
              <span style="font-size:11px;color:#B8860B;font-weight:800;">⏱️ ${{b.read_min}}</span>
            </div>
            <div style="font-size:18px;font-weight:900;margin-top:8px;line-height:1.45;">${{b.title}}</div>
            <div style="font-size:12px;color:#6B5846;margin-top:4px;">✍️ ${{b.author}}</div>
            <div class="quote-box">${{b.quote}}</div>
            <div class="btn-row">
              <button type="button" class="btn btn-emerald" onclick="openReader(${{idx}})">📖 馬上沉浸閱讀</button>
              <button type="button" class="btn btn-paper" onclick="quickSaveQuote(${{idx}}, this)">🔖 收藏金句</button>
            </div>
          </div>`;
        }}).join('');
      }}

      async function quickSaveQuote(idx, btn) {{
        const b = BOOKS[idx];
        if (!b) return;
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
      renderBooks();
      renderNotes();
    </script></body></html>"""
    return HTMLResponse(content=html)
def make_reading_salon_card():
    S = chr(47)
    app_uri = f"{RENDER_BASE_URL}/reader_app?openExternalBrowser=1"
    first_book = next(iter(CLASSIC_LIBRARY), {})
    daily_title = str(first_book.get("title", "《原子習慣》深度精讀")) if isinstance(first_book, dict) else "《原子習慣》深度精讀"
    daily_quote = str(first_book.get("quote", "「你並不會上升到你目標的高度，你會墜落到你系統的水平。」")) if isinstance(first_book, dict) else "「閱讀讓靈魂更自由。」"

    share_msg = urllib.parse.quote(f"📚【典藏書房 ＆ 深度長文閱讀館】\n今日精選金句：{daily_quote}\n📖 點開即讀經典名著深度拆解 ＋ 中文語音聽書！\n👉 立即進入書房：\n{app_uri}")
    share_uri = f"https:{S}{S}line.me{S}R{S}share?text={share_msg}"

    bubble_1 = BubbleContainer(
        size="mega",
        header=BoxComponent(layout="vertical", background_color="#1E3A2F", padding_all="16px", contents=[
            TextComponent(text="📚 典藏書房 ＆ 深度長文閱讀館", weight="bold", size="md", color="#F7F3EA", wrap=True),
            TextComponent(text="經典名著精讀 · 語音聽書 · 靈感書摘筆記", size="xs", color="#E5C158", weight="bold", wrap=True, margin="xs")
        ]),
        body=BoxComponent(layout="vertical", spacing="sm", background_color="#FFFDF9", contents=[
            TextComponent(text=f"📖 今日館藏精選：{daily_title}", size="xs", color="#1E3A2F", weight="bold", wrap=True),
            BoxComponent(layout="vertical", background_color="#F4EFE4", corner_radius="12px", padding_all="12px", contents=[
                TextComponent(text=daily_quote, size="xs", color="#4A3B2C", wrap=True)
            ])
        ]),
        footer=BoxComponent(layout="vertical", spacing="sm", background_color="#FFFDF9", contents=[
            ButtonComponent(style="primary", color="#1E3A2F", height="sm", action=URIAction(label="📖 開啟典藏書房 ＆ 馬上閱讀", uri=app_uri)),
            BoxComponent(layout="horizontal", spacing="sm", contents=[
                ButtonComponent(style="primary", color="#B8860B", height="sm", action=MessageAction(label="🎲 抽金句", text="每日金句")),
                ButtonComponent(style="secondary", height="sm", action=MessageAction(label="📚 看書單", text="經典書單"))
            ]),
            BoxComponent(layout="horizontal", spacing="sm", contents=[
                ButtonComponent(style="secondary", height="sm", action=MessageAction(label="💎 讀財富", text="財富思維")),
                ButtonComponent(style="secondary", height="sm", action=MessageAction(label="🌿 讀心理", text="心理人生"))
            ])
        ])
    )

    bubble_2 = BubbleContainer(
        size="mega",
        header=BoxComponent(layout="vertical", background_color="#142820", padding_all="16px", contents=[
            TextComponent(text="🔖 分享好文 ＆ 購書收藏直達", weight="bold", size="md", color="#F7F3EA", wrap=True),
            TextComponent(text="一鍵分享今日金句給好友、收藏實體與電子書", size="xs", color="#E5C158", weight="bold", wrap=True, margin="xs")
        ]),
        body=BoxComponent(layout="vertical", spacing="xs", background_color="#FFFDF9", contents=[
            TextComponent(text="👈 向左滑動返回「典藏書房與長文閱讀器」", size="xxs", color="#6B5846", weight="bold")
        ]),
        footer=BoxComponent(layout="vertical", spacing="sm", background_color="#FFFDF9", contents=[
            ButtonComponent(style="primary", color="#B8860B", height="sm", action=URIAction(label="🛒 前往博客來／讀墨收藏好書", uri=BOOK_AFFILIATE_URL)),
            ButtonComponent(style="primary", color="#1E3A2F", height="sm", action=URIAction(label="💌 分享今日金句給 LINE 好友", uri=share_uri))
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
    card = make_reading_salon_card()
    line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="📚 典藏書房 ＆ 深度長文閱讀館已啟動", contents=card))

@handler.add(MessageEvent, message=TextMessage)
def on_text(event):
    uid = event.source.user_id
    uname = get_user_name(uid)
    txt = event.message.text.strip()
    app_uri = f"{RENDER_BASE_URL}/reader_app?openExternalBrowser=1"

    try:
        if txt == "每日金句":
            b = random.choice(CLASSIC_LIBRARY)
            msg = (
                f"🎲【今日經典金句靈感】\n\n"
                f"{b.get('quote','')}\n"
                f"—— {b.get('author','')}《{b.get('title','')}》\n\n"
                f"📖 點擊進入典藏書房閱讀完整深度長文：\n{app_uri}"
            )
            card = make_reading_salon_card()
            line_bot_api.reply_message(event.reply_token, [
                TextSendMessage(text=msg),
                FlexSendMessage(alt_text="📚 典藏書房 ＆ 深度長文閱讀館", contents=card)
            ])
            return

        if txt == "經典書單":
            lines = ["📚【典藏書房・精選經典書單與深度長文】"]
            for idx, b in enumerate(CLASSIC_LIBRARY, 1):
                lines.append(f"\n{idx}. {b.get('title','')}（{b.get('read_min','')}）\n   ✍️ {b.get('author','')}")
            lines.append(f"\n📖 點擊開啟全螢幕護眼閱讀器（支援語音聽書）：\n{app_uri}")
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="\n".join(lines)))
            return

        if txt in ["財富思維", "心理人生", "習慣效率"]:
            cat_key = "財富" if "財富" in txt else ("心理" if "心理" in txt else "習慣")
            matched = [b for b in CLASSIC_LIBRARY if cat_key in b.get("cat", "")]
            b = next(iter(matched), CLASSIC_LIBRARY[0])
            msg = (
                f"📖【{b.get('cat','')}精選長文搶先讀】\n"
                f"{b.get('title','')}\n"
                f"✍️ {b.get('author','')}\n\n"
                f"{b.get('quote','')}\n\n"
                f"👉 點擊展開完整精讀長文與語音聽書：\n{app_uri}"
            )
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
            return

        matched_book = [b for b in CLASSIC_LIBRARY if any(k in txt for k in ["原子", "納瓦爾", "勇氣", "致富", "心流", "習慣"])]
        if matched_book:
            b = next(iter(matched_book), {})
            msg = (
                f"🔍 為您找到館藏經典：\n\n"
                f"📖 {b.get('title','')}\n"
                f"✍️ {b.get('author','')}（{b.get('read_min','')}）\n\n"
                f"{b.get('quote','')}\n\n"
                f"👉 立即開啟護眼閱讀器精讀全文：\n{app_uri}"
            )
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
            return

        card = make_reading_salon_card()
        line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="📚 典藏書房 ＆ 深度長文閱讀館", contents=card))
    except Exception as e:
        line_bot_api.push_message(uid, TextSendMessage(text=f"📚 書房小提示：{str(e)[:80]}"))
