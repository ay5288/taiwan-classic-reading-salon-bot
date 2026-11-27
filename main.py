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
        "id": "BK01", "cat": "習慣與效率", "read_min": "3 分鐘精讀", "title": "1. 《原子習慣》：每天進步 1%，一年後強大 37 倍的複利系統",
        "author": "詹姆斯・克利爾（James Clear）",
        "quote": "「你並不會上升到你目標的高度，你會墜落到你系統的水平。」",
        "content": "多數人之所以無法養成好習慣，是因為把焦點放在「設定宏大目標」，卻忽略了「設計日常系統」。《原子習慣》揭示了行為改變的四大法則：\n\n一、讓提示顯而易見：把想讀的書放在枕頭上，而不是收進書櫃深處；想多喝水就把水壺放在書桌正中央。環境設計永遠比意志力更可靠。\n二、讓吸引力增強：將「需要做的事」與「喜歡做的事」綁定，例如只有騎單車或散步時才允許自己聽最愛的 Podcast。\n三、讓行動輕而易舉（兩分鐘法則）：任何新習慣的開始都不要超過兩分鐘——「每晚讀書一小時」先縮減為「每晚翻開書讀兩頁」，先求有再求好。\n四、讓獎賞令人滿足：利用視覺化追蹤（如在日曆打勾或累積閱讀連勝天數），大腦會因為看見連續紀錄而產生強烈動力不願中斷。\n\n【今日行動清單】：今晚睡前把手機放在客廳充電，將一本好書放在床頭櫃上，只讀兩頁就好。",
        "url": BOOK_AFFILIATE_URL
    },
    {
        "id": "BK02", "cat": "財富與思維", "read_min": "4 分鐘精讀", "title": "2. 《納瓦爾寶典》：如何不靠運氣致富，打造睡覺時也能賺錢的槓桿",
        "author": "艾瑞克・喬根森（Eric Jorgenson）",
        "quote": "「追求財富，而不是金錢或地位。財富是指你在睡覺時仍能為你賺錢的資產。」",
        "content": "矽谷傳奇天使投資人納瓦爾（Naval Ravikant）指出，單純靠「出租自己的時間」永遠無法實現真正的財務自由，因為時間有上限且一旦停止工作收入就歸零。真正致富的核心公式是：\n\n一、培養「專長知識（Specific Knowledge）」：這是無法透過短期培訓班教會的技能，它通常源自你內心真正的熱情與好奇心。對你來說像在玩耍，對別人來說卻像苦工的事，就是你的專長。\n二、善用「無邊際複製成本的槓桿」：過去的槓桿需要資本或人力，但新時代最強大的槓桿是「程式碼（軟體工具）」與「自媒體內容（文章、知識庫）」。寫好一套工具或一篇深度好文，複製給一萬人或一百萬人閱讀的邊際成本幾乎為零。\n三、堅持「長期主義」：生命中所有的回報，無論是財富、人際關係還是知識，都來自複利效應。\n\n【今日行動清單】：寫下三件你做起來毫不費力、卻常被朋友請教的事，思考如何將它轉化為可複製的數位資產。",
        "url": BOOK_AFFILIATE_URL
    },
    {
        "id": "BK03", "cat": "心理與人生", "read_min": "3 分鐘精讀", "title": "3. 《被討厭的勇氣》：課題分離，斬斷 90% 人際內耗的阿德勒哲學",
        "author": "岸見一郎 ＆ 古賀史健",
        "quote": "「所有的煩惱，全都是人際關係的煩惱。而自由，就是被別人討厭的勇氣。」",
        "content": "我們之所以活得疲憊，往往是因為背負了太多「不屬於自己的課題」。阿德勒心理學提出最核心的解藥——「課題分離」：\n\n一、區分「這是誰的課題」：判斷標準非常簡單——「這件事最終的後果由誰承擔？」例如：你認真寫出一篇真誠的文章，別人喜不喜歡、會不會批評，那是「別人的課題」，你無法控制；你唯一能控制的是「自己是否用心創作」。\n二、停止尋求所有人的認可：如果你總是為了滿足別人的期待而活，等於把人生的方向盤交給他人。當你擁有「被討厭的勇氣」時，才真正獲得了做自己的自由。\n三、活在「此時此刻」：人生不是一條必須爬到山頂才算成功的線，而是一連串「當下」的點。把聚光燈照在眼前的這一刻，專注做好手邊的事，過去與未來的焦慮自然消散。\n\n【今日行動清單】：遇到讓你焦慮的人際瑣事時，在心裡默念一句：「這是他的課題，不是我的課題。」",
        "url": BOOK_AFFILIATE_URL
    },
    {
        "id": "BK04", "cat": "財富與思維", "read_min": "4 分鐘精讀", "title": "4. 《致富心態》：留有餘裕與長尾效應，普通人也能贏過華爾街的秘密",
        "author": "摩根・豪澤爾（Morgan Housel）",
        "quote": "「財富就是你沒花掉的那些錢。真正的富有，是擁有掌控自己時間的自由。」",
        "content": "理財的成敗，往往不取決於你懂多少複雜的財務公式，而是取決於你的「行為與心態」：\n\n一、永遠為計畫預留「安全邊際（Room for Error）」：市場永遠會發生歷史上沒出現過的黑天鵝。不要把資金槓桿開到極限，留有足夠的緊急預備金，才能在暴跌時安穩睡覺，甚至逆勢撿便宜。\n二、理解「長尾效應」：世界上絕大多數的成功，都來自極少數幾次關鍵決策。巴菲特一生買過四百多支股票，但絕大部分財富只來自其中不到十支。允許自己犯錯、持續留在牌桌上，等待屬於你的長尾爆發。\n三、明確知道「什麼叫做足夠」：不要為了追求自己不需要的東西，去冒險賭上自己絕對不能失去的東西（家人、健康與平靜）。\n\n【今日行動清單】：檢視自己的資產配置，確保手邊永遠留有一筆能讓自己從容應對突發狀況的現金安全墊。",
        "url": BOOK_AFFILIATE_URL
    },
    {
        "id": "BK05", "cat": "習慣與效率", "read_min": "3 分鐘精讀", "title": "5. 《心流（Flow）》：如何在資訊爆炸時代，進入忘我且高產出的巔峰狀態",
        "author": "米哈里・契克森米哈伊",
        "quote": "「一個人最美好的時刻，往往發生在身體或心智為了完成某件有挑戰性的事而發揮到極限之時。」",
        "content": "滑短影音雖然帶來短暫的多巴胺刺激，結束後卻常讓人感到空虛疲憊；唯有進入「心流（Flow）」狀態，才能帶來深層的幸福感與自我實現：\n\n一、挑戰與技能的黃金平衡：當任務太簡單時，人會感到無聊；當任務太難時，人會感到焦慮。將難度設定在「比你現有能力高出 10%」的位置，最容易觸發心流。\n二、單一任務與零干擾環境：大腦每次被手機通知打斷，平均需要 15 分鐘才能重新找回深度專注。設定一個 45 分鐘的「免打擾番茄鐘」，關閉所有彈窗，全神貫注只做一件事。\n三、即時反饋機制：無論是寫程式看到畫面成功跑出來、騎單車看到碼表里程推進，還是閱讀完一篇長文，清晰的即時反饋會讓大腦自動鎖定專注。\n\n【今日行動清單】：現在就深呼吸三次，在接下來的 25 分鐘內不看任何通知，專心完成一件最重要的事。",
        "url": BOOK_AFFILIATE_URL
    },
    {
        "id": "BK06", "cat": "思維與決策", "read_min": "4 分鐘精讀", "title": "6. 《思考，快與慢》：避開大腦偏誤，做重要決定前必看的雙系統法則",
        "author": "丹尼爾・康納曼（Daniel Kahneman）",
        "quote": "「我們的大腦太容易對眼前的少量資訊下結論，卻忽略了背後龐大的基礎機率。」",
        "content": "諾貝爾經濟學獎得主康納曼將人類大腦的運作分為「系統一（快思考：直覺、情緒、自動化）」與「系統二（慢思考：理性、邏輯、需要耗費精力）」。\n\n一、警惕「錨定效應」：當我們走進商店看到一件標價三千元的衣服打折變一千五，系統一會覺得賺到了；但若它原本只值八百元，我們就掉進了價格錨點陷阱。做任何投資或購物決策前，先問自己：「如果沒有這個原價標籤，我願意花多少錢買它？」\n二、克服「損失規避心理」：人類失去一千元所感受到的痛苦，是撿到一千元快樂的兩倍以上。這導致投資人常常「賺一點就急著跑、賠錢卻死抱不放」。\n三、啟動「事前驗屍法」：在啟動重大計畫前，假設一年後這件事徹底失敗了，請團隊寫下所有可能的失敗原因，提前把漏洞補起來。\n\n【今日行動清單】：遇到重大消費或投資衝動時，強制讓自己等待 24 小時，喚醒理性的系統二再做決定。",
        "url": BOOK_AFFILIATE_URL
    },
    {
        "id": "BK07", "cat": "習慣與效率", "read_min": "3 分鐘精讀", "title": "7. 《深度工作力》：在分心時代，用每天 3 小時高濃度專注贏過所有人",
        "author": "卡爾・紐波特（Cal Newport）",
        "quote": "「高質量的產出 ＝ 花費的時間 × 專注的強度。」",
        "content": "在社群訊息與短影音無孔不入的今天，「能夠長時間保持高強度專注」已經成為職場與創業最稀缺的超能力。\n\n一、戒除「低價值淺薄工作」：整天忙著回覆無關緊要的訊息、頻繁切換視窗，會產生嚴重的「注意力殘留」，讓大腦智商暫時下降。\n二、建立「儀式感進入深度工作」：固定每天早上精神最好的 90 分鐘（例如 08:30 到 10:00），把手機調成飛航模式並放進抽屜，泡一杯熱咖啡，只攻克最核心的難題。\n三、設定「下班關機儀式」：每天傍晚完成工作後，說一句「今日工作結束」，徹底讓大腦切換到運動、閱讀與陪伴家人的休息模式，隔天才能再次滿血輸出。\n\n【今日行動清單】：明天早上打開手機看社群動態前，先完成 60 分鐘不被打擾的深度專注任務。",
        "url": BOOK_AFFILIATE_URL
    },
    {
        "id": "BK08", "cat": "心理與人生", "read_min": "3 分鐘精讀", "title": "8. 《沉思錄》：羅馬帝王的斯多葛智慧，在混亂世界中保持內心如山般平靜",
        "author": "馬可・奧理略（Marcus Aurelius）",
        "quote": "「你擁有掌控自己內心的力量，而非外界的事件。領悟這一點，你就會找到力量。」",
        "content": "身為羅馬帝國權力最大的皇帝，奧理略每天面對瘟疫、戰爭與背叛，卻在軍營帳篷裡寫下了流傳兩千年的心靈修煉指南。\n\n一、控制二分法：世上所有的事情只分為兩種——「我們能控制的（自己的念頭、態度與行動）」與「我們無法控制的（天氣、市場波動、別人的嘴）」。把 100% 的精力放在能控制的事上，對無法控制的事泰然處之。\n二、把障礙變成道路：阻礙行動的事物，本身就會成為推動行動的契機。遇到突發挫折時，不要抱怨「為什麼是我」，而是問「這件事能教會我什麼新能力？」\n三、向死而生（Memento Mori）：時刻提醒自己生命有限，你就不會再為了雞毛蒜皮的小事生氣，而會把愛與時間留給真正重要的人。\n\n【今日行動清單】：今天遇到塞車、下雨或計畫變動時，微笑接受它，把這段多出來的時間用來聽一篇好書。",
        "url": BOOK_AFFILIATE_URL
    },
    {
        "id": "BK09", "cat": "人際與溝通", "read_min": "3 分鐘精讀", "title": "9. 《人性的弱點》：不批評、不指責，讓所有人自然喜歡與你合作的溝通藝術",
        "author": "戴爾・卡內基（Dale Carnegie）",
        "quote": "「如果你想採集蜂蜜，就不要去踢翻蜂巢。」",
        "content": "無論科技如何演變，人性的底層渴望從未改變——每個人都渴望被重視、被理解與被真誠欣賞。\n\n一、永遠不要直接批評或指責別人：批評只會讓對方立刻啟動防禦機制並為自己辯護，無法真正改變對方的行為。改用「先肯定對方的優點，再溫和提出建議」的方式，效果高出十倍。\n二、真誠地對別人感興趣：想在兩個月內交到好朋友，最快的方法是「真誠地關心別人、傾聽對方的故事」，而不是整天試圖讓別人對你感興趣。記住對方的名字並多聊對方擅長的領域。\n三、站在對方的角度思考（同理心）：在開口說服別人之前，先問自己：「這件事對他有什麼好處？他真正需要的是什麼？」當你幫別人解決了痛點，成交與合作就會水到渠成。\n\n【今日行動清單】：今天與家人、同事或客戶對話時，練習給出一個具體且真誠的讚美。",
        "url": BOOK_AFFILIATE_URL
    },
    {
        "id": "BK10", "cat": "財富與思維", "read_min": "4 分鐘精讀", "title": "10. 《富爸爸，窮爸爸》：分清資產與負債，讓錢每天 24 小時為你工作",
        "author": "羅伯特・清崎（Robert Kiyosaki）",
        "quote": "「富人買入資產，窮人只有支出，中產階級買入他們以為是資產的負債。」",
        "content": "這本改變全球數千萬人財商觀念的經典，用最白話的一句話定義了什麼是真正的「資產」與「負債」：\n\n一、資產就是「把錢放進你口袋裡的東西」：例如能產生穩定股息的優質 ETF、收租房產、或是能持續帶來自動分潤與訂閱收入的數位系統與版權。\n二、負債就是「把錢從你口袋裡拿走的東西」：例如會隨時間貶值且需要高額保養費的豪華車貸、衝動刷卡買下卻只穿一次的衣物。\n三、先支付給自己：每個月領到薪水或營收的第一時間，先撥出 15%～20% 買入能生錢的資產，剩下的錢才用來支付生活開銷。當你的「被動資產現金流」大於「每月生活總支出」時，你就擁有了真正的人生選擇權。\n\n【今日行動清單】：拿出一張紙列出你目前的每一筆開銷，分辨哪些是會生錢的資產，哪些是消耗現金的負債。",
        "url": BOOK_AFFILIATE_URL
    }
]
def fetch_daily_articles():
    try:
        today = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
        u = f"https://wikipedia.org{today.year}/{today.month:02d}/{today.day:02d}"
        headers = {"User-Agent": "ClassicReadingSalonBot/2.5"}
        j = requests.get(u, headers=headers, timeout=6).json()
        tfa = j.get("tfa", {})
        t_title = tfa.get("titles", {}).get("normalized", "")
        t_ext = tfa.get("extract", "")
        t_url = tfa.get("content_urls", {}).get("mobile", {}).get("page", BOOK_AFFILIATE_URL)
        if t_title and t_ext and not any(t_title in x.get("title", "") for x in CLASSIC_LIBRARY):
            CLASSIC_LIBRARY.insert(0, {
                "id": f"WK0_{today.strftime('%m%d')}",
                "cat": "今日精選長文",
                "read_min": f"{max(2, round(len(t_ext)/300))} 分鐘精讀",
                "title": f"【今日深度百科】{t_title}",
                "author": "全球百科知識庫・每日特色長文",
                "quote": f"「{t_ext[:68]}……」",
                "content": t_ext + "\n\n【閱讀延伸】：知識的複利來自每天保持好奇心，點擊下方「語音聽書」可聆聽完整台灣中文語音朗讀。",
                "url": t_url
            })
        most_list = j.get("mostread", {}).get("articles", [])
        added_cnt = 0
        for art in most_list:
            if added_cnt >= 9:
                break
            atitle = art.get("titles", {}).get("normalized", "")
            aext = art.get("extract", "")
            aurl = art.get("content_urls", {}).get("mobile", {}).get("page", BOOK_AFFILIATE_URL)
            if atitle and len(aext) >= 60 and "Wikipedia" not in atitle and not any(atitle in x.get("title", "") for x in CLASSIC_LIBRARY):
                added_cnt += 1
                CLASSIC_LIBRARY.insert(0, {
                    "id": f"WK{added_cnt}_{today.strftime('%m%d')}",
                    "cat": "今日精選長文",
                    "read_min": f"{max(2, round(len(aext)/300))} 分鐘精讀",
                    "title": f"【今日熱讀 #{added_cnt}】{atitle}",
                    "author": "全球熱讀深度百科・每日自動收錄",
                    "quote": f"「{aext[:68]}……」",
                    "content": aext + "\n\n【閱讀延伸】：本篇為今日全球華語讀者最關注的深度知識條目，支援一鍵台灣中文語音朗讀與連續連播。",
                    "url": aurl
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
    return {"status": "Online", "service": "Taiwan Classic Reading Salon & Audio Reader Pro 2.5"}

@app.post("/api/article_add")
async def web_article_add(
    cat: str = Form("習慣與效率"),
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
        "cat": cat.strip() or "習慣與效率",
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
    fetch_daily_articles()
    S = chr(47)
    books_json = json.dumps(CLASSIC_LIBRARY, ensure_ascii=False)
    total_articles = len(CLASSIC_LIBRARY)
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
      .toc-box {{ background: #FFFDF9; border: 1px solid rgba(139, 108, 66, 0.24); border-radius: 18px; padding: 14px; margin-bottom: 14px; }}
      body.dark .toc-box {{ background: #25211D; border-color: rgba(212, 175, 55, 0.22); }}
      .toc-item {{ display: block; padding: 6px 0; font-size: 13px; color: #1E3A2F; text-decoration: none; border-bottom: 1px dashed rgba(139, 108, 66, 0.18); font-weight: 700; cursor: pointer; }}
      body.dark .toc-item {{ color: #E5C158; }}
      .chips {{ display: flex; gap: 8px; overflow-x: auto; padding-bottom: 12px; scrollbar-width: none; }}
      .chip {{ white-space: nowrap; background: #EFE9DC; border: 1px solid rgba(139, 108, 66, 0.25); color: #5C4938; padding: 7px 14px; border-radius: 20px; font-size: 12px; font-weight: 700; cursor: pointer; font-family: -apple-system, sans-serif; }}
      .chip.active {{ background: #1E3A2F; border-color: #D4AF37; color: #F7F3EA; }}
      body.dark .chip {{ background: #2A2520; color: #C8BBAE; }}
      body.dark .chip.active {{ background: #D4AF37; color: #1B1815; }}
      .book-card {{ background: #FFFDF9; border: 1px solid rgba(139, 108, 66, 0.22); border-radius: 20px; padding: 18px; margin-bottom: 16px; box-shadow: 0 6px 20px rgba(44, 36, 30, 0.06); }}
      body.dark .book-card {{ background: #25211D; border-color: rgba(212, 175, 55, 0.2); }}
      .quote-box {{ background: #F4EFE4; border-left: 3px solid #B8860B; padding: 10px 12px; border-radius: 8px; font-size: 13px; color: #4A3B2C; margin: 10px 0; line-height: 1.6; font-style: italic; }}
      body.dark .quote-box {{ background: #1E1A17; color: #D8CBB8; border-left-color: #E5C158; }}
      .full-article {{ font-size: 16px; line-height: 1.92; white-space: pre-line; margin-top: 12px; padding-top: 12px; border-top: 1px dashed rgba(139, 108, 66, 0.28); letter-spacing: 0.4px; }}
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
      <h1>📚 典藏書房（共 {total_articles} 篇長文）</h1>
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
          <span style="font-size:12px;color:#E5C158;font-weight:800;">🕯️ 每日自動蒐集 10 篇新文章 ＋ 10 篇經典</span>
          <span id="read-stat" style="font-size:11px;background:rgba(212,175,55,0.2);color:#F7F3EA;padding:3px 10px;border-radius:12px;font-weight:700;">已聽讀 0 篇</span>
        </div>
        <div style="font-size:15px;font-weight:900;margin-top:8px;line-height:1.5;">打開即讀完整長文 · 全館 20 篇文章皆支援「台灣中文語音朗讀」與「有聲書連續連播」！</div>
        <div class="btn-row" style="margin-top:10px;">
          <button type="button" class="btn btn-gold" id="radio-btn" onclick="toggleRadio()">📻 全館有聲書連續朗讀</button>
          <button type="button" class="btn btn-paper" style="max-width:110px;" id="rate-btn" onclick="cycleRate()">🎚️ 1.0x 語速</button>
        </div>
      </div>

      <div class="toc-box">
        <div style="font-size:13px;font-weight:900;color:#1E3A2F;margin-bottom:6px;">📑 本期館藏全文快速跳轉目錄（點擊直達該篇）：</div>
        <div id="toc-list" style="max-height:150px;overflow-y:auto;"></div>
      </div>

      <input id="search-in" class="field" placeholder="🔍 搜尋書名、今日熱讀關鍵字或作者..." oninput="renderBooks()" style="margin-bottom:10px;"/>

      <div class="chips">
        <div class="chip active" onclick="filterCat('all', this)">📚 全部 ({total_articles} 篇全文)</div>
        <div class="chip" onclick="filterCat('今日精選長文', this)">🆕 今日自動蒐集 (10篇)</div>
        <div class="chip" onclick="filterCat('習慣與效率', this)">⏳ 習慣與效率</div>
        <div class="chip" onclick="filterCat('財富與思維', this)">💎 財富與思維</div>
        <div class="chip" onclick="filterCat('心理與人生', this)">🌿 心理與人生</div>
      </div>
      <div id="book-box"></div>
    </div></div>

    <div id="page-notes" class="page"><div class="wrap">
      <div class="book-card">
        <div style="font-size:17px;font-weight:900;color:#1E3A2F;margin-bottom:4px;">🔖 我的隨身金句與閱讀靈感筆記</div>
        <input id="note-title" class="field" placeholder="📖 書名或文章出處"/>
        <textarea id="note-quote" class="field" rows="3" placeholder="✍️ 寫下觸動你的金句或心得..."></textarea>
        <button type="button" class="btn btn-emerald" style="width:100%;margin-top:10px;padding:12px;" onclick="saveManualNote()">💾 存入我的雲端書摘筆記本</button>
      </div>
      <div id="notes-list"></div>
    </div></div>

    <div id="page-add" class="page"><div class="wrap">
      <div class="book-card">
        <div style="font-size:17px;font-weight:900;color:#1E3A2F;margin-bottom:4px;">➕ 投稿收錄經典好書或深度長文</div>
        <form action="{S}api{S}article_add" method="post">
          <select name="cat" class="field">
            <option value="今日精選長文">🆕 今日精選長文</option>
            <option value="習慣與效率">⏳ 習慣與效率</option>
            <option value="財富與思維">💎 財富與思維</option>
            <option value="心理與人生">🌿 心理與人生</option>
          </select>
          <input name="title" class="field" placeholder="📚 文章標題" required/>
          <input name="author" class="field" placeholder="✍️ 作者姓名" value="典藏書房嚴選"/>
          <input name="quote" class="field" placeholder="💡 核心金句摘要" required/>
          <textarea name="content" class="field" rows="5" placeholder="📜 貼上完整長文內容（自動支援台灣中文語音朗讀）..." required></textarea>
          <input name="url" class="field" placeholder="🔗 相關購書或延伸連結（選填）"/>
          <button type="submit" class="btn btn-emerald" style="width:100%;margin-top:12px;padding:14px;">📖 立即上架並加入語音連播</button>
        </form>
      </div>
    </div></div>

    <div class="tabbar">
      <div class="tab active" onclick="switchTab('lib', this)">📚 20篇全文與聽書</div>
      <div class="tab" onclick="switchTab('notes', this)">🔖 靈感書摘本</div>
      <div class="tab" onclick="switchTab('add', this)"><span class="tab-cta">➕ 收錄好文</span></div>
    </div>
    <script>
      const BOOKS = {books_json};
      let curCat = 'all', fontSize = 16, speakingIdx = -1, radioMode = false, speechRate = 1.0;

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
        if (rbtn) rbtn.innerText = '📻 全館有聲書連續朗讀';
        document.querySelectorAll('.tts-single-btn').forEach(b => b.innerText = '🎧 語音聽書');
      }}

      function playBookAt(idx, autoNext) {{
        if (!('speechSynthesis' in window)) {{ alert('此瀏覽器不支援中文語音朗讀'); return; }}
        window.speechSynthesis.cancel();
        if (idx >= BOOKS.length) {{ stopAllSpeech(); return; }}
        const b = BOOKS[idx];
        speakingIdx = idx;
        radioMode = autoNext;
        document.querySelectorAll('.tts-single-btn').forEach(btn => btn.innerText = '🎧 語音聽書');
        const curBtn = document.getElementById('tts-btn-' + idx);
        if (curBtn) curBtn.innerText = '⏹️ 停止朗讀';
        const rbtn = document.getElementById('radio-btn');
        if (rbtn) rbtn.innerText = autoNext ? `⏹️ 連播中 (${{idx+1}}/${{BOOKS.length}})` : '📻 全館有聲書連續朗讀';
        const utter = new SpeechSynthesisUtterance(b.title + '。' + b.quote + '。' + b.content);
        utter.lang = 'zh-TW';
        utter.rate = speechRate;
        utter.onend = () => {{
          markDoneById(b.id);
          if (radioMode && idx + 1 < BOOKS.length) {{
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
        document.getElementById('toc-list').innerHTML = BOOKS.map((b, idx) =>
          `<div class="toc-item" onclick="jumpToBook(${{idx}})">📖 ${{idx + 1}}. ${{b.title}} <span style="color:#B8860B;font-size:11px;">(${{b.cat}})</span></div>`
        ).join('');
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
          return `<div id="book-card-${{idx}}" class="book-card">
            <div style="display:flex;justify-content:space-between;align-items:center;font-family:-apple-system,sans-serif;">
              <span style="font-size:11px;font-weight:800;background:#EFE9DC;color:#1E3A2F;padding:3px 10px;border-radius:10px;">${{b.cat}}</span>
              <span style="font-size:11px;color:#B8860B;font-weight:800;">⏱️ ${{b.read_min}}</span>
            </div>
            <div style="font-size:19px;font-weight:900;margin-top:8px;line-height:1.45;">${{b.title}}</div>
            <div style="font-size:12px;color:#6B5846;margin-top:4px;">✍️ ${{b.author}}</div>
            <div class="quote-box">${{b.quote}}</div>
            <div class="full-article" style="font-size:${{fontSize}}px;">${{b.content}}</div>
            <div class="btn-row">
              <button type="button" id="tts-btn-${{idx}}" class="btn btn-gold tts-single-btn" onclick="speakBook(${{idx}})">🎧 語音聽書</button>
              <button type="button" class="btn btn-paper" onclick="quickSaveQuote(${{idx}}, this)">🔖 收藏金句</button>
              <a class="btn btn-emerald" href="${{b.url}}" target="_blank">🛒 收藏好書</a>
            </div>
          </div>`;
        }}).join('');
      }}

      async function quickSaveQuote(idx, btn) {{
        const b = BOOKS[idx];
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
    first_book = next(iter(CLASSIC_LIBRARY), {})
    daily_title = str(first_book.get("title", "《原子習慣》深度精讀")) if isinstance(first_book, dict) else "《原子習慣》深度精讀"
    daily_quote = str(first_book.get("quote", "「你並不會上升到你目標的高度，你會墜落到你系統的水平。」")) if isinstance(first_book, dict) else "「閱讀讓靈魂更自由。」"

    share_msg = urllib.parse.quote(f"📚【典藏書房 ＆ 深度長文閱讀館】\n今日精選金句：{daily_quote}\n📖 打開即享 20 篇完整深度長文 ＋ 台灣中文語音聽書連播！\n👉 立即進入書房：\n{app_uri}")
    share_uri = f"https:{S}{S}line.me{S}R{S}share?text={share_msg}"

    bubble_1 = BubbleContainer(
        size="mega",
        header=BoxComponent(layout="vertical", background_color="#1E3A2F", padding_all="16px", contents=[
            TextComponent(text="📚 典藏書房 ＆ 深度長文閱讀館", weight="bold", size="md", color="#F7F3EA", wrap=True),
            TextComponent(text="每日10篇新長文 · 10大經典 · 中文語音連播", size="xs", color="#E5C158", weight="bold", wrap=True, margin="xs")
        ]),
        body=BoxComponent(layout="vertical", spacing="sm", background_color="#FFFDF9", contents=[
            TextComponent(text=f"📖 最新收錄：{daily_title}", size="xs", color="#1E3A2F", weight="bold", wrap=True),
            BoxComponent(layout="vertical", background_color="#F4EFE4", corner_radius="12px", padding_all="12px", contents=[
                TextComponent(text=daily_quote, size="xs", color="#4A3B2C", wrap=True)
            ])
        ]),
        footer=BoxComponent(layout="vertical", spacing="sm", background_color="#FFFDF9", contents=[
            ButtonComponent(style="primary", color="#1E3A2F", height="sm", action=URIAction(label="📖 開啟 20 篇全文 ＆ 中文語音聽書", uri=app_uri)),
            BoxComponent(layout="horizontal", spacing="sm", contents=[
                ButtonComponent(style="primary", color="#B8860B", height="sm", action=MessageAction(label="🎲 抽金句", text="每日金句")),
                ButtonComponent(style="secondary", height="sm", action=MessageAction(label="📚 看目錄", text="經典書單"))
            ]),
            BoxComponent(layout="horizontal", spacing="sm", contents=[
                ButtonComponent(style="secondary", height="sm", action=MessageAction(label="🆕 今日文", text="今日精選")),
                ButtonComponent(style="secondary", height="sm", action=MessageAction(label="💎 讀財富", text="財富思維"))
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
            TextComponent(text="👈 向左滑動返回「20 篇全文與中文語音聽書館」", size="xxs", color="#6B5846", weight="bold")
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
    fetch_daily_articles()
    card = make_reading_salon_card()
    line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="📚 典藏書房 ＆ 20 篇全文中文語音聽書館已啟動", contents=card))

@handler.add(MessageEvent, message=TextMessage)
def on_text(event):
    uid = event.source.user_id
    uname = get_user_name(uid)
    txt = event.message.text.strip()
    app_uri = f"{RENDER_BASE_URL}/reader_app?openExternalBrowser=1"
    fetch_daily_articles()

    try:
        if txt == "每日金句":
            b = random.choice(CLASSIC_LIBRARY)
            msg = (
                f"🎲【今日經典金句靈感】\n\n"
                f"{b.get('quote','')}\n"
                f"—— {b.get('author','')}《{b.get('title','')}》\n\n"
                f"📖 點擊開啟 20 篇全文與台灣中文語音聽書：\n{app_uri}"
            )
            card = make_reading_salon_card()
            line_bot_api.reply_message(event.reply_token, [
                TextSendMessage(text=msg),
                FlexSendMessage(alt_text="📚 典藏書房 ＆ 深度長文閱讀館", contents=card)
            ])
            return

        if txt in ["經典書單", "今日精選"]:
            target = [b for b in CLASSIC_LIBRARY if b.get("cat") == "今日精選長文"] if txt == "今日精選" else CLASSIC_LIBRARY
            if not target:
                target = CLASSIC_LIBRARY
            header = "🆕【今日自動蒐集 10 篇最新中文深度長文】" if txt == "今日精選" else f"📚【典藏書房・全館 {len(CLASSIC_LIBRARY)} 篇全文目錄】"
            lines = [header]
            for idx, b in enumerate(target[:12], 1):
                lines.append(f"\n{idx}. {b.get('title','')}（{b.get('read_min','')}）")
            lines.append(f"\n🎧 點擊進入全螢幕閱讀器，馬上全文閱讀＋中文語音連播：\n{app_uri}")
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
                f"👉 點擊展開完整精讀長文與台灣中文語音朗讀：\n{app_uri}"
            )
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
            return

        matched_book = [b for b in CLASSIC_LIBRARY if any(k in txt for k in ["原子", "納瓦爾", "勇氣", "致富", "心流", "思考", "深度", "沉思", "人性", "富爸爸"])]
        if matched_book:
            b = next(iter(matched_book), {})
            msg = (
                f"🔍 為您找到館藏經典：\n\n"
                f"📖 {b.get('title','')}\n"
                f"✍️ {b.get('author','')}（{b.get('read_min','')}）\n\n"
                f"{b.get('quote','')}\n\n"
                f"👉 立即開啟護眼閱讀器精讀全文＋語音聽書：\n{app_uri}"
            )
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
            return

        card = make_reading_salon_card()
        line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="📚 典藏書房 ＆ 深度長文閱讀館", contents=card))
    except Exception as e:
        line_bot_api.push_message(uid, TextSendMessage(text=f"📚 書房小提示：{str(e)[:80]}"))
