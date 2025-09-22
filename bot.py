import discord
from discord.ext import commands
import random, asyncio, json, os
from discord import app_commands
from flask import Flask
from threading import Thread

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=":", intents=intents)
tree = bot.tree

DATA_FILE = "data.json"

# ============ DATABASE ============
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

players = load_data()

# ============ ECONOMY CONFIG =========
fish_rarities = {
    "Common": {"emoji": "🐟"},
    "Uncommon": {"emoji": "🐠"},
    "Rare": {"emoji": "🐡"},
    "Epic": {"emoji": "🦑"},
    "Legendary": {"emoji": "🦈"},
    "Mythic": {"emoji": "🐉"},
    "Exotic": {"emoji": "🐋"}
}

# Cá với giá trị riêng
fishes = {
    "Common": {
        "Cá trê": 20, "Cá chép": 25, "Cá rô phi": 30, "Cá cơm": 15, "Cá lóc": 40, "Cá mè": 35, "Cá chuối": 28
    },
    "Uncommon": {
        "Cá thu": 60, "Cá ngừ": 80, "Cá đối": 50, "Cá bống": 45, "Cá nhám nhỏ": 70, "Cá mòi": 65, "Cá trích": 75
    },
    "Rare": {
        "Cá hồi": 200, "Cá nục": 250, "Cá chim": 300, "Cá tráp": 280, "Cá nhồng": 350, "Cá mú": 320, "Cá sòng": 270
    },
    "Epic": {
        "Cá mập nhỏ": 500, "Cá đuối": 600, "Cá nhám": 700, "Cá đao": 800, "Cá mò": 750, "Cá ngát": 650, "Cá sấu nước ngọt": 900
    },
    "Legendary": {
        "Cá heo": 3000, "Cá kiếm": 5000, "Cá voi xanh": 8000, "Cá voi lưng gù": 7500, "Cá ngựa biển khổng lồ": 6000, "Cá sấu khổng lồ": 4000, "Cá mập trắng": 9000
    },
    "Mythic": {
        "Kraken": 20000, "Cá rồng": 30000, "Cá tiên": 25000, "Leviathan": 40000, "Cá phượng hoàng": 35000, "Cá thần thoại": 45000, "Cá ma": 28000
    },
    "Exotic": {
        "CatFish": 100000, "Megalodon": 250000
    }
}

# Cần câu - khoảng 20 cây
rods = {
    "Cần tre": {"price": 1000, "luck": 1},
    "Cần gỗ": {"price": 5000, "luck": 2},
    "Cần sắt": {"price": 20000, "luck": 4},
    "Cần đồng": {"price": 50000, "luck": 6},
    "Cần bạc": {"price": 100000, "luck": 8},
    "Cần vàng": {"price": 300000, "luck": 10},
    "Cần bạch kim": {"price": 800000, "luck": 12},
    "Cần titan": {"price": 2000000, "luck": 15},
    "Cần ruby": {"price": 5000000, "luck": 20},
    "Cần kim cương": {"price": 10000000, "luck": 25},
    "Cần thiên thần": {"price": 20000000, "luck": 30},
    "Cần huyền thoại": {"price": 50000000, "luck": 40},
    "Cần bóng tối": {"price": 80000000, "luck": 50},
    "Cần ánh sáng": {"price": 100000000, "luck": 60},
    "Cần tối thượng": {"price": 200000000, "luck": 80},
    "Cần vũ trụ": {"price": 500000000, "luck": 100},
    "Cần dragon": {"price": 800000000, "luck": 150},
    "Cần immortal": {"price": 1000000000, "luck": 200},
    "Cần ultimate": {"price": 2000000000, "luck": 300},
    "Cần god": {"price": 5000000000, "luck": 500}
}

# Mồi - khoảng 15 loại
baits = {
    "Giun đất": {"price": 500, "luck": 1, "durability": 10},
    "Tôm nhỏ": {"price": 2000, "luck": 3, "durability": 15},
    "Mồi nhân tạo": {"price": 10000, "luck": 6, "durability": 25},
    "Mồi cá nhỏ": {"price": 30000, "luck": 8, "durability": 30},
    "Mồi thịt": {"price": 60000, "luck": 10, "durability": 35},
    "Mồi cá đặc biệt": {"price": 120000, "luck": 15, "durability": 40},
    "Mồi vàng": {"price": 500000, "luck": 20, "durability": 45},
    "Mồi titan": {"price": 2000000, "luck": 25, "durability": 50},
    "Mồi ruby": {"price": 5000000, "luck": 35, "durability": 55},
    "Mồi kim cương": {"price": 10000000, "luck": 50, "durability": 60},
    "Mồi huyền thoại": {"price": 50000000, "luck": 80, "durability": 70},
    "Mồi bóng tối": {"price": 100000000, "luck": 100, "durability": 80},
    "Mồi ánh sáng": {"price": 200000000, "luck": 150, "durability": 90},
    "Mồi vũ trụ": {"price": 500000000, "luck": 200, "durability": 100},
    "Mồi god": {"price": 1000000000, "luck": 300, "durability": 120}
}

# ============ INIT PLAYER ============
def init_player(user_id):
    if str(user_id) not in players:
        players[str(user_id)] = {
            "money": 1000,
            "inventory": {},
            "fishes": {},
            "level": 1,
            "exp": 0
        }
        save_data(players)

# ============ LEVEL SYSTEM ============
def add_exp(user_id, amount):
    init_player(user_id)
    player = players[str(user_id)]
    player["exp"] += amount
    level_up = False
    while player["exp"] >= player["level"] * 100:
        player["exp"] -= player["level"] * 100
        player["level"] += 1
        level_up = True
    save_data(players)
    return level_up, player["level"]

# ============ COMMANDS ================
@bot.event
async def on_ready():
    await tree.sync()
    print(f"Bot {bot.user} đã online!")

@bot.command(name="sotien")
async def sotien(ctx):
    init_player(ctx.author.id)
    money = players[str(ctx.author.id)]["money"]
    embed = discord.Embed(title="💰 Số tiền", description=f"Bạn có {money} Coincat 💶", color=0x00ff00)
    await ctx.send(embed=embed)
# =================== PHẦN 2 (tiếp nối Part 1) ===================
# Các lệnh: chuyentien, admingive, mua (mua nhiều), cuahang (nếu muốn), khodo (đã có), cauca (với tỉ lệ), cooldown, slash commands

import math
from discord.ext import commands
from discord import app_commands

ADMIN_ID = 1199321278637678655
COIN_NAME = "Coincat"
COIN_EMOJI = "💶"

# --- đảm bảo player có fields cooldown & last_used nếu part1 chưa tạo ---
def ensure_cooldown_fields(user_id):
    init_player(user_id)
    p = players[str(user_id)]
    changed = False
    if "cooldown" not in p:
        p["cooldown"] = 3.0
        changed = True
    if "last_used" not in p:
        p["last_used"] = 0.0
        changed = True
    if "exp" not in p:
        p["exp"] = 0
        changed = True
    if "level" not in p:
        p["level"] = 1
        changed = True
    if changed:
        save_data(players)

# --- cooldown check & apply (base 3s, +0.2s each use, reset after 3600s) ---
BASE_CD = 3.0
CD_STEP = 0.2
CD_RESET = 3600  # 1 hour

def can_use(user_id):
    ensure_cooldown_fields(user_id)
    p = players[str(user_id)]
    now = time.time()
    # reset if last_used older than CD_RESET
    if now - p.get("last_used", 0) >= CD_RESET:
        p["cooldown"] = BASE_CD
        save_data(players)
    remaining = p.get("cooldown", BASE_CD) - (now - p.get("last_used", 0))
    if remaining > 0:
        return False, remaining
    # allow, then increase cooldown and set last_used
    p["last_used"] = now
    p["cooldown"] = p.get("cooldown", BASE_CD) + CD_STEP
    save_data(players)
    return True, 0.0

# --- fishing logic using requested probabilities ---
# probs: common 40%, uncommon 26%, rare 18%, epic 13%, legendary 2.9%, mythic 2.9%, exotic 0.1%
RARITY_ORDER = ["Common","Uncommon","Rare","Epic","Legendary","Mythic","Exotic"]
RARITY_WEIGHTS_PERCENT = [40.0, 26.0, 18.0, 13.0, 2.9, 2.9, 0.1]

def pick_rarity_by_weights():
    # create cumulative
    total = sum(RARITY_WEIGHTS_PERCENT)
    pick = random.uniform(0, total)
    upto = 0
    for r, w in zip(RARITY_ORDER, RARITY_WEIGHTS_PERCENT):
        if upto + w >= pick:
            return r
        upto += w
    return "Common"

def do_single_fish_catch(user_id):
    # choose rarity with tiny exotic chance exactly as weights above
    rarity = pick_rarity_by_weights()
    # ensure fishes[rarity] exists and non-empty
    choices = list(fishes.get(rarity, {}).keys()) if isinstance(fishes.get(rarity, {}), dict) else fishes.get(rarity, [])
    # In your Part1 fishes mapping for prices: fishes[rarity] is dict (fish->price)
    if isinstance(fishes.get(rarity), dict):
        choices = list(fishes[rarity].keys())
    if not choices:
        # fallback: pick any common
        choices = list(fishes.get("Common", {}).keys()) if isinstance(fishes.get("Common"), dict) else fishes.get("Common", [])
    fish_name = random.choice(choices)
    # price from fishes dict (Part1 set fish->price)
    if isinstance(fishes[rarity], dict):
        price = fishes[rarity].get(fish_name, 0)
    else:
        price = 0
    return fish_name, rarity, price

# ---- command: cauca (prefix + slash) ----
@bot.command(name="cauca")
async def _cauca(ctx, times: int = 1):
    uid = ctx.author.id
    ensure_cooldown_fields(uid)
    if times < 1:
        times = 1
    if times > 10:
        times = 10
    ok, wait = can_use(uid)
    if not ok:
        await ctx.send(f"⏳ Hãy chờ {round(wait,1)}s nữa rồi mới câu tiếp nhé!")
        return
    catches = []
    for _ in range(times):
        fish, rarity, price = do_single_fish_catch(uid)
        # add to player's fishes inventory
        p = players[str(uid)]
        p["fishes"][fish] = p["fishes"].get(fish, 0) + 1
        # exp + level
        level_up, new_level = add_exp(uid, 10)
        catches.append((fish, rarity, price))
    save_data(players)
    # build embed
    import discord
    embed = discord.Embed(title="🎣 Kết quả câu cá", color=0x1abc9c)
    text = ""
    for i, (f, r, pr) in enumerate(catches, 1):
        text += f"{i}. {f} — **{r}** — Giá cơ bản: {pr} {COIN_EMOJI}\n"
    embed.description = text
    await ctx.send(embed=embed)

@tree.command(name="cauca", description="Câu cá (tối đa 10 lần)")
@app_commands.describe(times="Số lần câu (1-10)")
async def slash_cauca(interaction: discord.Interaction, times: int = 1):
    uid = interaction.user.id
    ensure_cooldown_fields(uid)
    if times < 1: times = 1
    if times > 10: times = 10
    ok, wait = can_use(uid)
    if not ok:
        await interaction.response.send_message(f"⏳ Hãy chờ {round(wait,1)}s nữa rồi mới câu tiếp nhé!", ephemeral=True)
        return
    catches = []
    for _ in range(times):
        fish, rarity, price = do_single_fish_catch(uid)
        p = players[str(uid)]
        p["fishes"][fish] = p["fishes"].get(fish, 0) + 1
        level_up, new_level = add_exp(uid, 10)
        catches.append((fish, rarity, price))
    save_data(players)
    text = ""
    for i, (f, r, pr) in enumerate(catches, 1):
        text += f"{i}. {f} — **{r}** — Giá cơ bản: {pr} {COIN_EMOJI}\n"
    await interaction.response.send_message(embed=discord.Embed(title="🎣 Kết quả câu cá", description=text, color=0x1abc9c))

# ---- command: banca (sell) ----
@bot.command(name="banca")
async def _banca(ctx, *, name: str = "all"):
    uid = ctx.author.id
    init_player(uid)
    p = players[str(uid)]
    total = 0
    details = []
    if name.lower() == "all":
        for rarity, fish_map in fishes.items():
            # fishes[rarity] is dict fish->price
            if isinstance(fish_map, dict):
                for fish, price in fish_map.items():
                    qty = p["fishes"].get(fish, 0)
                    if qty > 0:
                        gain = price * qty
                        # level bonus: +2% per level
                        gain = int(gain * (1 + p.get("level",1) * 0.02))
                        total += gain
                        details.append(f"{qty}x {fish} → {gain} {COIN_EMOJI}")
                        p["fishes"][fish] = 0
        # clear zero items
        p["fishes"] = {k:v for k,v in p["fishes"].items() if v>0}
        p["money"] = p.get("money",0) + total
        save_data(players)
        if total == 0:
            await ctx.send("📭 Bạn không có cá để bán!")
        else:
            await ctx.send(embed=discord.Embed(title="💸 Bán tất cả cá", description="\n".join(details)+f"\n\n**Tổng nhận:** {total} {COIN_EMOJI}", color=0xf1c40f))
    else:
        # match fish by substring case-insensitive
        found = None
        for rarity, fish_map in fishes.items():
            for fish, price in (fish_map.items() if isinstance(fish_map, dict) else []):
                if name.lower() in fish.lower():
                    found = (fish, price, rarity)
                    break
            if found:
                break
        if not found:
            await ctx.send("❌ Không tìm thấy loại cá phù hợp để bán.")
            return
        fish_name, price, rarity = found
        qty = p["fishes"].get(fish_name, 0)
        if qty <= 0:
            await ctx.send("❌ Bạn không có con cá này trong kho.")
            return
        gain = price * qty
        gain = int(gain * (1 + p.get("level",1) * 0.02))
        p["money"] = p.get("money",0) + gain
        p["fishes"].pop(fish_name, None)
        save_data(players)
        await ctx.send(embed=discord.Embed(title="💸 Bán cá", description=f"Bạn bán {qty}x {fish_name} và nhận {gain} {COIN_EMOJI}", color=0xf1c40f))

@tree.command(name="banca", description="Bán cá (gõ 'all' để bán hết)")
@app_commands.describe(name="Tên cá hoặc 'all'")
async def slash_banca(interaction: discord.Interaction, name: str = "all"):
    await interaction.response.defer()
    uid = interaction.user.id
    init_player(uid)
    p = players[str(uid)]
    total = 0
    details = []
    if name.lower() == "all":
        for rarity, fish_map in fishes.items():
            if isinstance(fish_map, dict):
                for fish, price in fish_map.items():
                    qty = p["fishes"].get(fish, 0)
                    if qty > 0:
                        gain = price * qty
                        gain = int(gain * (1 + p.get("level",1) * 0.02))
                        total += gain
                        details.append(f"{qty}x {fish} → {gain} {COIN_EMOJI}")
                        p["fishes"][fish] = 0
        p["fishes"] = {k:v for k,v in p["fishes"].items() if v>0}
        p["money"] = p.get("money",0) + total
        save_data(players)
        if total == 0:
            await interaction.followup.send("📭 Bạn không có cá để bán!")
        else:
            await interaction.followup.send(embed=discord.Embed(title="💸 Bán tất cả cá", description="\n".join(details)+f"\n\n**Tổng nhận:** {total} {COIN_EMOJI}", color=0xf1c40f))
    else:
        found = None
        for rarity, fish_map in fishes.items():
            for fish, price in (fish_map.items() if isinstance(fish_map, dict) else []):
                if name.lower() in fish.lower():
                    found = (fish, price, rarity)
                    break
            if found:
                break
        if not found:
            await interaction.followup.send("❌ Không tìm thấy loại cá phù hợp để bán.", ephemeral=True)
            return
        fish_name, price, rarity = found
        qty = p["fishes"].get(fish_name, 0)
        if qty <= 0:
            await interaction.followup.send("❌ Bạn không có con cá này trong kho.", ephemeral=True)
            return
        gain = price * qty
        gain = int(gain * (1 + p.get("level",1) * 0.02))
        p["money"] = p.get("money",0) + gain
        p["fishes"].pop(fish_name, None)
        save_data(players)
        await interaction.followup.send(embed=discord.Embed(title="💸 Bán cá", description=f"Bạn bán {qty}x {fish_name} và nhận {gain} {COIN_EMOJI}", color=0xf1c40f))

# ---- chuyentien & admingive ----
@bot.command(name="chuyentien")
async def _chuyentien(ctx, member: discord.Member, amount: int):
    init_player(ctx.author.id)
    init_player(member.id)
    if amount <= 0:
        await ctx.send("❌ Số tiền phải > 0.")
        return
    if amount > 300000:
        await ctx.send("⚠️ Giới hạn chuyển tối đa: 300000")
        return
    sender = players[str(ctx.author.id)]
    if sender["money"] < amount:
        await ctx.send("❌ Bạn không đủ tiền.")
        return
    sender["money"] -= amount
    players[str(member.id)]["money"] = players[str(member.id)].get("money",0) + amount
    save_data(players)
    await ctx.send(embed=discord.Embed(title="💸 Chuyển tiền", description=f"Bạn đã chuyển {amount} {COIN_EMOJI} cho {member.mention}", color=0x3498db))

@tree.command(name="chuyentien", description="Chuyển tiền (<=300000)")
@app_commands.describe(member="Người nhận", amount="Số tiền")
async def slash_chuyentien(interaction: discord.Interaction, member: discord.Member, amount: int):
    await interaction.response.defer(ephemeral=True)
    init_player(interaction.user.id)
    init_player(member.id)
    if amount <= 0:
        await interaction.followup.send("❌ Số tiền phải > 0.", ephemeral=True); return
    if amount > 300000:
        await interaction.followup.send("⚠️ Giới hạn chuyển tối đa: 300000", ephemeral=True); return
    sender = players[str(interaction.user.id)]
    if sender["money"] < amount:
        await interaction.followup.send("❌ Bạn không đủ tiền.", ephemeral=True); return
    sender["money"] -= amount
    players[str(member.id)]["money"] = players[str(member.id)].get("money",0) + amount
    save_data(players)
    await interaction.followup.send(embed=discord.Embed(title="💸 Chuyển tiền", description=f"Bạn đã chuyển {amount} {COIN_EMOJI} cho {member.mention}", color=0x3498db))

@bot.command(name="admingive")
async def _admingive(ctx, member: discord.Member, amount: int):
    if ctx.author.id != ADMIN_ID:
        await ctx.send("❌ Bạn không có quyền dùng lệnh này.")
        return
    init_player(member.id)
    players[str(member.id)]["money"] = players[str(member.id)].get("money",0) + amount
    save_data(players)
    await ctx.send(embed=discord.Embed(title="Admin", description=f"Đã tặng {amount} {COIN_EMOJI} cho {member.mention}", color=0xffd700))

@tree.command(name="admingive", description="(Admin) Tặng tiền")
@app_commands.describe(member="Người nhận", amount="Số tiền")
async def slash_admingive(interaction: discord.Interaction, member: discord.Member, amount: int):
    if interaction.user.id != ADMIN_ID:
        await interaction.response.send_message("❌ Bạn không có quyền dùng lệnh này.", ephemeral=True); return
    init_player(member.id)
    players[str(member.id)]["money"] = players[str(member.id)].get("money",0) + amount
    save_data(players)
    await interaction.response.send_message(embed=discord.Embed(title="Admin", description=f"Đã tặng {amount} {COIN_EMOJI} cho {member.mention}", color=0xffd700))

# ---- helper: shop view (if you want to call again) ----
@bot.command(name="cuahang")
async def _cuahang(ctx):
    # display rods (first ~20) and baits
    rod_lines = []
    for k,v in rods.items():
        rod_lines.append(f"{k}: {v['price']} {COIN_EMOJI}")
    bait_lines = []
    for k,v in baits.items():
        bait_lines.append(f"{k}: {v['price']} {COIN_EMOJI}")
    embed = discord.Embed(title="🏪 Cửa hàng", color=0xF39C12)
    embed.add_field(name="🎣 Cần", value="\n".join(rod_lines), inline=False)
    embed.add_field(name="🪱 Mồi", value="\n".join(bait_lines), inline=False)
    await ctx.send(embed=embed)

# ---- buy command (accepts quantity) ----
@bot.command(name="mua")
async def _mua(ctx, item: str, qty: int = 1):
    init_player(ctx.author.id)
    name = item.strip()
    # direct match in rods
    if name in rods:
        price = rods[name]["price"] * qty
        if players[str(ctx.author.id)]["money"] < price:
            await ctx.send("❌ Bạn không đủ tiền để mua.")
            return
        players[str(ctx.author.id)]["money"] -= price
        players[str(ctx.author.id)]["inventory"][name] = players[str(ctx.author.id)]["inventory"].get(name,0) + qty
        save_data(players)
        await ctx.send(embed=discord.Embed(title="Mua thành công", description=f"Bạn mua {qty}x {name} - tổng {price} {COIN_EMOJI}", color=0x2ecc71))
        return
    if name in baits:
        price = baits[name]["price"] * qty
        if players[str(ctx.author.id)]["money"] < price:
            await ctx.send("❌ Bạn không đủ tiền để mua.")
            return
        players[str(ctx.author.id)]["money"] -= price
        players[str(ctx.author.id)]["inventory"][name] = players[str(ctx.author.id)]["inventory"].get(name,0) + qty
        save_data(players)
        await ctx.send(embed=discord.Embed(title="Mua thành công", description=f"Bạn mua {qty}x {name} - tổng {price} {COIN_EMOJI}", color=0x2ecc71))
        return
    await ctx.send("❌ Không tìm thấy vật phẩm trong cửa hàng (nhập chính xác tên).")

@tree.command(name="mua", description="Mua item từ cửa hàng")
@app_commands.describe(item="Tên vật phẩm chính xác", qty="Số lượng")
async def slash_mua(interaction: discord.Interaction, item: str, qty: int = 1):
    await interaction.response.defer(ephemeral=True)
    init_player(interaction.user.id)
    name = item.strip()
    if name in rods:
        price = rods[name]["price"] * qty
        if players[str(interaction.user.id)]["money"] < price:
            await interaction.followup.send("❌ Bạn không đủ tiền để mua.", ephemeral=True); return
        players[str(interaction.user.id)]["money"] -= price
        players[str(interaction.user.id)]["inventory"][name] = players[str(interaction.user.id)]["inventory"].get(name,0) + qty
        save_data(players)
        await interaction.followup.send(embed=discord.Embed(title="Mua thành công", description=f"Bạn mua {qty}x {name} - tổng {price} {COIN_EMOJI}", color=0x2ecc71))
        return
    if name in baits:
        price = baits[name]["price"] * qty
        if players[str(interaction.user.id)]["money"] < price:
            await interaction.followup.send("❌ Bạn không đủ tiền để mua.", ephemeral=True); return
        players[str(interaction.user.id)]["money"] -= price
        players[str(interaction.user.id)]["inventory"][name] = players[str(interaction.user.id)]["inventory"].get(name,0) + qty
        save_data(players)
        await interaction.followup.send(embed=discord.Embed(title="Mua thành công", description=f"Bạn mua {qty}x {name} - tổng {price} {COIN_EMOJI}", color=0x2ecc71))
        return
    await interaction.followup.send("❌ Không tìm thấy vật phẩm trong cửa hàng (nhập chính xác tên).", ephemeral=True)

# ---------- ready event (sync slash) ----------
@bot.event
async def on_ready():
    try:
        await tree.sync()
    except Exception:
        pass
    print(f"Bot đã sẵn sàng: {bot.user}")

# ================= END PART 2 ===================
