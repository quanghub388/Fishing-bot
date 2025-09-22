# bot.py
import discord
from discord.ext import commands, tasks
from discord import app_commands
import random
import json
import os
import logging
from flask import Flask
from threading import Thread
from typing import Optional

# --------------------- CONFIG ---------------------
logging.basicConfig(level=logging.INFO)
INTENTS = discord.Intents.default()
INTENTS.message_content = True
PREFIX = ":"
COIN_EMOJI = "🐱💰"

bot = commands.Bot(command_prefix=PREFIX, intents=INTENTS, help_command=None)

DATA_FILE = "data.json"

# --------------------- KEEP-ALIVE (Flask) ---------------------
app = Flask("")

@app.route("/")
def index():
    return "Fishing Bot (Render Web Service) — alive!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

flask_thread = Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

# --------------------- DATA STORE ---------------------
# Structure: players[user_id_str] = {
#   "money": int,
#   "inventory": {fish_name: qty, ...},
#   "rod": rod_name,
#   "bait": bait_name,
#   "rod_dur": int,
#   "bait_dur": int,
#   "level": int,
#   "exp": int
# }
players = {}

def load_data():
    global players
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                players = json.load(f)
        except Exception as e:
            logging.exception("Failed load data.json, starting fresh.")
            players = {}
    else:
        players = {}

def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(players, f, indent=2, ensure_ascii=False)
    except Exception:
        logging.exception("Failed saving data.json")

load_data()

# auto-save every 60s
@tasks.loop(seconds=60)
async def autosave_loop():
    save_data()
    logging.info("Autosave players.json")

# --------------------- GAME DATA ---------------------
# fish organized by rarity (prices BEFORE reduction)
FISH_BY_RARITY = {
    "Common": {
        "Cá trích 🐟": 10, "Cá chép 🐠": 20, "Tôm 🦐": 15, "Mực 🦑": 18,
        "Cua 🦀": 22, "Cá hề 🐠": 25, "Cá rô phi 🐟": 12, "Cá bống 🐟":14,
        "Cá diếc 🐟":16, "Cá mè 🐟":20, "Cá chuồn 🐟":11, "Cá trôi 🐟":13
    },
    "Uncommon": {
        "Cá koi 🎏": 80, "Cá nóc 🐡": 50, "Bạch tuộc 🐙": 70, "Cá cơm 🐠":60,
        "Cá trắm 🐟":65, "Cá chim 🐟":75, "Cá saba 🐟": 55
    },
    "Rare": {
        "Cá mập 🦈": 200, "Cá heo 🐬":220, "Cá voi 🐋":250, "Pufferfish hiếm 🐡":300,
        "Cá ngừ 🐟":280, "Cá hồi 🐟":260, "Cá ngựa 🐠":240
    },
    "Epic": {
        "Cá sấu 🐊":500, "Lươn khổng lồ 🐍":450, "Cá ngừ đại dương 🐟":550, "Cá mặt trăng 🐠":600,
        "Cá mặt quỷ 🐟":480
    },
    "Legendary": {
        "Cá nhà táng 🐳":1000, "Cá hổ 🐅":1200, "Cá kiếm 🐟":1100, "Marlin 🐟":1300
    },
    "Mythic": {
        "Rồng nước 🐉":2000, "Cá khủng long 🦖":3000, "Leviathan 🐟":4000
    },
    "Exotic": {  # exotic: prices NOT reduced
        "CatFish 🐟":350000, "Megalodon 🦈":500000, "Dragonfish 🐉":1000000
    }
}

# Apply price reduction (x0.1) to all rarities except Exotic
FISH_PRICE = {}
for rarity, mapping in FISH_BY_RARITY.items():
    for name, price in mapping.items():
        if rarity != "Exotic":
            FISH_PRICE[name] = max(1, int(price * 0.1))  # reduce 10x
        else:
            FISH_PRICE[name] = price

# Build a list with rarity info
FISH_INFO = {}
for rarity, mapping in FISH_BY_RARITY.items():
    for name, price in mapping.items():
        FISH_INFO[name] = {"rarity": rarity, "price": FISH_PRICE[name]}

# Rods (20)
RODS = {
    "Cần tre 🎣": {"price":50, "durability":30, "luck":0},
    "Cần gỗ 🎣": {"price":100, "durability":50, "luck":1},
    "Cần tre bọc sắt 🎣": {"price":200, "durability":60, "luck":2},
    "Cần sắt 🎣": {"price":500, "durability":100, "luck":4},
    "Cần hợp kim 🎣": {"price":1000, "durability":150, "luck":6},
    "Cần titan 🎣": {"price":2000, "durability":200, "luck":8},
    "Cần carbon 🎣": {"price":3000, "durability":220, "luck":10},
    "Cần vàng 🎣": {"price":5000, "durability":300, "luck":12},
    "Cần kim cương 🎣": {"price":10000, "durability":400, "luck":15},
    "Cần bạch kim 🎣": {"price":15000, "durability":500, "luck":18},
    "Cần thần thoại 🎣": {"price":25000, "durability":700, "luck":22},
    "Cần vũ trụ 🎣": {"price":50000, "durability":1000, "luck":30},
    "Cần quỷ 🎣": {"price":80000, "durability":1200, "luck":40},
    "Cần thiên thần 🎣": {"price":100000, "durability":1500, "luck":45},
    "Cần hỗn mang 🎣": {"price":200000, "durability":2000, "luck":60},
    "Cần thời gian 🎣": {"price":300000, "durability":2500, "luck":80},
    "Cần không gian 🎣": {"price":500000, "durability":3000, "luck":100},
    "Cần vĩnh hằng 🎣": {"price":1000000, "durability":5000, "luck":150},
    "Cần truyền thuyết 🎣": {"price":2000000, "durability":8000, "luck":220},
    "Cần tối thượng 🎣": {"price":5000000, "durability":10000, "luck":500},
}

# Baits (25)
BAITS = {
    "Giun đất 🪱": {"price":10, "luck":1, "durability":30},
    "Dế mèn 🪳": {"price":20, "luck":2, "durability":25},
    "Bánh mì 🍞": {"price":5, "luck":1, "durability":40},
    "Ngô 🌽": {"price":8, "luck":1, "durability":35},
    "Thịt vụn 🥩": {"price":15, "luck":2, "durability":30},
    "Tôm nhỏ 🦐": {"price":50, "luck":3, "durability":20},
    "Mồi mực 🦑": {"price":70, "luck":4, "durability":15},
    "Cá con 🐟": {"price":100, "luck":5, "durability":10},
    "Trái cây 🍎": {"price":30, "luck":2, "durability":20},
    "Ruồi 🪰": {"price":12, "luck":1, "durability":25},
    "Cào cào 🦗": {"price":18, "luck":2, "durability":25},
    "Ốc sên 🐌": {"price":25, "luck":2, "durability":20},
    "Muỗi 🦟": {"price":10, "luck":1, "durability":30},
    "Tôm bóc vỏ 🍤": {"price":60, "luck":3, "durability":15},
    "Cua nhỏ 🦀": {"price":80, "luck":3, "durability":10},
    "Xương cá 🦴": {"price":40, "luck":2, "durability":25},
    "Vỏ sò 🐚": {"price":45, "luck":2, "durability":20},
    "Trứng thối 🥚": {"price":5, "luck":1, "durability":15},
    "Phô mai 🧀": {"price":35, "luck":2, "durability":25},
    "Bánh mì dài 🥖": {"price":15, "luck":2, "durability":30},
    "Cà rốt 🥕": {"price":12, "luck":1, "durability":25},
    "Chuối 🍌": {"price":20, "luck":1, "durability":20},
    "Nho 🍇": {"price":22, "luck":2, "durability":25},
    "Gà sống 🍗": {"price":70, "luck":4, "durability":10},
}

# Precompute fish lists
ALL_FISH_NAMES = list(FISH_INFO.keys())
EXOTIC_NAMES = [n for n,info in FISH_INFO.items() if info["rarity"] == "Exotic"]
NON_EXOTIC_NAMES = [n for n in ALL_FISH_NAMES if n not in EXOTIC_NAMES]

# --------------------- HELPERS ---------------------
def ensure_player(uid: str):
    if uid not in players:
        # default: give small starting money and newbie rod/bait
        default_rod = "Cần tre 🎣"
        default_bait = "Giun đất 🪱"
        players[uid] = {
            "money": 1000,
            "inventory": {},   # fish_name -> qty
            "rod": default_rod,
            "bait": default_bait,
            "rod_dur": RODS[default_rod]["durability"],
            "bait_dur": BAITS[default_bait]["durability"],
            "level": 1,
            "exp": 0
        }
        save_data()

def gain_exp(uid: str, amount: int):
    ensure_player(uid)
    p = players[uid]
    p["exp"] += amount
    leveled = False
    while p["exp"] >= p["level"] * 100:
        p["exp"] -= p["level"] * 100
        p["level"] += 1
        leveled = True
    if leveled:
        save_data()
    return leveled

def compute_luck(uid: str):
    ensure_player(uid)
    rod = players[uid]["rod"]
    bait = players[uid]["bait"]
    rod_luck = RODS.get(rod, {}).get("luck", 0)
    bait_luck = BAITS.get(bait, {}).get("luck", 0)
    return rod_luck + bait_luck

# Choose fish with weighted rarities; exotic chance 0.1%
def choose_random_fish(uid: str):
    ensure_player(uid)
    luck = compute_luck(uid)
    # base weights by rarities (can be tuned)
    weights = []
    names = []
    # Give small weight boost to rare ones from luck
    for name, info in FISH_INFO.items():
        r = info["rarity"]
        base = {"Common":60, "Uncommon":20, "Rare":10, "Epic":5, "Legendary":3, "Mythic":2, "Exotic":0.1}[r]
        # apply luck small bonus to rarer tiers
        if r == "Rare": base += luck//2
        if r == "Epic": base += luck//3
        if r == "Legendary": base += luck//4
        if r == "Mythic": base += luck//5
        # Exotic handled separately (we keep very small)
        names.append(name)
        weights.append(max(0.01, base))
    # First check exotic chance explicitly (0.1%)
    if random.randint(1,1000) == 1:
        return random.choice(EXOTIC_NAMES)
    # Otherwise weighted choice among non-exotic
    filtered = [(n,w) for n,w in zip(names,weights) if n not in EXOTIC_NAMES]
    total = sum(w for _,w in filtered)
    pick = random.uniform(0, total)
    upto = 0
    for n,w in filtered:
        if upto + w >= pick:
            return n
        upto += w
    return filtered[-1][0]

# --------------------- COMMAND RESPONSES (shared logic) ---------------------
def format_money(amount:int):
    return f"{amount:,} {COIN_EMOJI}"

def add_fish_to_player(uid: str, fish_name: str, qty:int=1):
    ensure_player(uid)
    inv = players[uid]["inventory"]
    inv[fish_name] = inv.get(fish_name,0) + qty
    save_data()

def sell_fish_for_player(uid: str, fish_name: str, qty:int):
    ensure_player(uid)
    inv = players[uid]["inventory"]
    if fish_name not in inv or inv[fish_name] < qty:
        return False, 0, "Bạn không có đủ con cá đó."
    price_each = FISH_INFO.get(fish_name,{}).get("price")
    if price_each is None:
        return False, 0, "Không thể bán con cá này."
    total = price_each * qty
    # add money
    players[uid]["money"] = players[uid].get("money",0) + total
    inv[fish_name] -= qty
    if inv[fish_name] <= 0:
        del inv[fish_name]
    save_data()
    return True, total, None

# --------------------- PREFIX COMMANDS ---------------------

@bot.command(name="cauca")
async def cmd_cauca(ctx, times: Optional[int]=1):
    """:cauca [times] - câu 1 hoặc vài lần (mặc định 1)"""
    uid = str(ctx.author.id)
    ensure_player(uid)

    times = max(1, min(10, times))  # không cho spam quá nhiều lần, tối đa 10 lần/lệnh
    results = []
    total_exp = 0
    for _ in range(times):
        # check durability
        if players[uid]["rod_dur"] <= 0:
            await ctx.send("❌ Cần của bạn đã hỏng! Hãy mua/đổi cần mới trong :cuahang / :mua")
            return
        if players[uid]["bait_dur"] <= 0:
            await ctx.send("❌ Hết mồi! Hãy mua mồi trong :cuahang / :mua")
            return
        fish_caught = choose_random_fish(uid)
        add_fish_to_player(uid, fish_caught, 1)
        exp_gain = FISH_INFO[fish_caught]["price"]//2 if FISH_INFO[fish_caught]["price"]>0 else 1
        total_exp += exp_gain
        # reduce durability
        players[uid]["rod_dur"] -= 1
        players[uid]["bait_dur"] -= 1
        results.append(fish_caught)
    leveled = gain_exp(uid, total_exp)
    embed = discord.Embed(title=f"🎣 {ctx.author.display_name} vừa câu được {len(results)} con!", color=discord.Color.blue())
    embed.add_field(name="Cá nhận được", value="\n".join(results), inline=False)
    embed.add_field(name="Exp nhận", value=str(total_exp), inline=True)
    embed.add_field(name="Level", value=str(players[uid]["level"]), inline=True)
    embed.set_footer(text=f"Sức bền: Cần {players[uid]['rod_dur']} | Mồi {players[uid]['bait_dur']}")
    await ctx.send(embed=embed)

@bot.command(name="banca")
async def cmd_banca(ctx, target: str):
    """:banca <tên cá>|all - bán 1 con hoặc bán tất cả"""
    uid = str(ctx.author.id)
    ensure_player(uid)
    if target.lower() == "all":
        inv = players[uid]["inventory"]
        if not inv:
            await ctx.send("Bạn không có cá để bán.")
            return
        details = []
        total = 0
        for fish_name, qty in list(inv.items()):
            price_each = FISH_INFO.get(fish_name,{}).get("price")
            if price_each is None:
                continue
            subtotal = price_each * qty
            total += subtotal
            details.append(f"{qty}x {fish_name} = {format_money(subtotal)}")
            del inv[fish_name]
        players[uid]["money"] = players[uid].get("money",0) + total
        save_data()
        embed = discord.Embed(title="💸 Bán toàn bộ cá", color=discord.Color.green())
        embed.add_field(name="Chi tiết", value="\n".join(details), inline=False)
        embed.add_field(name="Tổng nhận", value=format_money(total), inline=False)
        await ctx.send(embed=embed)
    else:
        fish_name = target
        ok, total, err = sell_fish_for_player(uid, fish_name, 1)
        if not ok:
            await ctx.send(err)
            return
        await ctx.send(f"💸 Bạn đã bán 1x {fish_name} được {format_money(total)}")

@bot.command(name="cuahang")
async def cmd_cuahang(ctx):
    """:cuahang - xem cửa hàng"""
    embed = discord.Embed(title="🏪 Cửa hàng (Cần & Mồi)", color=discord.Color.purple())
    rods_text = "\n".join([f"{name} — {data['price']} {COIN_EMOJI} (Dur {data['durability']})" for name,data in RODS.items()])
    baits_text = "\n".join([f"{name} — {data['price']} {COIN_EMOJI} (Luck+{data['luck']}, Dur {data['durability']})" for name,data in BAITS.items()])
    embed.add_field(name="🎣 Cần", value=rods_text, inline=True)
    embed.add_field(name="🪱 Mồi", value=baits_text, inline=True)
    await ctx.send(embed=embed)

@bot.command(name="mua")
async def cmd_mua(ctx, *, item_name: str):
    """:mua <tên vật phẩm> - mua cần hoặc mồi"""
    uid = str(ctx.author.id)
    ensure_player(uid)
    item = item_name.strip()
    # exact match needed; allow case-insensitive match by scanning keys
    chosen = None
    for k in list(RODS.keys()) + list(BAITS.keys()):
        if k.lower() == item.lower():
            chosen = k
            break
    if not chosen:
        await ctx.send("❌ Không tìm thấy item trong cửa hàng (gõ đúng tên có emoji). Dùng :cuahang để xem danh sách.")
        return
    # price
    if chosen in RODS:
        price = RODS[chosen]["price"]
        if players[uid]["money"] < price:
            await ctx.send("❌ Bạn không đủ Coincat để mua.")
            return
        players[uid]["money"] -= price
        players[uid]["rod"] = chosen
        players[uid]["rod_dur"] = RODS[chosen]["durability"]
        save_data()
        await ctx.send(f"✅ Bạn đã mua {chosen} và trang bị nó. ({format_money(price)})")
    else:
        price = BAITS[chosen]["price"]
        if players[uid]["money"] < price:
            await ctx.send("❌ Bạn không đủ Coincat để mua.")
            return
        players[uid]["money"] -= price
        players[uid]["bait"] = chosen
        players[uid]["bait_dur"] = BAITS[chosen]["durability"]
        save_data()
        await ctx.send(f"✅ Bạn đã mua {chosen}. ({format_money(price)})")

@bot.command(name="khodo")
async def cmd_khodo(ctx):
    """:khodo - xem kho đồ (các con cá đang có)"""
    uid = str(ctx.author.id)
    ensure_player(uid)
    inv = players[uid]["inventory"]
    if not inv:
        await ctx.send("🎒 Kho của bạn trống rỗng.")
        return
    lines = [f"{qty}x {name}" for name,qty in inv.items()]
    embed = discord.Embed(title=f"🎒 Kho đồ của {ctx.author.display_name}", color=discord.Color.gold())
    embed.add_field(name="Các con cá", value="\n".join(lines), inline=False)
    embed.add_field(name="Số dư", value=format_money(players[uid]["money"]), inline=True)
    embed.add_field(name="Cần / Mồi", value=f"{players[uid]['rod']} | {players[uid]['bait']}", inline=True)
    await ctx.send(embed=embed)

@bot.command(name="sotien")
async def cmd_sotien(ctx):
    """:sotien - xem tiền Coincat"""
    uid = str(ctx.author.id)
    ensure_player(uid)
    await ctx.send(f"{ctx.author.mention}, bạn có {format_money(players[uid]['money'])}")

@bot.command(name="chuyentien")
async def cmd_chuyentien(ctx, member: discord.Member, amount: int):
    """:chuyentien <@user> <amount> - chuyển tiền (giới hạn 300000)"""
    uid_from = str(ctx.author.id)
    uid_to = str(member.id)
    ensure_player(uid_from)
    ensure_player(uid_to)
    if amount <= 0:
        await ctx.send("Số tiền phải lớn hơn 0.")
        return
    if amount > 300000:
        await ctx.send("Giới hạn chuyển tối đa là 300000 Coincat.")
        return
    if players[uid_from]["money"] < amount:
        await ctx.send("Bạn không đủ Coincat để chuyển.")
        return
    players[uid_from]["money"] -= amount
    players[uid_to]["money"] += amount
    save_data()
    await ctx.send(f"✅ {ctx.author.mention} đã chuyển {format_money(amount)} cho {member.mention}")

# ========================== SLASH COMMANDS ==========================
@tree.command(name="cauca", description="Câu cá và nhận phần thưởng!")
async def slash_cauca(interaction: discord.Interaction):
    await interaction.response.defer()
    ctx = await bot.get_context(await interaction.channel.send(f"{interaction.user.mention} dùng slash /cauca"))
    await cauca(ctx)

@tree.command(name="banca", description="Bán cá trong kho đồ")
@app_commands.describe(loai="Tên cá muốn bán hoặc 'all' để bán tất cả")
async def slash_banca(interaction: discord.Interaction, loai: str):
    await interaction.response.defer()
    ctx = await bot.get_context(await interaction.channel.send(f"{interaction.user.mention} dùng slash /banca {loai}"))
    await banca(ctx, loai)

@tree.command(name="cuahang", description="Xem cửa hàng")
async def slash_cuahang(interaction: discord.Interaction):
    await interaction.response.defer()
    ctx = await bot.get_context(await interaction.channel.send(f"{interaction.user.mention} dùng slash /cuahang"))
    await cuahang(ctx)

@tree.command(name="mua", description="Mua vật phẩm trong cửa hàng")
@app_commands.describe(ten="Tên vật phẩm muốn mua")
async def slash_mua(interaction: discord.Interaction, ten: str):
    await interaction.response.defer()
    ctx = await bot.get_context(await interaction.channel.send(f"{interaction.user.mention} dùng slash /mua {ten}"))
    await mua(ctx, ten)

@tree.command(name="khodo", description="Xem kho đồ")
async def slash_khodo(interaction: discord.Interaction):
    await interaction.response.defer()
    ctx = await bot.get_context(await interaction.channel.send(f"{interaction.user.mention} dùng slash /khodo"))
    await khodo(ctx)

@tree.command(name="sotien", description="Xem số tiền bạn đang có")
async def slash_sotien(interaction: discord.Interaction):
    await interaction.response.defer()
    ctx = await bot.get_context(await interaction.channel.send(f"{interaction.user.mention} dùng slash /sotien"))
    await sotien(ctx)

@tree.command(name="chuyentien", description="Chuyển tiền cho người khác")
@app_commands.describe(nguoi="Người nhận", so_tien="Số tiền muốn chuyển (<= 300000)")
async def slash_chuyentien(interaction: discord.Interaction, nguoi: discord.User, so_tien: int):
    await interaction.response.defer()
    ctx = await bot.get_context(await interaction.channel.send(f"{interaction.user.mention} dùng slash /chuyentien {nguoi.mention} {so_tien}"))
    await chuyentien(ctx, nguoi, so_tien)

# ========================== WEB SERVICE (KEEP-ALIVE) ==========================
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Fishing Bot is alive!"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ========================== START BOT ==========================
if __name__ == "__main__":
    keep_alive()
    token = os.getenv("DISCORD_TOKEN")
    bot.run(token)
