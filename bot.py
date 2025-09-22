# part1.py (PHẦN 1/2) — DÁN TRƯỚC
import discord
from discord.ext import commands
from discord import app_commands
import random
import os
import sqlite3
import time
from flask import Flask
from threading import Thread
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)

# ---------- CONFIG ----------
PREFIX = ":"
COIN_NAME = "Coincat"
COIN_EMOJI = "🐱💰"
DATA_DB = "data.db"
ADMIN_ID = "1199321278637678655"  # admin ID bạn cung cấp
BASE_COOLDOWN = 3.0              # base cooldown in seconds
COOLDOWN_STEP = 0.2              # add per use
COOLDOWN_RESET_AFTER = 3600.0    # seconds (1 hour)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# ---------- KEEP-ALIVE (Flask) ----------
app = Flask("")
@app.route("/")
def home():
    return "Fishing Bot (Render) — alive!"
def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
Thread(target=run_flask, daemon=True).start()

# ---------- SQLITE DB SETUP ----------
conn = sqlite3.connect(DATA_DB, check_same_thread=False)
c = conn.cursor()

# players: id TEXT PRIMARY KEY, money INT, rod TEXT, bait TEXT, rod_dur INT, bait_dur INT, level INT, exp INT
c.execute("""
CREATE TABLE IF NOT EXISTS players(
    id TEXT PRIMARY KEY,
    money INTEGER,
    rod TEXT,
    bait TEXT,
    rod_dur INTEGER,
    bait_dur INTEGER,
    level INTEGER,
    exp INTEGER
)
""")

# inventory: user_id, fish_name, qty
c.execute("""
CREATE TABLE IF NOT EXISTS inventory(
    user_id TEXT,
    fish_name TEXT,
    qty INTEGER,
    PRIMARY KEY(user_id, fish_name)
)
""")

# cooldowns: user_id PRIMARY KEY, current_cd REAL, last_use REAL, last_reset REAL
c.execute("""
CREATE TABLE IF NOT EXISTS cooldowns(
    user_id TEXT PRIMARY KEY,
    current_cd REAL,
    last_use REAL,
    last_reset REAL
)
""")

conn.commit()

# ---------- GAME DATA ----------
# Fish by rarity (prices are base sell price before multiplier)
FISH_BY_RARITY = {
    "Common": {
        "Cá chép 🐟": 50, "Cá rô phi 🐠": 40, "Tôm nhỏ 🦐": 30, "Mực nhỏ 🦑": 35,
        "Cua nhỏ 🦀": 25, "Cá bống 🐟": 28, "Cá diếc 🐟": 22, "Cá trôi 🐟": 24,
        "Cá chuồn 🐟": 20, "Cá vàng 🐠": 18, "Cá hề 🐠": 26, "Cá mè 🐟": 27
    },
    "Uncommon": {
        "Cá koi 🎏": 800, "Cá nóc 🐡": 500, "Bạch tuộc 🐙": 700, "Cá cơm 🐟": 600,
        "Cá trắm 🐟": 650, "Cá chim 🐟": 750, "Cá saba 🐟": 550
    },
    "Rare": {
        "Cá mập 🦈": 2000, "Cá heo 🐬": 2200, "Cá voi 🐋": 2500, "Pufferfish hiếm 🐡": 3000,
        "Cá ngừ 🐟": 2800, "Cá hồi 🐟": 2600, "Cá ngựa 🐠": 2400
    },
    "Epic": {
        "Cá sấu 🐊": 5000, "Lươn khổng lồ 🐍": 4500, "Cá ngừ đại dương 🐟": 5500, "Cá mặt trăng 🐠": 6000,
        "Cá mặt quỷ 🐟": 4800
    },
    "Legendary": {
        "Cá nhà táng 🐳": 10000, "Cá hổ 🐅": 12000, "Cá kiếm 🐟": 11000, "Marlin 🐟": 13000
    },
    "Mythic": {
        "Rồng nước 🐉": 20000, "Cá khủng long 🦖": 30000, "Leviathan 🐟": 40000
    },
    "Exotic": {  # exotic not reduced
        "CatFish 🐟": 350000, "Megalodon 🦈": 500000, "Dragonfish 🐉": 1000000
    }
}

# Apply sale multiplier: user requested "Giá bán cá tăng 2 lần"
# We'll store SELL_PRICE = base * 2
FISH_INFO = {}
for rar, mapping in FISH_BY_RARITY.items():
    for name, base in mapping.items():
        sell_price = base * 2  # x2 selling price
        FISH_INFO[name] = {"rarity": rar, "sell_price": sell_price}

# Rarity base weights for random choice (Exotic ~0.1%)
RARITY_BASE = {"Common":60, "Uncommon":20, "Rare":10, "Epic":5, "Legendary":3, "Mythic":2, "Exotic":0.1}
ALL_FISH_NAMES = list(FISH_INFO.keys())
EXOTIC_NAMES = [n for n,i in FISH_INFO.items() if i["rarity"]=="Exotic"]
NON_EXOTIC = [n for n in ALL_FISH_NAMES if n not in EXOTIC_NAMES]

# Rods (base prices), user requested "Giá đồ trong shop tăng 10 lần"
RODS_BASE = {
    "Cần tre 🎣": 50, "Cần gỗ 🎣": 100, "Cần tre bọc sắt 🎣": 200, "Cần sắt 🎣": 500,
    "Cần hợp kim 🎣": 1000, "Cần titan 🎣": 2000, "Cần carbon 🎣": 3000, "Cần vàng 🎣": 5000,
    "Cần kim cương 🎣": 10000, "Cần bạch kim 🎣": 15000, "Cần thần thoại 🎣": 25000,
    "Cần vũ trụ 🎣": 50000, "Cần quỷ 🎣": 80000, "Cần thiên thần 🎣": 100000,
    "Cần hỗn mang 🎣": 200000, "Cần thời gian 🎣": 300000, "Cần không gian 🎣": 500000,
    "Cần vĩnh hằng 🎣": 1000000, "Cần truyền thuyết 🎣": 2000000, "Cần tối thượng 🎣": 5000000
}
RODS = {}
for k,v in RODS_BASE.items():
    RODS[k] = {"price": v * 10, "durability": max(10, int(v/10)), "luck": max(0, int(v/1000))}

# Baits (base prices), user requested "Giá mồi trong shop tăng 100 lần"
BAITS_BASE = {
    "Giun đất 🪱": 10, "Dế mèn 🪳": 20, "Bánh mì 🍞": 5, "Ngô 🌽": 8, "Thịt vụn 🥩": 15,
    "Tôm nhỏ 🦐": 50, "Mồi mực 🦑": 70, "Cá con 🐟": 100, "Trái cây 🍎": 30, "Ruồi 🪰": 12,
    "Cào cào 🦗": 18, "Ốc sên 🐌": 25, "Muỗi 🦟": 10, "Tôm bóc vỏ 🍤": 60, "Cua nhỏ 🦀": 80,
    "Xương cá 🦴": 40, "Vỏ sò 🐚": 45, "Trứng thối 🥚": 5, "Phô mai 🧀": 35, "Bánh mì dài 🥖": 15,
    "Cà rốt 🥕": 12, "Chuối 🍌": 20, "Nho 🍇": 22, "Gà sống 🍗": 70, "Bò sống 🥩": 100
}
BAITS = {}
for k,v in BAITS_BASE.items():
    BAITS[k] = {"price": v * 100, "luck": max(0, int(v/20)), "durability": max(5, int(v/2))}

# ---------- DB helpers ----------
def get_player_row(user_id: str):
    c.execute("SELECT id,money,rod,bait,rod_dur,bait_dur,level,exp FROM players WHERE id=?", (user_id,))
    return c.fetchone()

def ensure_player_db(user_id: str):
    if get_player_row(user_id) is None:
        # default rod/bait = first keys
        default_rod = next(iter(RODS.keys()))
        default_bait = next(iter(BAITS.keys()))
        c.execute("INSERT INTO players(id,money,rod,bait,rod_dur,bait_dur,level,exp) VALUES(?,?,?,?,?,?,?,?)",
                  (user_id, 1000, default_rod, default_bait, RODS[default_rod]["durability"], BAITS[default_bait]["durability"], 1, 0))
        conn.commit()

def get_money(user_id: str):
    ensure_player_db(user_id)
    r = get_player_row(user_id)
    return r[1]

def set_money(user_id: str, amount: int):
    ensure_player_db(user_id)
    c.execute("UPDATE players SET money=? WHERE id=?", (amount, user_id))
    conn.commit()

def add_money(user_id: str, amount: int):
    ensure_player_db(user_id)
    cur = get_money(user_id)
    set_money(user_id, cur + amount)

def get_equipment(user_id: str):
    ensure_player_db(user_id)
    r = get_player_row(user_id)
    return {"rod": r[2], "bait": r[3], "rod_dur": r[4], "bait_dur": r[5], "level": r[6], "exp": r[7]}

def set_equipment(user_id: str, rod=None, bait=None, rod_dur=None, bait_dur=None):
    ensure_player_db(user_id)
    if rod is not None:
        c.execute("UPDATE players SET rod=? WHERE id=?", (rod, user_id))
    if bait is not None:
        c.execute("UPDATE players SET bait=? WHERE id=?", (bait, user_id))
    if rod_dur is not None:
        c.execute("UPDATE players SET rod_dur=? WHERE id=?", (rod_dur, user_id))
    if bait_dur is not None:
        c.execute("UPDATE players SET bait_dur=? WHERE id=?", (bait_dur, user_id))
    conn.commit()

def get_inventory(user_id: str):
    ensure_player_db(user_id)
    c.execute("SELECT fish_name,qty FROM inventory WHERE user_id=?", (user_id,))
    return dict(c.fetchall())

def set_inventory_item(user_id: str, fish_name: str, qty: int):
    ensure_player_db(user_id)
    if qty <= 0:
        c.execute("DELETE FROM inventory WHERE user_id=? AND fish_name=?", (user_id, fish_name))
    else:
        c.execute("INSERT INTO inventory(user_id,fish_name,qty) VALUES(?,?,?) ON CONFLICT(user_id,fish_name) DO UPDATE SET qty=?",
                  (user_id, fish_name, qty, qty))
    conn.commit()

def add_inventory(user_id: str, fish_name: str, delta: int):
    inv = get_inventory(user_id)
    newq = inv.get(fish_name, 0) + delta
    set_inventory_item(user_id, fish_name, newq)

def get_cooldown_row(user_id: str):
    c.execute("SELECT user_id,current_cd,last_use,last_reset FROM cooldowns WHERE user_id=?", (user_id,))
    return c.fetchone()

def ensure_cooldown_row(user_id: str):
    if get_cooldown_row(user_id) is None:
        now = time.time()
        c.execute("INSERT INTO cooldowns(user_id,current_cd,last_use,last_reset) VALUES(?,?,?,?)", (user_id, BASE_COOLDOWN, 0.0, now))
        conn.commit()

def update_cooldown_after_use(user_id: str):
    ensure_cooldown_row(user_id)
    row = get_cooldown_row(user_id)
    current_cd = row[1]
    last_use = time.time()
    last_reset = row[3]
    # if > reset interval since last reset, reset
    if last_use - last_reset >= COOLDOWN_RESET_AFTER:
        current_cd = BASE_COOLDOWN
        last_reset = last_use
    # increment
    current_cd += COOLDOWN_STEP
    c.execute("UPDATE cooldowns SET current_cd=?, last_use=?, last_reset=? WHERE user_id=?", (current_cd, last_use, last_reset, user_id))
    conn.commit()
    return current_cd

def check_and_apply_cooldown(user_id: str):
    """Return (ok:bool, wait_seconds:float). If ok, apply update (increase cd & set last_use)."""
    ensure_cooldown_row(user_id)
    row = get_cooldown_row(user_id)
    current_cd, last_use, last_reset = row[1], row[2], row[3]
    now = time.time()
    # reset if last_reset too old
    if now - last_reset >= COOLDOWN_RESET_AFTER:
        current_cd = BASE_COOLDOWN
        last_reset = now
    # check elapsed since last_use
    elapsed = now - last_use
    if elapsed < current_cd:
        return False, current_cd - elapsed
    # apply increase
    new_cd = current_cd + COOLDOWN_STEP
    c.execute("UPDATE cooldowns SET current_cd=?, last_use=?, last_reset=? WHERE user_id=?", (new_cd, now, last_reset, user_id))
    conn.commit()
    return True, 0.0

def give_exp(user_id: str, amount: int):
    ensure_player_db(user_id)
    row = get_player_row(user_id)
    level = row[6]
    exp = row[7] + amount
    leveled = False
    while exp >= level * 100:
        exp -= level * 100
        level += 1
        leveled = True
    c.execute("UPDATE players SET level=?, exp=? WHERE id=?", (level, exp, user_id))
    conn.commit()
    return leveled

def format_money(amount: int) -> str:
    return f"{amount:,} {COIN_EMOJI}"

# ---------- CHOOSE FISH ----------
def choose_fish_for_user(user_id: str):
    # exotic explicit 0.1%
    if random.randint(1,1000) == 1:
        return random.choice(EXOTIC_NAMES)
    # weighted among non-exotic
    weighted = []
    for name, info in FISH_INFO.items():
        if info["rarity"] == "Exotic": continue
        base = RARITY_BASE.get(info["rarity"], 1)
        weighted.append((name, base))
    total = sum(w for _,w in weighted)
    pick = random.uniform(0, total)
    upto = 0.0
    for name,w in weighted:
        if upto + w >= pick:
            return name
        upto += w
    return weighted[-1][0]
    # part2.py (PHẦN 2/2) — DÁN SAU PHẦN 1

# ---------- COMMANDS (prefix) ----------
@bot.event
async def on_ready():
    logging.info(f"{bot.user} is online. Syncing slash commands...")
    try:
        await bot.tree.sync()
        logging.info("Slash commands synced.")
    except Exception:
        logging.exception("Failed syncing slash commands")
    # autosave not needed (DB), but keep tasks if desired
    logging.info("Bot ready.")

@bot.command(name="sotien")
async def cmd_sotien(ctx):
    uid = str(ctx.author.id)
    ensure_player_db(uid)
    m = get_money(uid)
    embed = discord.Embed(title="Số dư", color=0x00AAFF)
    embed.add_field(name=f"{ctx.author.display_name}", value=f"{format_money(m)}", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="khodo")
async def cmd_khodo(ctx):
    uid = str(ctx.author.id)
    ensure_player_db(uid)
    inv = get_inventory(uid)
    if not inv:
        await ctx.send(embed=discord.Embed(description="🎒 Kho của bạn trống rỗng.", color=0xFFD700))
        return
    # group by rarity
    grouped = {}
    for fish_name, qty in inv.items():
        rar = FISH_INFO.get(fish_name, {}).get("rarity","Common")
        grouped.setdefault(rar, []).append((fish_name, qty))
    embed = discord.Embed(title=f"🎒 Kho đồ của {ctx.author.display_name}", color=0xFFD700)
    for rar in ["Common","Uncommon","Rare","Epic","Legendary","Mythic","Exotic"]:
        if rar in grouped:
            embed.add_field(name=f"{rar} ({len(grouped[rar])})", value="\n".join(f"{n} x{q}" for n,q in grouped[rar]), inline=False)
    eq = get_equipment(uid)
    embed.set_footer(text=f"Cần: {eq['rod']} (Dur {eq['rod_dur']}) | Mồi: {eq['bait']} (Dur {eq['bait_dur']})")
    await ctx.send(embed=embed)

@bot.command(name="cuahang")
async def cmd_cuahang(ctx):
    embed = discord.Embed(title="🏪 Cửa hàng", color=0x8A2BE2)
    rods_text = "\n".join([f"{name} — {format_money(info['price'])} (Dur {info['durability']})" for name,info in RODS.items()])
    baits_text = "\n".join([f"{name} — {format_money(info['price'])} (Luck+{info['luck']}, Dur {info['durability']})" for name,info in BAITS.items()])
    embed.add_field(name="🎣 Cần", value=rods_text[:1000] or "—", inline=True)
    embed.add_field(name="🪱 Mồi", value=baits_text[:1000] or "—", inline=True)
    await ctx.send(embed=embed)

@bot.command(name="mua")
async def cmd_mua(ctx, *, item: str):
    uid = str(ctx.author.id)
    ensure_player_db(uid)
    it = item.strip().lower()
    chosen = None
    for k in RODS:
        if it == k.lower() or it in k.lower():
            chosen = ("rod", k); break
    if not chosen:
        for k in BAITS:
            if it == k.lower() or it in k.lower():
                chosen = ("bait", k); break
    if not chosen:
        await ctx.send(embed=discord.Embed(description="❌ Không tìm thấy vật phẩm trong cửa hàng (gõ đúng tên/substring).", color=0xFF5555))
        return
    cat, name = chosen
    price = (RODS if cat=="rod" else BAITS)[name]["price"]
    money = get_money(uid)
    if money < price:
        await ctx.send(embed=discord.Embed(description="❌ Bạn không đủ Coincat.", color=0xFF5555))
        return
    # deduct and set equip
    set_money(uid, money - price)
    if cat == "rod":
        set_equipment(uid, rod=name, rod_dur=RODS[name]["durability"])
    else:
        set_equipment(uid, bait=name, bait_dur=BAITS[name]["durability"])
    await ctx.send(embed=discord.Embed(description=f"✅ Đã mua {name} — {format_money(price)}", color=0x55FF55))

@bot.command(name="cauca")
async def cmd_cauca(ctx, times: Optional[int]=1):
    uid = str(ctx.author.id)
    ensure_player_db(uid)
    ok, wait = check_and_apply_cooldown(uid)
    if not ok:
        await ctx.send(embed=discord.Embed(description=f"⏳ Hãy đợi {wait:.1f}s trước khi dùng lại.", color=0xFFAA00))
        return
    times = max(1, min(10, times or 1))
    results=[]
    total_exp = 0
    for _ in range(times):
        equip = get_equipment(uid)
        if equip["rod_dur"] <= 0:
            await ctx.send(embed=discord.Embed(description="❌ Cần của bạn đã hỏng. Mua cần mới trong :cuahang", color=0xFF5555)); return
        if equip["bait_dur"] <= 0:
            await ctx.send(embed=discord.Embed(description="❌ Hết mồi. Mua mồi trong :cuahang", color=0xFF5555)); return
        fish = choose_fish_for_user(uid)
        add_inventory(uid, fish, 1)
        price = FISH_INFO[fish]["sell_price"]
        total_exp += max(1, int(price/2))
        # reduce durability
        set_equipment(uid, rod_dur=equip["rod_dur"]-1, bait_dur=equip["bait_dur"]-1)
        results.append(f"{fish} — {FISH_INFO[fish]['rarity']} — {format_money(price)}")
    give_exp(uid, total_exp)
    embed = discord.Embed(title=f"🎣 {ctx.author.display_name} đã câu {len(results)} con!", color=0x00CC66)
    embed.add_field(name="Kết quả", value="\n".join(results), inline=False)
    embed.add_field(name="Exp", value=str(total_exp), inline=True)
    await ctx.send(embed=embed)

@bot.command(name="banca")
async def cmd_banca(ctx, *, arg: str):
    uid = str(ctx.author.id)
    ensure_player_db(uid)
    inv = get_inventory(uid)
    if not inv:
        await ctx.send(embed=discord.Embed(description="Bạn không có cá để bán.", color=0xFFCC00)); return
    if arg.lower() == "all":
        total=0; details=[]
        for fish_name, qty in list(inv.items()):
            price = FISH_INFO.get(fish_name, {}).get("sell_price",0)
            subtotal = price * qty
            total += subtotal
            details.append(f"{qty}x {fish_name} = {format_money(subtotal)}")
            set_inventory_item(uid, fish_name, 0)
        add_money(uid, total)
        await ctx.send(embed=discord.Embed(title="💸 Bán toàn bộ cá", description="\n".join(details), color=0x00AAFF).add_field(name="Tổng nhận", value=format_money(total)))
        return
    # sell single by substring
    matched = None
    for fish_name in list(inv.keys()):
        if arg.lower() in fish_name.lower():
            matched = fish_name; break
    if not matched:
        await ctx.send(embed=discord.Embed(description="❌ Không tìm thấy con cá này trong kho.", color=0xFF5555)); return
    price = FISH_INFO.get(matched, {}).get("sell_price",0)
    add_money(uid, price)
    newq = inv[matched]-1
    set_inventory_item(uid, matched, newq)
    await ctx.send(embed=discord.Embed(description=f"💰 Đã bán 1x {matched} — {format_money(price)}", color=0x55FF55))

@bot.command(name="chuyentien")
async def cmd_chuyentien(ctx, member: discord.Member, amount: int):
    uid_from = str(ctx.author.id)
    uid_to = str(member.id)
    ensure_player_db(uid_from); ensure_player_db(uid_to)
    if amount <= 0:
        await ctx.send(embed=discord.Embed(description="Số tiền phải lớn hơn 0.", color=0xFF5555)); return
    if amount > 300000:
        await ctx.send(embed=discord.Embed(description="Giới hạn chuyển tối đa là 300000 Coincat.", color=0xFF5555)); return
    if get_money(uid_from) < amount:
        await ctx.send(embed=discord.Embed(description="Bạn không đủ tiền.", color=0xFF5555)); return
    add_money(uid_from, -amount); add_money(uid_to, amount)
    await ctx.send(embed=discord.Embed(description=f"✅ {ctx.author.mention} đã chuyển {format_money(amount)} cho {member.mention}", color=0x00FF88))

@bot.command(name="admingive")
async def cmd_admingive(ctx, amount: int):
    # only admin id allowed
    if str(ctx.author.id) != ADMIN_ID:
        await ctx.send(embed=discord.Embed(description="❌ Bạn không có quyền dùng lệnh này.", color=0xFF5555)); return
    uid = str(ctx.author.id)
    ensure_player_db(uid)
    add_money(uid, amount)
    await ctx.send(embed=discord.Embed(description=f"✅ Đã thêm {format_money(amount)} cho {ctx.author.mention}", color=0x88FF88))

# ---------- SLASH COMMANDS (mirror) ----------
@bot.tree.command(name="sotien", description="Xem số tiền Coincat")
async def slash_sotien(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    ensure_player_db(uid)
    m = get_money(uid)
    embed = discord.Embed(title="Số dư", color=0x00AAFF)
    embed.add_field(name=interaction.user.display_name, value=format_money(m), inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="khodo", description="Xem kho đồ (phân theo rarity)")
async def slash_khodo(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    ensure_player_db(uid)
    inv = get_inventory(uid)
    if not inv:
        await interaction.response.send_message(embed=discord.Embed(description="🎒 Kho trống.", color=0xFFD700), ephemeral=True); return
    grouped={}
    for fish_name, qty in inv.items():
        rar = FISH_INFO.get(fish_name, {}).get("rarity","Common")
        grouped.setdefault(rar, []).append((fish_name, qty))
    embed = discord.Embed(title=f"🎒 Kho đồ của {interaction.user.display_name}", color=0xFFD700)
    for rar in ["Common","Uncommon","Rare","Epic","Legendary","Mythic","Exotic"]:
        if rar in grouped:
            embed.add_field(name=f"{rar} ({len(grouped[rar])})", value="\n".join(f"{n} x{q}" for n,q in grouped[rar]), inline=False)
    eq = get_equipment(uid)
    embed.set_footer(text=f"Cần: {eq['rod']} (Dur {eq['rod_dur']}) | Mồi: {eq['bait']} (Dur {eq['bait_dur']})")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="cuahang", description="Xem cửa hàng")
async def slash_cuahang(interaction: discord.Interaction):
    rods_text = "\n".join([f"{name} — {format_money(info['price'])} (Dur {info['durability']})" for name,info in RODS.items()])
    baits_text = "\n".join([f"{name} — {format_money(info['price'])} (Luck+{info['luck']}, Dur {info['durability']})" for name,info in BAITS.items()])
    embed = discord.Embed(title="🏪 Cửa hàng", color=0x8A2BE2)
    embed.add_field(name="🎣 Cần", value=rods_text[:1000], inline=True)
    embed.add_field(name="🪱 Mồi", value=baits_text[:1000], inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="mua", description="Mua cần/mồi")
@app_commands.describe(item="Tên vật phẩm (copy đúng hoặc chứa substring)")
async def slash_mua(interaction: discord.Interaction, item: str):
    uid = str(interaction.user.id)
    ensure_player_db(uid)
    it = item.strip().lower()
    chosen=None
    for k in RODS:
        if it==k.lower() or it in k.lower(): chosen=("rod",k); break
    if not chosen:
        for k in BAITS:
            if it==k.lower() or it in k.lower(): chosen=("bait",k); break
    if not chosen:
        await interaction.response.send_message(embed=discord.Embed(description="❌ Không tìm thấy vật phẩm.", color=0xFF5555), ephemeral=True); return
    cat,name = chosen
    price = (RODS if cat=="rod" else BAITS)[name]["price"]
    if get_money(uid) < price:
        await interaction.response.send_message(embed=discord.Embed(description="❌ Bạn không đủ Coincat.", color=0xFF5555), ephemeral=True); return
    set_money(uid, get_money(uid)-price)
    if cat=="rod":
        set_equipment(uid, rod=name, rod_dur=RODS[name]["durability"])
    else:
        set_equipment(uid, bait=name, bait_dur=BAITS[name]["durability"])
    await interaction.response.send_message(embed=discord.Embed(description=f"✅ Đã mua {name} — {format_money(price)}", color=0x55FF55))

@bot.tree.command(name="cauca", description="Câu cá (1-10 lần)")
@app_commands.describe(times="Số lần (mặc định 1, max 10)")
async def slash_cauca(interaction: discord.Interaction, times: Optional[int]=1):
    await interaction.response.defer()
    uid = str(interaction.user.id)
    ensure_player_db(uid)
    ok, wait = check_and_apply_cooldown(uid)
    if not ok:
        await interaction.followup.send(embed=discord.Embed(description=f"⏳ Hãy đợi {wait:.1f}s trước khi dùng lại.", color=0xFFAA00)); return
    times = max(1, min(10, times or 1))
    results=[]; total_exp=0
    for _ in range(times):
        eq = get_equipment(uid)
        if eq["rod_dur"] <= 0:
            await interaction.followup.send(embed=discord.Embed(description="❌ Cần của bạn đã hỏng. Mua cần mới trong /cuahang", color=0xFF5555)); return
        if eq["bait_dur"] <= 0:
            await interaction.followup.send(embed=discord.Embed(description="❌ Hết mồi. Mua mồi trong /cuahang", color=0xFF5555)); return
        fish = choose_fish_for_user(uid)
        add_inventory(uid, fish, 1)
        price = FISH_INFO[fish]["sell_price"]
        total_exp += max(1, int(price/2))
        set_equipment(uid, rod_dur=eq["rod_dur"]-1, bait_dur=eq["bait_dur"]-1)
        results.append(f"{fish} — {FISH_INFO[fish]['rarity']} — {format_money(price)}")
    give_exp(uid, total_exp)
    await interaction.followup.send(embed=discord.Embed(title=f"🎣 {interaction.user.display_name} đã câu {len(results)} con!", description="\n".join(results), color=0x00CC66).add_field(name="Exp", value=str(total_exp)))

@bot.tree.command(name="banca", description="Bán cá (banca all để bán tất cả)")
@app_commands.describe(target="Tên cá hoặc 'all'")
async def slash_banca(interaction: discord.Interaction, target: Optional[str]=None):
    await interaction.response.defer()
    uid = str(interaction.user.id)
    ensure_player_db(uid)
    inv = get_inventory(uid)
    if not inv:
        await interaction.followup.send(embed=discord.Embed(description="Bạn không có cá để bán.", color=0xFFCC00)); return
    if target is None or target.lower()=="all":
        total=0; details=[]
        for fish_name, qty in list(inv.items()):
            price = FISH_INFO.get(fish_name,{}).get("sell_price",0)
            subtotal = price*qty
            total+=subtotal
            details.append(f"{qty}x {fish_name} = {format_money(subtotal)}")
            set_inventory_item(uid, fish_name, 0)
        add_money(uid, total)
        await interaction.followup.send(embed=discord.Embed(title="💸 Bán toàn bộ cá", description="\n".join(details), color=0x00AAFF).add_field(name="Tổng nhận", value=format_money(total)))
        return
    matched=None
    for fish_name in list(inv.keys()):
        if target.lower() in fish_name.lower():
            matched=fish_name; break
    if not matched:
        await interaction.followup.send(embed=discord.Embed(description="Không tìm thấy loại cá trong kho.", color=0xFF5555)); return
    price = FISH_INFO.get(matched,{}).get("sell_price",0)
    add_money(uid, price)
    set_inventory_item(uid, matched, inv[matched]-1)
    await interaction.followup.send(embed=discord.Embed(description=f"💰 Đã bán 1x {matched} — {format_money(price)}", color=0x55FF55))

@bot.tree.command(name="chuyentien", description="Chuyển Coincat (max 300000)")
@app_commands.describe(member="Người nhận", amount="Số tiền (<=300000)")
async def slash_chuyentien(interaction: discord.Interaction, member: discord.Member, amount: int):
    uid_from = str(interaction.user.id); uid_to = str(member.id)
    ensure_player_db(uid_from); ensure_player_db(uid_to)
    if amount <=0:
        await interaction.response.send_message(embed=discord.Embed(description="Số tiền phải >0.", color=0xFF5555), ephemeral=True); return
    if amount>300000:
        await interaction.response.send_message(embed=discord.Embed(description="Giới hạn 300000 Coincat.", color=0xFF5555), ephemeral=True); return
    if get_money(uid_from) < amount:
        await interaction.response.send_message(embed=discord.Embed(description="Bạn không đủ tiền.", color=0xFF5555), ephemeral=True); return
    add_money(uid_from, -amount); add_money(uid_to, amount)
    await interaction.response.send_message(embed=discord.Embed(description=f"✅ {interaction.user.mention} đã chuyển {format_money(amount)} cho {member.mention}", color=0x00FF88))

# ---------- ERROR HANDLER (slash & prefix handled in on_command_error) ----------
@bot.event
async def on_command_error(ctx, error):
    try:
        await ctx.send(embed=discord.Embed(title="⚠️ Lỗi xảy ra", description=f"`{type(error).__name__}: {error}`", color=0xFF5555))
    except Exception:
        logging.exception("Failed to notify user about error")
    logging.exception("Exception in command")

# ---------- RUN ----------
if __name__ == "__main__":
    logging.info("Starting bot...")
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logging.error("DISCORD_TOKEN env var not set. Exiting.")
    else:
        bot.run(token)
    
