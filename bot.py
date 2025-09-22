import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
import sqlite3
import os
import time
from flask import Flask
import threading
import json

TOKEN = "YOUR_BOT_TOKEN"
ADMIN_ID = 1199321278637678655

# ============ DATABASE ============ #
conn = sqlite3.connect("fishing.db")
cur = conn.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    money INTEGER DEFAULT 0,
    inventory TEXT DEFAULT '{}',
    cooldown REAL DEFAULT 3.0,
    last_reset INTEGER DEFAULT 0
)""")
conn.commit()

def get_user(user_id: int):
    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    if not row:
        cur.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        return get_user(user_id)
    return row

def update_user(user_id: int, money=None, inventory=None, cooldown=None, last_reset=None):
    if money is not None:
        cur.execute("UPDATE users SET money=? WHERE user_id=?", (money, user_id))
    if inventory is not None:
        cur.execute("UPDATE users SET inventory=? WHERE user_id=?", (inventory, user_id))
    if cooldown is not None:
        cur.execute("UPDATE users SET cooldown=? WHERE user_id=?", (cooldown, user_id))
    if last_reset is not None:
        cur.execute("UPDATE users SET last_reset=? WHERE user_id=?", (last_reset, user_id))
    conn.commit()

# ============ BOT CONFIG ============ #
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=":", intents=intents)
tree = bot.tree

# ============ KEEP ALIVE FOR RENDER ============ #
app = Flask("")

@app.route('/')
def home():
    return "Fishing Bot is running!"

def run():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

# ============ GAME DATA ============ #
fish_list = {
    "common": [
        ("🐟 Cá chép", 20*2), ("🐠 Cá rô", 25*2), ("🐡 Cá nóc", 30*2),
        ("🎏 Cá cảnh", 15*2), ("🐟 Cá trích", 18*2), ("🐠 Cá bống", 22*2)
    ],
    "uncommon": [
        ("🦑 Mực", 50*2), ("🦐 Tôm", 60*2), ("🦞 Tôm hùm", 70*2),
        ("🦀 Cua", 65*2), ("🐟 Cá mòi", 55*2)
    ],
    "rare": [
        ("🐬 Cá heo", 200*2), ("🐳 Cá voi con", 250*2),
        ("🐋 Cá voi xanh", 300*2), ("🦭 Hải cẩu", 180*2)
    ],
    "epic": [
        ("🦈 Cá mập", 500*2), ("🐉 Rồng biển", 700*2),
        ("🐊 Cá sấu", 650*2), ("🐢 Rùa biển", 400*2)
    ],
    "legendary": [
        ("🐲 Thần ngư", 1500*2), ("🐉 Cá rồng đen", 2000*2),
        ("🐅 Cá hổ Amazon", 1800*2)
    ],
    "mythic": [
        ("🐧 Cá băng", 3000*2), ("🔥 Cá lửa", 3500*2),
        ("⚡ Cá sét", 4000*2)
    ],
    "exotic": [
        ("🐉 Cá rồng vàng", 10000*2), ("👑 Cá hoàng đế", 15000*2),
        ("💎 Cá kim cương", 20000*2)
    ]
}

rods = {
    "Cần tre": 100*10, "Cần gỗ": 200*10, "Cần đồng": 300*10,
    "Cần sắt": 500*10, "Cần thép": 800*10, "Cần bạc": 1200*10,
    "Cần vàng": 2000*10, "Cần ruby": 3000*10, "Cần sapphire": 5000*10,
    "Cần emerald": 7000*10, "Cần platinum": 10000*10,
    "Cần kim cương": 15000*10, "Cần obsidian": 20000*10,
    "Cần thần thánh": 30000*10, "Cần huyền thoại": 50000*10,
    "Cần rồng": 70000*10, "Cần ma thuật": 100000*10,
    "Cần thiên giới": 150000*10, "Cần vũ trụ": 200000*10,
    "Cần tuyệt thế": 300000*10
}

baits = {
    "Mồi thường": 10*100, "Mồi cá khô": 20*100, "Mồi bánh mì": 30*100,
    "Mồi trùn": 40*100, "Mồi dế": 50*100, "Mồi tép": 60*100,
    "Mồi cá nhỏ": 80*100, "Mồi thịt": 100*100, "Mồi thơm": 150*100,
    "Mồi bí ẩn": 200*100, "Mồi đặc biệt": 300*100, "Mồi VIP": 500*100,
    "Mồi kim cương": 1000*100, "Mồi vàng": 2000*100, "Mồi ruby": 3000*100,
    "Mồi sapphire": 4000*100, "Mồi emerald": 5000*100,
    "Mồi platinum": 7000*100, "Mồi huyền thoại": 10000*100,
    "Mồi ma thuật": 15000*100, "Mồi rồng": 20000*100,
    "Mồi thiên giới": 30000*100, "Mồi vũ trụ": 50000*100,
    "Mồi tuyệt thế": 100000*100
}

# ============ HELPER FUNCTIONS ============ #
def add_inventory(user_id, item, amount=1):
    row = get_user(user_id)
    inv = json.loads(row[2])
    inv[item] = inv.get(item, 0) + amount
    update_user(user_id, inventory=json.dumps(inv))

def remove_inventory(user_id, item, amount=1):
    row = get_user(user_id)
    inv = json.loads(row[2])
    if inv.get(item, 0) >= amount:
        inv[item] -= amount
        if inv[item] <= 0:
            del inv[item]
        update_user(user_id, inventory=json.dumps(inv))
        return True
    return False

def get_inventory(user_id):
    row = get_user(user_id)
    return json.loads(row[2])

# ============ EVENTS ============ #
@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot {bot.user} is online!")

# ============ COMMANDS ============ #
@tree.command(name="sotien", description="Xem số tiền bạn đang có")
async def sotien(interaction: discord.Interaction):
    row = get_user(interaction.user.id)
    embed = discord.Embed(title="💶 Số tiền", description=f"Bạn đang có **{row[1]} Coincat**", color=0x00ff00)
    await interaction.response.send_message(embed=embed)

@tree.command(name="cuahang", description="Xem cửa hàng bán cần và mồi")
async def cuahang(interaction: discord.Interaction):
    embed = discord.Embed(title="🛒 Cửa hàng", color=0xffd700)
    rod_text = "\n".join([f"🎣 {r} - {p}💶" for r, p in rods.items()])
    bait_text = "\n".join([f"🪱 {b} - {p}💶" for b, p in baits.items()])
    embed.add_field(name="Cần câu", value=rod_text, inline=False)
    embed.add_field(name="Mồi câu", value=bait_text, inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name="mua", description="Mua vật phẩm từ cửa hàng")
async def mua(interaction: discord.Interaction, ten_vat_pham: str, so_luong: int = 1):
    row = get_user(interaction.user.id)

    if ten_vat_pham in rods:
        cost = rods[ten_vat_pham] * so_luong
    elif ten_vat_pham in baits:
        cost = baits[ten_vat_pham] * so_luong
    else:
        await interaction.response.send_message("❌ Không tìm thấy vật phẩm!", ephemeral=True)
        return

    if row[1] >= cost:
        update_user(interaction.user.id, money=row[1] - cost)
        add_inventory(interaction.user.id, ten_vat_pham, so_luong)
        await interaction.response.send_message(f"✅ Bạn đã mua {so_luong} **{ten_vat_pham}** với giá {cost}💶")
    else:
        await interaction.response.send_message("❌ Bạn không đủ tiền!", ephemeral=True)
    # ========================== FISHING (CÂU CÁ) ========================== #
@tree.command(name="cauca", description="Câu cá và nhận phần thưởng!")
async def cauca(interaction: discord.Interaction):
    user_id = interaction.user.id
    row = get_user(user_id)

    # Reset cooldown sau 1 tiếng
    now = int(time.time())
    if now - row[4] >= 3600:
        update_user(user_id, cooldown=3.0, last_reset=now)
        row = get_user(user_id)

    cooldown = row[3]
    if hasattr(interaction.user, "last_used") and time.time() - interaction.user.last_used < cooldown:
        wait_time = round(cooldown - (time.time() - interaction.user.last_used), 1)
        await interaction.response.send_message(f"⏳ Bạn phải chờ {wait_time} giây nữa mới được câu tiếp!", ephemeral=True)
        return

    interaction.user.last_used = time.time()
    update_user(user_id, cooldown=cooldown + 0.2)

    # Xác suất ra cá
    roll = random.randint(1, 1000)
    if roll <= 400: rarity = "common"
    elif roll <= 650: rarity = "uncommon"
    elif roll <= 850: rarity = "rare"
    elif roll <= 950: rarity = "epic"
    elif roll <= 990: rarity = "legendary"
    elif roll <= 999: rarity = "mythic"
    else: rarity = "exotic"

    fish, price = random.choice(fish_list[rarity])
    add_inventory(user_id, fish, 1)

    embed = discord.Embed(title="🎣 Bạn đã câu cá!", color=0x1abc9c)
    embed.add_field(name="Loại cá", value=f"{fish} ({rarity.upper()})", inline=False)
    embed.add_field(name="Giá trị", value=f"{price} Coincat", inline=False)
    await interaction.response.send_message(embed=embed)


# ========================== BÁN CÁ ========================== #
@tree.command(name="banca", description="Bán cá trong kho của bạn")
async def banca(interaction: discord.Interaction, ten_ca: str = "all"):
    user_id = interaction.user.id
    row = get_user(user_id)
    inv = get_inventory(user_id)
    total_money = row[1]

    if ten_ca.lower() == "all":
        sell_money = 0
        for rarity, fishes in fish_list.items():
            for fish, price in fishes:
                if fish in inv:
                    sell_money += price * inv[fish]
                    inv[fish] = 0
        update_user(user_id, money=total_money + sell_money, inventory=json.dumps(inv))
        await interaction.response.send_message(f"💰 Bạn đã bán tất cả cá và nhận được {sell_money} Coincat!")
    else:
        for rarity, fishes in fish_list.items():
            for fish, price in fishes:
                if fish == ten_ca:
                    if inv.get(fish, 0) > 0:
                        sell_money = price * inv[fish]
                        inv[fish] = 0
                        update_user(user_id, money=total_money + sell_money, inventory=json.dumps(inv))
                        await interaction.response.send_message(f"✅ Bạn đã bán {fish} và nhận {sell_money} Coincat!")
                        return
                    else:
                        await interaction.response.send_message("❌ Bạn không có cá này!", ephemeral=True)
                        return
        await interaction.response.send_message("❌ Không tìm thấy cá!", ephemeral=True)


# ========================== KHO ĐỒ ========================== #
@tree.command(name="khodo", description="Xem kho đồ của bạn")
async def khodo(interaction: discord.Interaction):
    user_id = interaction.user.id
    inv = get_inventory(user_id)

    embed = discord.Embed(title=f"📦 Kho đồ của {interaction.user.name}", color=0x3498db)

    # Chia theo dòng cá
    for rarity, fishes in fish_list.items():
        items = []
        for fish, _ in fishes:
            if fish in inv:
                items.append(f"{fish} x{inv[fish]}")
        if items:
            embed.add_field(name=f"{rarity.upper()} fish", value="\n".join(items), inline=False)

    # Cần & mồi
    rods_items = [f"🎣 {r} x{inv[r]}" for r in rods if r in inv]
    baits_items = [f"🪱 {b} x{inv[b]}" for b in baits if b in inv]
    if rods_items:
        embed.add_field(name="Cần câu", value="\n".join(rods_items), inline=False)
    if baits_items:
        embed.add_field(name="Mồi câu", value="\n".join(baits_items), inline=False)

    await interaction.response.send_message(embed=embed)


# ========================== CHUYỂN TIỀN ========================== #
@tree.command(name="chuyentien", description="Chuyển tiền cho người khác (tối đa 300000)")
async def chuyentien(interaction: discord.Interaction, nguoinhan: discord.Member, so_tien: int):
    if so_tien <= 0 or so_tien > 300000:
        await interaction.response.send_message("❌ Số tiền không hợp lệ!", ephemeral=True)
        return

    row = get_user(interaction.user.id)
    if row[1] < so_tien:
        await interaction.response.send_message("❌ Bạn không đủ tiền!", ephemeral=True)
        return

    # Trừ tiền người gửi
    update_user(interaction.user.id, money=row[1] - so_tien)

    # Cộng tiền người nhận
    row_receiver = get_user(nguoinhan.id)
    update_user(nguoinhan.id, money=row_receiver[1] + so_tien)

    await interaction.response.send_message(f"💸 Bạn đã chuyển {so_tien} Coincat cho {nguoinhan.mention}!")


# ========================== ADMIN GIVE ========================== #
@tree.command(name="admingive", description="Tặng tiền không giới hạn (ADMIN ONLY)")
async def admingive(interaction: discord.Interaction, nguoinhan: discord.Member, so_tien: int):
    if interaction.user.id != ADMIN_ID:
        await interaction.response.send_message("❌ Bạn không có quyền dùng lệnh này!", ephemeral=True)
        return

    row_receiver = get_user(nguoinhan.id)
    update_user(nguoinhan.id, money=row_receiver[1] + so_tien)

    await interaction.response.send_message(f"👑 {nguoinhan.mention} đã được cộng {so_tien} Coincat bởi ADMIN!")


# ========================== START BOT ========================== #
keep_alive()
bot.run(TOKEN)
    
