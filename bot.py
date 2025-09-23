import discord
from discord.ext import commands
import random
import json
import os
from flask import Flask
import threading

# ===== Flask keep-alive =====
app = Flask(__name__)
@app.route("/")
def home():
    return "🎣 Fishing Bot is running!"

# ===== Bot setup =====
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)  # help_command=None để dùng !help custom

DATA_FILE = "data.json"
ADMIN_ID = 1199321278637678655

# ===== Load / Save Data =====
def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE,"w") as f:
            json.dump({"players":{}, "fish":[], "rods":[], "baits":[]}, f)
    with open(DATA_FILE,"r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE,"w") as f:
        json.dump(data,f,indent=4,ensure_ascii=False)

# ===== Initialize Game Data =====
def init_game_data():
    data = load_data()
    if not data["fish"]:
        data["fish"] = [
            # Common 30%
            {"name":"🐟 Cá Chép Vàng","rarity":"common","price":20,"chance":0.075},
            {"name":"🐠 Cá Trôi Bạc","rarity":"common","price":25,"chance":0.075},
            {"name":"🐡 Cá Vàng Xinh","rarity":"common","price":30,"chance":0.075},
            {"name":"🐟 Cá Hồng Phớt","rarity":"common","price":20,"chance":0.075},
            {"name":"🐠 Cá Chim Xanh","rarity":"common","price":25,"chance":0.075},
            {"name":"🐡 Cá Lóc Nâu","rarity":"common","price":30,"chance":0.075},
            {"name":"🐟 Cá Trôi Cam","rarity":"common","price":20,"chance":0.075},
            {"name":"🐠 Cá Chạch Vàng","rarity":"common","price":25,"chance":0.075},
            {"name":"🐡 Cá Vược","rarity":"common","price":30,"chance":0.075},
            {"name":"🐟 Cá Trê","rarity":"common","price":20,"chance":0.075},
            # Uncommon 26%
            {"name":"🐠 Cá Tầm Xanh","rarity":"uncommon","price":50,"chance":0.043},
            {"name":"🐡 Cá Rồng Nho","rarity":"uncommon","price":55,"chance":0.043},
            {"name":"🐟 Cá Hồi Cam","rarity":"uncommon","price":60,"chance":0.043},
            {"name":"🐠 Cá Ngừ Đại Dương","rarity":"uncommon","price":50,"chance":0.043},
            {"name":"🐡 Cá Mú Đỏ","rarity":"uncommon","price":55,"chance":0.043},
            {"name":"🐟 Cá Bơn Xanh","rarity":"uncommon","price":60,"chance":0.043},
            {"name":"🐠 Cá Thu Trắng","rarity":"uncommon","price":50,"chance":0.043},
            {"name":"🐡 Cá Chình Vàng","rarity":"uncommon","price":55,"chance":0.043},
            {"name":"🐟 Cá Hổ Phớt","rarity":"uncommon","price":60,"chance":0.043},
            {"name":"🐠 Cá Sấu Mini","rarity":"uncommon","price":50,"chance":0.043},
            # Rare 20%
            {"name":"🐡 Cá Ngừ Khổng Lồ","rarity":"rare","price":200,"chance":0.05},
            {"name":"🐟 Cá Mú Hoàng","rarity":"rare","price":250,"chance":0.05},
            {"name":"🐠 Cá Bơn Đại Dương","rarity":"rare","price":220,"chance":0.05},
            {"name":"🐡 Cá Thu Vàng","rarity":"rare","price":210,"chance":0.05},
            {"name":"🐟 Cá Lăng Xanh","rarity":"rare","price":230,"chance":0.05},
            {"name":"🐠 Cá Chim Vàng","rarity":"rare","price":200,"chance":0.05},
            {"name":"🐡 Cá Chạch Cam","rarity":"rare","price":250,"chance":0.05},
            {"name":"🐟 Cá Trê Đại Dương","rarity":"rare","price":220,"chance":0.05},
            # Epic 15%
            {"name":"🐠 Cá Chim Hoàng","rarity":"epic","price":500,"chance":0.0375},
            {"name":"🐡 Cá Lóc Hoàng Kim","rarity":"epic","price":550,"chance":0.0375},
            {"name":"🐟 Cá Hồng Đại Dương","rarity":"epic","price":600,"chance":0.0375},
            {"name":"🐠 Cá Ngừ Titan","rarity":"epic","price":500,"chance":0.0375},
            {"name":"🐡 Cá Rồng Vương","rarity":"epic","price":550,"chance":0.0375},
            # Legend 6%
            {"name":"🐟 Cá Chình Vương","rarity":"legend","price":2000,"chance":0.03},
            {"name":"🐠 Cá Sấu Vàng","rarity":"legend","price":2500,"chance":0.03},
            {"name":"🐡 Cá Hổ Titan","rarity":"legend","price":2200,"chance":0.03},
            # Mythic 2.9%
            {"name":"🐟 Cá Vua Đại Dương","rarity":"mythic","price":30000,"chance":0.0145},
            {"name":"🐠 Cá Rồng Biển","rarity":"mythic","price":50000,"chance":0.0145},
            # Exotic 0.1%
            {"name":"🐡 Cá Rồng Thần","rarity":"exotic","price":200000,"chance":0.001}
        ]
    if not data["rods"]:
        data["rods"] = [
            {"name":"🎣 Shimano FX","price":500,"luck":1},
            {"name":"🎣 Daiwa Pro","price":1000,"luck":1.1},
            {"name":"🎣 Abu Garcia","price":5000,"luck":1.2},
            {"name":"🎣 Penn Battle","price":10000,"luck":1.3},
            {"name":"🎣 Okuma Carbon","price":50000,"luck":1.5},
            {"name":"🎣 St. Croix Legend","price":100000,"luck":1.7},
            {"name":"🎣 G. Loomis NRX","price":500000,"luck":2},
            {"name":"🎣 Fenwick Elite","price":1000000,"luck":2.2},
            {"name":"🎣 Tsunami Elite","price":5000000,"luck":2.5},
            {"name":"🎣 Megaforce X","price":10000000,"luck":3},
            {"name":"🎣 Titan Power","price":50000000,"luck":3.5},
            {"name":"🎣 King Rod","price":100000000,"luck":4},
            {"name":"🎣 Supreme Pro","price":500000000,"luck":4.5},
            {"name":"🎣 Ultimate Legend","price":1000000000,"luck":5}
        ]
    if not data["baits"]:
        data["baits"] = [
            {"name":"🪱 Giun Đất","price":500,"luck":1},
            {"name":"🪱 Sâu Trắng","price":1000,"luck":1.1},
            {"name":"🦐 Tép Sống","price":2000,"luck":1.15},
            {"name":"🥚 Trứng Cá","price":5000,"luck":1.2},
            {"name":"🦑 Mực Tươi","price":10000,"luck":1.3},
            {"name":"🦐 Tôm Biển","price":50000,"luck":1.5},
            {"name":"✨ Mồi Đặc Biệt","price":100000,"luck":1.7},
            {"name":"💎 Mồi Hảo Hạng","price":500000,"luck":2},
            {"name":"🪄 Mồi Siêu","price":1000000,"luck":2.2},
            {"name":"🥇 Mồi Vàng","price":5000000,"luck":2.5},
            {"name":"💎 Mồi Kim Cương","price":10000000,"luck":3},
            {"name":"🛡️ Mồi Titan","price":50000000,"luck":3.5},
            {"name":"🏆 Mồi Hoàng Kim","price":100000000,"luck":4},
            {"name":"👑 Mồi Vua","price":500000000,"luck":4.5},
            {"name":"🐉 Mồi Rồng","price":1000000000,"luck":5}
        ]
    save_data(data)

# ===== Initialize =====
init_game_data()

# ===== Helper functions =====
def get_player(user_id):
    data = load_data()
    if str(user_id) not in data["players"]:
        data["players"][str(user_id)] = {
            "coin":1000,
            "level":1,
            "exp":0,
            "fish_caught":{},
            "inventory":{"rods":{},"baits":{}},
            "daily_transfer":0
        }
        save_data(data)
    return data["players"][str(user_id)]

def save_player(user_id, player):
    data = load_data()
    data["players"][str(user_id)] = player
    save_data(data)

def get_fish_by_name(name):
    data = load_data()
    for f in data["fish"]:
        if f["name"].lower() == name.lower():
            return f
    return None

def get_item_by_name(category,name):
    data = load_data()
    for i in data[category]:
        if i["name"].lower() == name.lower():
            return i
    return None
# ===== Bot Events =====
@bot.event
async def on_ready():
    print(f"{bot.user} is online!")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(e)

# ===== !help / /help =====
@bot.command()
async def help(ctx):
    embed = discord.Embed(title="🎣 Fishing Bot Commands", color=0x1abc9c)
    embed.add_field(name="!cauca", value="Câu cá (mỗi lần 1-5 con)", inline=False)
    embed.add_field(name="!banca <tên cá> <số lượng>", value="Bán cá", inline=False)
    embed.add_field(name="!banca all", value="Bán tất cả cá", inline=False)
    embed.add_field(name="!cuahang", value="Xem cửa hàng", inline=False)
    embed.add_field(name="!mua <tên vật phẩm> <số lượng>", value="Mua vật phẩm", inline=False)
    embed.add_field(name="!khodo", value="Xem kho đồ", inline=False)
    embed.add_field(name="!profile", value="Xem thông tin cá nhân", inline=False)
    embed.add_field(name="!chuyentien <@user> <số tiền>", value="Chuyển tiền (giới hạn 1,000,000 Coincat/ngày)", inline=False)
    embed.add_field(name="!admintang <@user> <số tiền>", value="Admin tăng tiền không giới hạn", inline=False)
    await ctx.send(embed=embed)

# ===== !cuahang =====
@bot.command()
async def cuahang(ctx):
    data = load_data()
    embed = discord.Embed(title="🏪 Cửa Hàng", color=0x3498db)
    rods = "\n".join([f"{r['name']} - {r['price']} Coincat - Luck: {r['luck']}" for r in data["rods"]])
    baits = "\n".join([f"{b['name']} - {b['price']} Coincat - Luck: {b['luck']}" for b in data["baits"]])
    embed.add_field(name="🎣 Cần câu", value=rods, inline=False)
    embed.add_field(name="🪱 Mồi câu", value=baits, inline=False)
    await ctx.send(embed=embed)

# ===== !mua =====
@bot.command()
async def mua(ctx, name:str, amount:int=1):
    player = get_player(ctx.author.id)
    item = get_item_by_name("rods", name) or get_item_by_name("baits", name)
    if not item:
        await ctx.send("❌ Vật phẩm không tồn tại!")
        return
    total_price = item["price"]*amount
    if player["coin"] < total_price:
        await ctx.send("❌ Bạn không đủ Coincat!")
        return
    player["coin"] -= total_price
    category = "rods" if item in load_data()["rods"] else "baits"
    if item["name"] in player["inventory"][category]:
        player["inventory"][category][item["name"]] += amount
    else:
        player["inventory"][category][item["name"]] = amount
    save_player(ctx.author.id, player)
    await ctx.send(f"✅ Bạn đã mua {amount} x {item['name']}")

# ===== !khodo =====
@bot.command()
async def khodo(ctx):
    player = get_player(ctx.author.id)
    embed = discord.Embed(title=f"🧰 Kho đồ của {ctx.author.display_name}", color=0xf1c40f)
    rods = "\n".join([f"{k} x{v}" for k,v in player["inventory"]["rods"].items()]) or "Không có"
    baits = "\n".join([f"{k} x{v}" for k,v in player["inventory"]["baits"].items()]) or "Không có"
    fish = "\n".join([f"{k} x{v}" for k,v in player["fish_caught"].items()]) or "Không có"
    embed.add_field(name="🎣 Cần câu", value=rods, inline=False)
    embed.add_field(name="🪱 Mồi câu", value=baits, inline=False)
    embed.add_field(name="🐟 Cá", value=fish, inline=False)
    await ctx.send(embed=embed)

# ===== !profile =====
@bot.command()
async def profile(ctx):
    player = get_player(ctx.author.id)
    embed = discord.Embed(title=f"👤 Profile {ctx.author.display_name}", color=0x9b59b6)
    embed.add_field(name="💰 Coincat", value=str(player["coin"]))
    embed.add_field(name="🎣 Cá bắt được", value=sum(player["fish_caught"].values()))
    embed.add_field(name="📈 Level", value=player["level"])
    await ctx.send(embed=embed)

# ===== !cauca =====
@bot.command()
async def cauca(ctx):
    player = get_player(ctx.author.id)
    data = load_data()
    caught = {}
    num_fish = random.randint(1,5)
    for _ in range(num_fish):
        r = random.random()
        total = 0
        for f in data["fish"]:
            total += f["chance"]
            if r <= total:
                caught[f["name"]] = caught.get(f["name"],0)+1
                player["fish_caught"][f["name"]] = player["fish_caught"].get(f["name"],0)+1
                break
    save_player(ctx.author.id, player)
    embed = discord.Embed(title="🎣 Kết quả câu cá", color=0x1abc9c)
    for k,v in caught.items():
        embed.add_field(name=k, value=f"x{v}", inline=True)
    await ctx.send(embed=embed)

# ===== !banca =====
@bot.command()
async def banca(ctx, name:str=None, amount:int=None):
    player = get_player(ctx.author.id)
    if name=="all":
        total = sum([get_fish_by_name(f)["price"]*v for f,v in player["fish_caught"].items()])
        player["coin"] += total
        player["fish_caught"] = {}
        save_player(ctx.author.id, player)
        await ctx.send(f"💰 Bạn đã bán tất cả cá và nhận {total} Coincat")
        return
    fish = get_fish_by_name(name)
    if not fish or name not in player["fish_caught"]:
        await ctx.send("❌ Bạn không có cá này!")
        return
    if amount is None or amount>player["fish_caught"][name]:
        amount = player["fish_caught"][name]
    player["coin"] += fish["price"]*amount
    player["fish_caught"][name] -= amount
    if player["fish_caught"][name]==0:
        del player["fish_caught"][name]
    save_player(ctx.author.id, player)
    await ctx.send(f"💰 Bạn đã bán {amount} x {name} nhận {fish['price']*amount} Coincat")

# ===== !chuyentien =====
@bot.command()
async def chuyentien(ctx, member:discord.Member, amount:int):
    sender = get_player(ctx.author.id)
    receiver = get_player(member.id)
    if amount>1000000 or amount>sender["coin"]:
        await ctx.send("❌ Không thể chuyển số tiền này!")
        return
    sender["coin"] -= amount
    receiver["coin"] += amount
    save_player(ctx.author.id, sender)
    save_player(member.id, receiver)
    await ctx.send(f"✅ {ctx.author.display_name} đã chuyển {amount} Coincat cho {member.display_name}")

# ===== !admintang =====
@bot.command()
async def admintang(ctx, member:discord.Member, amount:int):
    if ctx.author.id != ADMIN_ID:
        await ctx.send("❌ Bạn không có quyền!")
        return
    player = get_player(member.id)
    player["coin"] += amount
    save_player(member.id, player)
    await ctx.send(f"✅ Admin đã tăng {amount} Coincat cho {member.display_name}")

# ===== Keep bot online on Render =====
def run_flask():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_flask).start()

# ===== Run bot =====
bot.run("YOUR_BOT_TOKEN_HERE")
    
