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

# 軌道 A：每日自動蒐集的新文章（由 API 動態抓取 ＋ 保底補滿 10 篇，永遠滿載）
DAILY_FRESH_ARTICLES = []

# 軌道 B：傳世經典長文原典館（10 篇千古名篇完整原文 ＋ 深度白話解析）
CLASSIC_LONG_ARTICLES = [
    {
        "id": "CL01", "track": "經典長文", "cat": "兵法謀略", "title": "1. 《孫子兵法・謀攻篇》完整原典與現代戰略深解",
        "author": "孫武（春秋時期）",
        "quote": "「故百戰百勝，非善之善者也；不戰而屈人之兵，善之善者也。」",
        "content": "【完整原典】\n孫子曰：凡用兵之法，全國為上，破國次之；全軍為上，破軍次之；全旅為上，破旅次之；全卒為上，破卒次之；全伍為上，破伍次之。是故百戰百勝，非善之善者也；不戰而屈人之兵，善之善者也。\n\n故上兵伐謀，其次伐交，其次伐兵，其下攻城。攻城之法，為不得已。修櫓轒轀，具器械，三月而後成；距闉，又三月而後已。將不勝其忿而蟻附之，殺士三分之一而城不拔者，此攻之災也。\n\n故善用兵者，屈人之兵而非戰也，拔人之城而非攻也，毀人之國而非久也，必以全爭於天下，故兵不頓而利可全，此謀攻之法也。\n\n故用兵之法，十則圍之，五則攻之，倍則分之，敵則能戰之，少則能逃之，不若則能避之。故小敵之堅，大敵之擒也。\n\n夫將者，國之輔也。輔周則國必強，輔隙則國必弱。故君之所以患於軍者三：不知軍之不可以進而謂之進，不知軍之不可以退而謂之退，是謂縻軍；不知三軍之事，而同三軍之政者，則軍士惑矣；不知三軍之權，而同三軍之任，則軍士疑矣。三軍既惑且疑，則諸侯之難至矣，是謂亂軍引勝。\n\n故知勝有五：知可以戰與不可以戰者勝，識眾寡之用者勝，上下同欲者勝，以虞待不虞者勝，將能而君不御者勝。此五者，知勝之道也。\n\n故曰：知彼知己，百戰不殆；不知彼而知己，一勝一負；不知彼，不知己，每戰必殆。\n\n【現代商業與人生深度解析】\n本篇核心在於「全勝思維」與「成本意識」。真正的頂尖決策者，不會把精力耗費在硬碰硬的價格戰或消耗戰（攻城），而是從更高維度的商業模式設計（伐謀）與跨界聯盟（伐交）解決問題。在投入任何重大專案前，務必以「知勝五事」檢視：時機是否成熟、資源配置是否得當、團隊目標是否一致、是否做好風險預案，以及授權是否充分。",
        "url": BOOK_AFFILIATE_URL
    },
    {
        "id": "CL02", "track": "經典長文", "cat": "山水散文", "title": "2. 蘇軾《前赤壁賦》完整原典與生命哲學賞析",
        "author": "蘇軾（北宋）",
        "quote": "「蓋將自其變者而觀之，則天地曾不能以一瞬；自其不變者而觀之，則物與我皆無盡也。」",
        "content": "【完整原典】\n壬戌之秋，七月既望，蘇子與客泛舟遊於赤壁之下。清風徐來，水波不興。舉酒屬客，誦明月之詩，歌窈窕之章。少焉，月出於東山之上，徘徊於斗牛之間。白露橫江，水光接天。縱一葦之所如，凌萬頃之茫然。浩浩乎如馮虛御風，而不知其所止；飄飄乎如遺世獨立，羽化而登仙。\n\n於是飲酒樂甚，扣舷而歌之。歌曰：「桂棹兮蘭槳，擊空明兮溯流光。渺渺兮予懷，望美人兮天一方。」客有吹洞簫者，倚歌而和之。其聲嗚嗚然，如怨如慕，如泣如訴，餘音嫋嫋，不絕如縷。舞幽壑之潛蛟，泣孤舟之嫠婦。\n\n蘇子愀然，正襟危坐而問客曰：「何為其然也？」客曰：「『月明星稀，烏鵲南飛』，此非曹孟德之詩乎？西望夏口，東望武昌，山川相繆，鬱乎蒼蒼，此非孟德之困於周郎者乎？方其破荊州，下江陵，順流而東也，舳艫千里，旌旗蔽空，釃酒臨江，橫槊賦詩，固一世之雄也，而今安在哉？況吾與子漁樵於江渚之上，侶魚蝦而友麋鹿，駕一葉之扁舟，舉匏樽以相屬。寄蜉蝣於天地，渺滄海之一粟。哀吾生之須臾，羨長江之無窮。挾飛仙以遨遊，抱明月而長終。知不可乎驟得，託遺響於悲風。」\n\n蘇子曰：「客亦知夫水與月乎？逝者如斯，而未嘗往也；盈虛者如彼，而卒莫消長也。蓋將自其變者而觀之，則天地曾不能以一瞬；自其不變者而觀之，則物與我皆無盡也，而又何羨乎！且夫天地之間，物各有主，苟非吾之所有，雖一毫而莫取。惟江上之清風，與山間之明月，耳得之而為聲，目遇之而成色，取之無禁，用之不竭，是造物者之無盡藏也，而吾與子之所共適。」\n\n客喜而笑，洗盞更酌。肴核既盡，杯盤狼藉。相與枕藉乎舟中，不知東方之既白。\n\n【哲學與心境深解】\n蘇軾在人生最低谷（烏臺詩案貶謫黃州）寫下此篇。面對歷史英雄的消逝與生命的短暫，他提出「變與不變」的雙重視角：若執著於外在名利與得失（變者），萬物瞬息萬變令人焦慮；若從宇宙運行與精神本質（不變者）來看，清風明月、內心平靜皆為無盡寶藏，無須羨慕外物，只需全心享受當下。",
        "url": BOOK_AFFILIATE_URL
    },
    {
        "id": "CL03", "track": "經典長文", "cat": "道家智慧", "title": "3. 老子《道德經》核心精選十章完整原典與處世心法",
        "author": "老子（春秋時期）",
        "quote": "「上善若水。水善利萬物而不爭，處眾人之所惡，故幾於道。」",
        "content": "【完整原典精編】\n第一章：道可道，非常道。名可名，非常名。無名天地之始；有名萬物之母。故常無欲，以觀其妙；常有欲，以觀其徼。此兩者，同出而異名，同謂之玄。玄之又玄，眾妙之門。\n\n第八章：上善若水。水善利萬物而不爭，處眾人之所惡，故幾於道。居善地，心善淵，與善仁，言善信，正善治，事善能，動善時。夫唯不爭，故無尤。\n\n第十二章：五色令人目盲；五音令人耳聾；五味令人口爽；馳騁畋獵，令人心發狂；難得之貨，令人行妨。是以聖人為腹不為目，故去彼取此。\n\n第三十三章：知人者智，自知者明。勝人者有力，自勝者強。知足者富。強行者有志。不失其所者久。死而不亡者壽。\n\n第六十三章：為無為，事無事，味無味。大小多少，報怨以德。圖難於其易，為大於其細；天下難事，必作於易，天下大事，必作於細。是以聖人終不為大，故能成其大。\n\n第六十四章：其安易持，其未兆易謀。其脆易泮，其微易散。為之於未有，治之於未亂。合抱之木，生於毫末；九層之臺，起於累土；千里之行，始於足下。\n\n【現代生活應用】\n《道德經》教導我們「減法哲學」與「積累智慧」：外在聲色資訊過多（五色、五音）只會消耗心神，回歸內在真實需求（為腹不為目）才能獲得寧靜；同時所有偉大的成就都始於微小的日常積累（合抱之木生於毫末），在問題尚未惡化前提前佈局（治之於未亂），便是最高明的處世之道。",
        "url": BOOK_AFFILIATE_URL
    },
    {
        "id": "CL04", "track": "經典長文", "cat": "忠義名表", "title": "4. 諸葛亮《出師表》完整原典與領導者擔當深解",
        "author": "諸葛亮（三國蜀漢）",
        "quote": "「受任於敗軍之際，奉命於危難之間，爾來二十有一年矣。」",
        "content": "【完整原典】\n先帝創業未半而中道崩殂，今天下三分，益州疲弊，此誠危急存亡之秋也。然侍衛之臣不懈於內，忠志之士忘身於外者，蓋追先帝之殊遇，欲報之於陛下也。誠宜開張聖聽，以光先帝遺德，恢弘志士之氣，不宜妄自菲薄，引喻失義，以塞忠諫之路也。\n\n宮中府中，俱為一體，陟罰臧否，不宜異同。若有作姦犯科及為忠善者，宜付有司論其刑賞，以昭陛下平明之理，不宜偏私，使內外異法也。\n\n侍中、侍郎郭攸之、費禕、董允等，此皆良實，志慮忠純，是以先帝簡拔以遺陛下。愚以為宮中之事，事無大小，悉以咨之，然後施行，必能裨補闕漏，有所廣益。將軍向寵，性行淑均，曉暢軍事，試用於昔日，先帝稱之曰能，是以眾議舉寵為督。愚以為營中之事，悉以咨之，必能使行陣和睦，優劣得所。\n\n親賢臣，遠小人，此先漢所以興隆也；親小人，遠賢臣，此後漢所以傾頹也。先帝在時，每與臣論此事，未嘗不歎息痛恨於桓、靈也。侍中、尚書、長史、參軍，此悉貞良死節之臣，願陛下親之信之，則漢室之隆，可計日而待也。\n\n臣本布衣，躬耕於南陽，苟全性命於亂世，不求聞達於諸侯。先帝不以臣卑鄙，猥自枉屈，三顧臣於草廬之中，咨臣以當世之事，由是感激，遂許先帝以驅馳。後值傾覆，受任於敗軍之際，奉命於危難之間，爾來二十有一年矣。\n\n先帝知臣謹慎，故臨崩寄臣以大事也。受命以來，夙夜憂歎，恐託付不效，以傷先帝之明，故五月渡瀘，深入不毛。今南方已定，兵甲已足，當獎率三軍，北定中原，庶竭駑鈍，攘除姦凶，興復漢室，還於舊都。此臣所以報先帝而忠陛下之職分也。至於斟酌損益，進盡忠言，則攸之、禕、允之任也。\n\n願陛下託臣以討賊興復之效；不效，則治臣之罪，以告先帝之靈。若無興德之言，則責攸之、禕、允等之慢，以彰其咎；陛下亦宜自謀，以咨諏善道，察納雅言，深追先帝遺詔。臣不勝受恩感激。今當遠離，臨表涕零，不知所言。\n\n【現代組織與領導深解】\n《出師表》是一份頂級的「組織交接與治理說明書」。諸葛亮在出征前清晰劃分了「宮中（行政幕僚）」與「營中（前線作戰）」的權責邊界，建立賞罰分明的制度，並為年輕領導者建立核心智囊團。",
        "url": BOOK_AFFILIATE_URL
    },
    {
        "id": "CL05", "track": "經典長文", "cat": "家國胸懷", "title": "5. 范仲淹《岳陽樓記》完整原典與逆境心境賞析",
        "author": "范仲淹（北宋）",
        "quote": "「不以物喜，不以己悲；居廟堂之高則憂其民，處江湖之遠則憂其君。」",
        "content": "【完整原典】\n慶曆四年春，滕子京謫守巴陵郡。越明年，政通人和，百廢具興。乃重修岳陽樓，增其舊制，刻唐賢今人詩賦於其上。屬予作文以記之。\n\n予觀夫巴陵勝狀，在洞庭一湖。銜遠山，吞長江，浩浩湯湯，橫無際涯；朝暉夕陰，氣象萬千。此則岳陽樓之大觀也，前人之述備矣。然則北通巫峽，南極瀟湘，遷客騷人，多會於此，覽物之情，得無異乎？\n\n若夫霪雨霏霏，連月不開，陰風怒號，濁浪排空；日星隱曜，山岳潛形；商旅不行，檣傾楫摧；薄暮冥冥，虎嘯猿啼。登斯樓也，則有去國懷鄉，憂讒畏譏，滿目蕭然，感極而悲者矣。\n\n至若春和景明，波瀾不驚，上下天光，一碧萬頃；沙鷗翔集，錦鱗游泳；岸芷汀蘭，郁郁青青。而或長煙一空，皓月千里，浮光躍金，靜影沉璧，漁歌互答，此樂何極！登斯樓也，則有心曠神怡，寵辱偕忘，把酒臨風，其喜洋洋者矣。\n\n嗟夫！予嘗求古仁人之心，或異二者為之，何哉？不以物喜，不以己悲；居廟堂之高則憂其民，處江湖之遠則憂其君。是進亦憂，退亦憂。然則何時而樂耶？其必曰「先天下之憂而憂，後天下之樂而樂」乎！噫！微斯人，吾誰與歸？時六年九月十五日。\n\n【現代情緒管理深解】\n一般人的情緒極易被外在天氣與順逆境左右：雨天悲傷、晴天狂喜。范仲淹提出「不以物喜，不以己悲」的高維心態——不因外在短期波動而過度亢奮，也不因一時挫折而陷入絕望，把內心的穩定錨定在長遠的價值與責任之上。",
        "url": BOOK_AFFILIATE_URL
    },
    {
        "id": "CL06", "track": "經典長文", "cat": "理想家園", "title": "6. 陶淵明《桃花源記》完整原典與心靈避風港深解",
        "author": "陶淵明（東晉）",
        "quote": "「土地平曠，屋舍儼然，有良田美池桑竹之屬。阡陌交通，雞犬相聞。」",
        "content": "【完整原典】\n晉太元中，武陵人捕魚為業。緣溪行，忘路之遠近。忽逢桃花林，夾岸數百步，中無雜樹，芳草鮮美，落英繽紛。漁人甚異之，復前行，欲窮其林。\n\n林盡水源，便得一山，山有小口，彷彿若有光。便捨船，從口入。初極狹，纔通人。復行數十步，豁然開朗。土地平曠，屋舍儼然，有良田美池桑竹之屬。阡陌交通，雞犬相聞。其中往來種作，男女衣著，悉如外人。黃髮垂髫，並怡然自樂。\n\n見漁人，乃大驚，問所從來。具答之。便要還家，設酒殺雞作食。村中聞有此人，咸來問訊。自雲先世避秦時亂，率妻子邑人來此絕境，不復出焉，遂與外人間隔。問今是何世，乃不知有漢，無論魏晉。此人一一為具言所聞，皆歎惋。餘人各復延至其家，皆出酒食。停數日，辭去。此中人語雲：「不足為外人道也。」\n\n既出，得其船，便扶向路，處處誌之。及郡下，詣太守，說如此。太守即遣人隨其往，尋向所誌，遂迷，不復得路。南陽劉子驥，高尚士也，聞之，欣然規往。未果，尋病終。後遂無問津者。\n\n【現代生活啟示】\n每個人在繁忙的都市生活中，都需要一座屬於自己的「桃花源」——可能是清晨騎單車迎風的河濱車道、深夜泡一杯熱茶獨處的書房，或是遠離社群喧囂的兩小時閱讀時光。心境一旦寧靜，處處皆是桃花源。",
        "url": BOOK_AFFILIATE_URL
    },
    {
        "id": "CL07", "track": "經典長文", "cat": "生命哲思", "title": "7. 王羲之《蘭亭集序》完整原典與珍惜當下深解",
        "author": "王羲之（東晉）",
        "quote": "「後之視今，亦猶今之視昔，悲夫！」",
        "content": "【完整原典】\n永和九年，歲在癸丑，暮春之初，會於會稽山陰之蘭亭，修禊事也。群賢畢至，少長鹹集。此地有崇山峻嶺，茂林修竹，又有清流激湍，映帶左右，引以為流觴曲水，列坐其次。雖無絲竹管弦之盛，一觴一詠，亦足以暢敘幽情。\n\n是日也，天朗氣清，惠風和暢。仰觀宇宙之大，俯察品類之盛，所以遊目騁懷，足以極視聽之娛，信可樂也。\n\n夫人之相與，俯仰一世。或取諸懷抱，悟言一室之內；或因寄所託，放浪形骸之外。雖趣舍萬殊，靜躁不同，當其欣於所遇，暫得於己，快然自足，不知老之將至；及其所之既倦，情隨事遷，感慨係之矣。向之所欣，俯仰之間，已為陳跡，猶不能不以之興懷，況修短隨化，終期於盡！古人雲：「死生亦大矣。」豈不痛哉！\n\n每覽昔人興感之由，若合一契，未嘗不臨文嗟悼，不能喻之於懷。固知一死生為虛誕，齊彭殤為妄作。後之視今，亦猶今之視昔，悲夫！故列敘時人，錄其所述，雖世殊事異，所以興懷，其致一也。後之覽者，亦將有感於斯文。\n\n【哲學深解】\n王羲之在最歡樂的春日雅集中，敏銳察覺到「歡樂短暫、時光流逝」的本質，卻並不消極頹廢，而是透過書寫與紀錄，讓當下的感動跨越千年與後世讀者產生共鳴。",
        "url": BOOK_AFFILIATE_URL
    },
    {
        "id": "CL08", "track": "經典長文", "cat": "求學師道", "title": "8. 韓愈《師說》完整原典與終身學習心法",
        "author": "韓愈（唐代）",
        "quote": "「聞道有先後，術業有專攻，如是而已。」",
        "content": "【完整原典】\n古之學者必有師。師者，所以傳道受業解惑也。人非生而知之者，孰能無惑？惑而不從師，其為惑也，終不解矣。\n\n生乎吾前，其聞道也固先乎吾，吾從而師之；生乎吾後，其聞道也亦先乎吾，吾從而師之。吾師道也，夫庸知其年之先後生於吾乎？是故無貴無賤，無長無少，道之所存，師之所存也。\n\n嗟乎！師道之不傳也久矣！欲人之無惑也難矣！古之聖人，其出人也遠矣，猶且從師而問焉；今之眾人，其下聖人也亦遠矣，而恥學於師。是故聖益聖，愚益愚。聖人之所以為聖，愚人之所以為愚，其皆出於此乎？\n\n愛其子，擇師而教之；於其身也，則恥師焉，惑矣。彼童子之師，授之書而習其句讀者，非吾所謂傳其道解其惑者也。句讀之不知，惑之不解，或師焉，或不焉，小學而大遺，吾未見其明也。\n\n巫醫樂師百工之人，不恥相師。士大夫之族，曰師曰弟子雲者，則群聚而笑之。問之，則曰：「彼與彼年相若也，道相似也，位卑則足羞，官盛則近諛。」嗚呼！師道之不復，可知矣。巫醫樂師百工之人，君子不齒，今其智乃反不能及，其可怪也歟！\n\n聖人無常師。孔子師郯子、萇弘、師襄、老聃。郯子之徒，其賢不及孔子。孔子曰：三人行，則必有我師。是故弟子不必不如師，師不必賢於弟子，聞道有先後，術業有專攻，如是而已。\n\n【現代終身學習啟示】\n在知識快速迭代的時代，放下年齡與頭銜的包袱，「道之所存，師之所存」——向任何領域比我們先一步掌握方法的人學習，正是保持持續成長的核心秘訣。",
        "url": BOOK_AFFILIATE_URL
    },
    {
        "id": "CL09", "track": "經典長文", "cat": "君子修養", "title": "9. 劉禹錫《陋室銘》＆ 周敦頤《愛蓮說》雙經典原典合輯",
        "author": "劉禹錫（唐）＆ 周敦頤（北宋）",
        "quote": "「山不在高，有仙則名；水不在深，有龍則靈。斯是陋室，惟吾德馨。」",
        "content": "【《陋室銘》完整原典】\n山不在高，有仙則名。水不在深，有龍則靈。斯是陋室，惟吾德馨。苔痕上階綠，草色入簾青。談笑有鴻儒，往來無白丁。可以調素琴，閱金經。無絲竹之亂耳，無案牘之勞形。南陽諸葛廬，西蜀子雲亭。孔子雲：何陋之有？\n\n【《愛蓮說》完整原典】\n水陸草木之花，可愛者甚蕃。晉陶淵明獨愛菊。自李唐來，世人甚愛牡丹。予獨愛蓮之出淤泥而不染，濯清漣而不妖，中通外直，不蔓不枝，香遠益清，亭亭淨植，可遠觀而不可褻玩焉。\n\n予謂菊，花之隱逸者也；牡丹，花之富貴者也；蓮，花之君子者也。噫！菊之愛，陶後鮮有聞。蓮之愛，同予者何人？牡丹之愛，宜乎眾矣！\n\n【現代精神富足深解】\n真正的富足不在於豪宅名車的外在堆砌，而在於內在精神的豐盈（惟吾德馨）與優質的社交圈（談笑有鴻儒）；在複雜的商業與社會環境中，保持「出淤泥而不染、中通外直」的原則，便能行穩致遠。",
        "url": BOOK_AFFILIATE_URL
    },
    {
        "id": "CL10", "track": "經典長文", "cat": "逍遙境界", "title": "10. 莊子《逍遙遊》核心篇章完整原典與格局突破深解",
        "author": "莊子（戰國時期）",
        "quote": "「水擊三千里，摶扶搖而上者九萬里，去以六月息者也。」",
        "content": "【完整原典精編】\n北冥有魚，其名為鯤。鯤之大，不知其幾千里也；化而為鳥，其名為鵬。鵬之背，不知其幾千里也；怒而飛，其翼若垂天之雲。是鳥也，海運則將徙於南冥。南冥者，天池也。《齊諧》者，志怪者也。《諧》之言曰：「鵬之徙於南冥也，水擊三千里，摶扶搖而上者九萬里，去以六月息者也。」\n\n野馬也，塵埃也，生物之以息相吹也。天之蒼蒼，其正色邪？其遠而無所至極邪？其視下也，亦若是則已矣。且夫水之積也不厚，則其負大舟也無力。覆杯水於坳堂之上，則芥為之舟，置杯焉則膠，水淺而舟大也。風之積也不厚，則其負大翼也無力。故九萬里，則風斯在下矣，而後乃今培風；背負青天，而莫之夭閼者，而後乃今將圖南。\n\n蜩與學鳩笑之曰：「我決起而飛，搶榆枋而止，時則不至，而控於地而已矣，奚以之九萬里而南為？」適莽蒼者，三餐而反，腹猶果然；適百里者，宿舂糧；適千里者，三月聚糧。之二蟲又何知！小知不及大知，小年不及大年。\n\n【現代格局與積累深解】\n莊子用「水淺而舟大」點破了所有成大事者的底層邏輯：沒有足夠深厚的知識、資本與能力積累（積水、積風），就無法承載巨大的機會（大舟、大翼）。不要與目光短淺的蜩與學鳩爭辯，只需默默積蓄九萬里的長風，時機一到自然扶搖直上。",
        "url": BOOK_AFFILIATE_URL
    }
]
FALLBACK_DAILY_ARTICLES = [
    {"title": "【今日深度長文 #1】睡眠科學與大腦膠淋巴排毒機制完整解析", "cat": "健康科學", "author": "今日知識精編", "quote": "「深度睡眠是大腦清除代謝廢物、鞏固長期記憶的黃金修復期。」", "content": "現代神經科學研究發現，人類大腦在進入深層非快速動眼睡眠（NREM）時，腦脊髓液的流動速度會大幅增加，透過「膠淋巴系統（Glymphatic System）」將白天清醒時累積的 β-類澱粉蛋白等神經代謝廢物沖刷排出。\n\n長期睡眠不足不僅會導致專注力下降與情緒波動，更會讓大腦處於慢性發炎狀態。要提升深度睡眠品質，專家建議三個核心習慣：第一，每天早上起床後 30 分鐘內接觸自然陽光 10 分鐘，校準生理時鐘與褪黑激素分泌節律；第二，下午兩點後避免攝取咖啡因；第三，睡前一小時調暗室內燈光並遠離高亮度螢幕，讓體溫自然微降，即可大幅縮短入睡時間並延長深睡比例。"},
    {"title": "【今日深度長文 #2】複利效應在知識、健康與財務中的底層運作", "cat": "思維模型", "author": "今日知識精編", "quote": "「複利是世界第八大奇蹟，了解它的人賺取它，不了解它的人支付它。」", "content": "複利之所以違反人類直覺，是因為它在前期的增長曲線極為平緩，甚至在頭幾年幾乎看不出與線性努力的差別；但一旦跨過臨界點，增長速度就會呈指數級爆發。\n\n在知識領域，每天精讀一篇深度長文並寫下一句心得，一年累積的認知模型將讓你看透多數人看不見的商業與人生規律；在健康領域，每週維持三次 45 分鐘的 Zone 2 有氧單車或快走，五年後的心肺機能與代謝年齡將遠勝同齡人；在財務領域，持續將現金流投入低成本寬基指數資產並讓股息再投入，時間便會成為你最忠實的合夥人。"},
    {"title": "【今日深度長文 #3】注意力經濟時代的資訊節食與深度思考", "cat": "數位生活", "author": "今日知識精編", "quote": "「當一項服務免費時，你的注意力就是被出售的商品。」", "content": "演算法推薦系統的設計初衷，是最大化用戶停留在螢幕上的時間，因此它天然偏好推送能引發憤怒、焦慮或即時感官刺激的碎片化內容。長期處於這種高頻資訊轟炸下，大腦的前額葉皮質會逐漸喪失耐心，變得難以閱讀超過一千字的完整文章。\n\n要奪回大腦的主導權，必須刻意練習「資訊節食」：關閉手機非必要的推播通知、每天保留一段完全不滑動態牆的「長文閱讀與聽書時段」，讓大腦重新習慣完整邏輯推演與系統性思考。"},
    {"title": "【今日深度長文 #4】第一性原理思維：打破經驗慣性的創新方法論", "cat": "創新思維", "author": "今日知識精編", "quote": "「不要用類比思維隨波逐流，要回到事物最底層的物理事實重新推演。」", "content": "大多數人在做決策時習慣使用「類比思維」——看別人怎麼做、行業過去怎麼做，我們就跟著微調。這種方式雖然安全，卻永遠無法帶來十倍速的突破。\n\n第一性原理（First Principles）要求我們把問題拆解到最基本、不可再分割的真實條件，再從零開始向上重新組合。無論是降低產品成本、設計個人商業模式，還是規劃健康減脂計畫，只要敢於質疑「一直以來都是這樣」的假設，就能發現別人忽略的結構性紅利。"},
    {"title": "【今日深度長文 #5】第二大腦知識管理術：從輸入到輸出的閉環", "cat": "學習方法", "author": "今日知識精編", "quote": "「知識只有在被整理、連結並實際輸出應用時，才會真正成為你的資產。」", "content": "許多愛書人讀了上百本書，半年後卻只記得書名，原因在於缺乏「輸出導向」的筆記系統。高效的學習閉環包含三個步驟：捕捉（只記下真正觸動你的金句與觀點）、提煉（用自己的白話重寫成三行核心摘要）、輸出（分享給朋友、寫成短文或套用到手邊的專案中）。當你帶著「今晚要分享給別人」的心態閱讀時，吸收效率會瞬間提升三倍以上。"},
    {"title": "【今日深度長文 #6】決策疲勞與極簡主義：把意志力留給最重要的小事", "cat": "生活哲學", "author": "今日知識精編", "quote": "「意志力就像手機電池，每做一個無關緊要的小決定就會消耗一格電量。」", "content": "心理學研究證實，人類每天能夠做出的高品質決策次數是有限的。如果在早上就花費大量精力煩惱早餐吃什麼、穿哪件衣服、回覆瑣碎訊息，到了下午面對真正影響人生與事業的重大決策時，大腦就會傾向選擇最省力卻最平庸的選項。\n\n建立固定的晨間儀式、簡化日常選擇、將重複性事務自動化，能為你的大腦保留最寶貴的認知頻寬，專注於創造真正高價值的成果。"},
    {"title": "【今日深度長文 #7】反脆弱系統設計：如何在不確定性中越挫越勇", "cat": "風險管理", "author": "今日知識精編", "quote": "「風會熄滅蠟燭，卻能使火越燒越旺。我們要成為渴望風的火焰。」", "content": "塔雷伯在《反脆弱》中將事物分為三類：脆弱（遇到波動就碎裂）、強韌（抵抗波動保持不變）、反脆弱（從波動、壓力與混亂中吸收養分而變得更強大）。\n\n個人職涯與財務規劃也應具備「槓鈴策略」：一端用 85% 的資源配置在極度穩健、絕對安全的基礎上（如健康作息、核心技能、穩健現金流）；另一端用 15% 的時間與成本進行低風險、高上限的小型試錯（如開發新數位工具、學習新領域），如此便能在零破產風險的前提下享受無限向上的驚喜。"},
    {"title": "【今日深度長文 #8】微習慣與環境設計：無痛建立終身運動與閱讀節奏", "cat": "行為科學", "author": "今日知識精編", "quote": "「你不需要更強大的自律，你只需要一個讓好習慣自動發生的環境。」", "content": "靠咬牙苦撐的自律通常撐不過兩週，因為大腦天性抗拒高耗能的改變。最聰明的做法是把目標縮小到「不可能失敗」的程度——想運動就先穿上車褲出門騎十分鐘；想閱讀就先打開有聲書聽五分鐘。\n\n一旦啟動阻力消失，大腦的慣性就會自然帶動你繼續前進。同時把手機充電座移出臥室、把書本與水壺放在視線第一落點，環境會默默替你完成 80% 的自律。"},
    {"title": "【今日深度長文 #9】非暴力溝通四要素：化解衝突的高情商表達公式", "cat": "人際心理", "author": "今日知識精編", "quote": "「在指責與評判的背後，往往隱藏著一個尚未被滿足的深層需求。」", "content": "人際衝突多半源於把「客觀事實」與「主觀評判」混為一談。非暴力溝通提供一套清晰有效的四步公式：第一，描述客觀觀察（不帶評價地說出看到或聽到的事實）；第二，表達內心感受（說出「我感到焦急或擔心」，而非「你總是讓我生氣」）；第三，說明背後的需要（因為我重視這件事的品質與時間）；第四，提出具體可行的請求。這套方法能大幅降低對方的防禦心，讓對話迅速回到解決問題的軌道。"},
    {"title": "【今日深度長文 #10】長期主義者的時間視角：用十年維度看眼前的選擇", "cat": "人生戰略", "author": "今日知識精編", "quote": "「大多數人高估了自己一年能做到的事，卻嚴重低估了自己十年能成就的高度。」", "content": "在追求即時滿足的時代，願意以五年、十年為單位佈局的人幾乎沒有競爭對手。無論是深耕一項專業技能、累積健康的身體資本，還是打造一套持續服務用戶的知識與工具生態，前期都需要耐得住寂寞的耕耘。\n\n每當面臨選擇時，問自己一個問題：「十年後的我，會感謝今天的我做出哪一個決定？」答案往往清晰無比。"}
]

def fetch_daily_articles():
    today = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    today_tag = today.strftime("%Y-%m-%d")
    if len([x for x in DAILY_FRESH_ARTICLES if x.get("date_tag") == today_tag]) >= 10:
        return

    try:
        u = "https://wikipedia.org"
        headers = {"User-Agent": "ClassicReadingSalonBot/5.0"}
        pages = requests.get(u, headers=headers, timeout=6).json().get("query", {}).get("pages", {})
        added = len([x for x in DAILY_FRESH_ARTICLES if x.get("date_tag") == today_tag])
        for pid, pinfo in pages.items():
            if added >= 10:
                break
            raw_title = pinfo.get("title", "").strip()
            full_txt = pinfo.get("extract", "").strip()
            if raw_title and len(full_txt) >= 300 and ":" not in raw_title and not any(raw_title in x.get("title", "") for x in DAILY_FRESH_ARTICLES):
                added += 1
                clean_full = full_txt[:3600] + ("\n\n（……以上為完整深度知識長文精編）" if len(full_txt) > 3600 else "")
                first_sent = next(iter([s.strip() for s in clean_full.split("。") if len(s.strip()) > 12]), clean_full[:55])
                DAILY_FRESH_ARTICLES.append({
                    "id": f"DY{today.strftime('%m%d')}_{added}",
                    "date_tag": today_tag,
                    "track": "每日文章",
                    "cat": "今日深度百科",
                    "title": f"【今日長文 #{added}】{raw_title}",
                    "author": f"{today_tag} 每日自動蒐集完整知識長文",
                    "quote": f"「{first_sent}。」",
                    "content": clean_full,
                    "url": f"https://wikipedia.org{urllib.parse.quote(raw_title)}"
                })
    except Exception:
        pass

    # 移出 try...except 之外，確保無論維基 API 是否連線成功，永遠補滿足足 10 篇今日每日長文！
    for fb in FALLBACK_DAILY_ARTICLES:
        if len([x for x in DAILY_FRESH_ARTICLES if x.get("date_tag") == today_tag]) >= 10:
            break
        if not any(fb["title"] in x.get("title", "") for x in DAILY_FRESH_ARTICLES):
            DAILY_FRESH_ARTICLES.append({
                "id": f"FB_{today.strftime('%m%d')}_{len(DAILY_FRESH_ARTICLES)+1}",
                "date_tag": today_tag,
                "track": "每日文章",
                "cat": fb["cat"],
                "title": fb["title"],
                "author": f"{today_tag} {fb['author']}",
                "quote": fb["quote"],
                "content": fb["content"],
                "url": BOOK_AFFILIATE_URL
            })

fetch_daily_articles()

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
    return {"status": "Online", "service": "Taiwan Classic & Daily Full-Text Audio Reader Pro 5.0"}

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
        "id": bid, "track": track, "cat": cat.strip() or "深度長文",
        "title": title.strip() or "私藏長文", "author": author.strip() or "典藏讀者",
        "quote": quote.strip() or "「閱讀讓靈魂更自由。」", "content": content.strip() or "完整長文內容",
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
        <div id="track-desc" style="font-size:14px;font-weight:900;margin-top:8px;line-height:1.5;">📅【今日每日長文軌道】每日自動蒐集 10 篇最新完整知識長文（與經典原典完全不同），支援台灣中文語音連播！</div>
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
          ? '📅【今日每日長文軌道】每日自動蒐集 10 篇最新完整知識長文（與經典原典完全不同），支援台灣中文語音連播！'
          : '🏛️【傳世經典原典軌道】精選 10 篇千古名篇完整原文與深度賞析，支援台灣中文語音連播！';
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
    d_title = str(daily_top.get("title", "今日全球華語熱讀完整長文")) if isinstance(daily_top, dict) else "今日全球華語熱讀完整長文"
    c_quote = str(classic_top.get("quote", "「不戰而屈人之兵，善之善者也。」")) if isinstance(classic_top, dict) else "「閱讀讓靈魂更自由。」"

    share_msg = urllib.parse.quote(f"📚【雙軌典藏書房 ＆ 完整長文有聲閱讀館】\n📅 今日新文：{d_title}\n🏛️ 經典名句：{c_quote}\n🎧 打開即享 20 篇完整長文全文 ＋ 台灣中文語音連續聽書！\n👉 立即進入書房：\n{app_uri}")
    share_uri = f"https:{S}{S}line.me{S}R{S}share?text={share_msg}"

    bubble_1 = BubbleContainer(
        size="mega",
        header=BoxComponent(layout="vertical", background_color="#1E3A2F", padding_all="16px", contents=[
            TextComponent(text="📚 雙軌典藏書房 ＆ 長文閱讀館", weight="bold", size="md", color="#F7F3EA", wrap=True),
            TextComponent(text="今日長文 10 篇 · 經典原典 10 篇 · 中文聽書", size="xs", color="#E5C158", weight="bold", wrap=True, margin="xs")
        ]),
        body=BoxComponent(layout="vertical", spacing="sm", background_color="#FFFDF9", contents=[
            TextComponent(text=f"📅 今日新文：{d_title}", size="xs", color="#1E3A2F", weight="bold", wrap=True),
            BoxComponent(layout="vertical", background_color="#F4EFE4", corner_radius="12px", padding_all="12px", contents=[
                TextComponent(text=f"🏛️ 經典原典：{c_quote}", size="xs", color="#4A3B2C", wrap=True)
            ])
        ]),
        footer=BoxComponent(layout="vertical", spacing="sm", background_color="#FFFDF9", contents=[
            ButtonComponent(style="primary", color="#1E3A2F", height="sm", action=URIAction(label="📖 開啟雙軌 20 篇全文 ＆ 中文聽書", uri=app_uri)),
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
            TextComponent(text="👈 向左滑動返回「雙軌 20 篇完整長文與中文聽書館」", size="xxs", color="#6B5846", weight="bold")
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
    line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="📚 雙軌典藏書房 ＆ 20 篇完整長文有聲閱讀館已啟動", contents=card))

@handler.add(MessageEvent, message=TextMessage)
def on_text(event):
    uid = event.source.user_id
    txt = event.message.text.strip()
    app_uri = f"{RENDER_BASE_URL}/reader_app?openExternalBrowser=1"
    fetch_daily_articles()

    try:
        if txt == "每日長文":
            lines = ["📅【今日自動蒐集・10 篇完整深度長文目錄（與經典原典完全不同）】"]
            for idx, b in enumerate(DAILY_FRESH_ARTICLES[:10], 1):
                lines.append(f"\n{idx}. {b.get('title','')}（約 {len(b.get('content',''))} 字）")
            lines.append(f"\n🎧 點擊開啟護眼閱讀器，馬上全文直讀＋台灣中文語音連播：\n{app_uri}")
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="\n".join(lines)))
            return

        if txt == "經典長文":
            lines = ["🏛️【傳世經典原典館・10 篇千古名篇完整原文與賞析】"]
            for idx, b in enumerate(CLASSIC_LONG_ARTICLES[:10], 1):
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

        matched = [b for b in (DAILY_FRESH_ARTICLES + CLASSIC_LONG_ARTICLES) if any(k in txt for k in ["孫子", "兵法", "赤壁", "蘇軾", "道德經", "老子", "出師表", "諸葛亮", "岳陽樓", "范仲淹", "桃花源", "陶淵明", "蘭亭", "王羲之", "師說", "韓愈", "陋室銘", "愛蓮說", "逍遙遊", "莊子"])]
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
