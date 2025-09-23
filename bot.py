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
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

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
            {"name":"🐟 Cá Chép","rarity":"common","price":20,"chance":0.075},
            {"name":"🐠 Cá Trê","rarity":"common","price":25,"chance":0.075},
            {"name":"🐡 Cá Rô","rarity":"common","price":30,"chance":0.075},
            {"name":"🐟 Cá Lóc","rarity":"common","price":20,"chance":0.075},
            {"name":"🐠 Cá Mú","rarity":"common","price":25,"chance":0.075},
            {"name":"🐡 Cá Trắm","rarity":"common","price":30,"chance":0.075},
            {"name":"🐟 Cá Chạch","rarity":"common","price":20,"chance":0.075},
            {"name":"🐠 Cá Bống","rarity":"common","price":25,"chance":0.075},
            {"name":"🐡 Cá Nheo","rarity":"common","price":30,"chance":0.075},
            {"name":"🐟 Cá Cơm","rarity":"common","price":20,"chance":0.075},

            # Uncommon 26%
            {"name":"🐠 Cá Hồi","rarity":"uncommon","price":50,"chance":0.043},
            {"name":"🐡 Cá Chình","rarity":"uncommon","price":55,"chance":0.043},
            {"name":"🐟 Cá Ngừ","rarity":"uncommon","price":60,"chance":0.043},
            {"name":"🐠 Cá Thu","rarity":"uncommon","price":50,"chance":0.043},
            {"name":"🐡 Cá Sấu","rarity":"uncommon","price":55,"chance":0.043},
            {"name":"🐟 Cá Hồng","rarity":"uncommon","price":60,"chance":0.043},
            {"name":"🐠 Cá Vược","rarity":"uncommon","price":50,"chance":0.043},
            {"name":"🐡 Cá Chim","rarity":"uncommon","price":55,"chance":0.043},
            {"name":"🐟 Cá Lăng","rarity":"uncommon","price":60,"chance":0.043},
            {"name":"🐠 Cá Sặc","rarity":"uncommon","price":50,"chance":0.043},

            # Rare 20%
            {"name":"🐡 Cá Ngừ Đại Dương","rarity":"rare","price":200,"chance":0.05},
            {"name":"🐟 Cá Mú Hoàng","rarity":"rare","price":250,"chance":0.05},
            {"name":"🐠 Cá Bơn","rarity":"rare","price":220,"chance":0.05},
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

            # Exotic 0.1% - chỉ 3 con
            {"name":"🐟 Catfish","rarity":"exotic","price":350000,"chance":0.0003},
            {"name":"🦈 Megalodon","rarity":"exotic","price":500000,"chance":0.0003},
            {"name":"🐉 Dragon","rarity":"exotic","price":750000,"chance":0.0004},
        ]
        # ===== Helper Functions =====
def get_player(user_id):
    data = load_data()
    if str(user_id) not in data["players"]:
        data["players"][str(user_id)] = {
            "coin":1000,
            "level":1,
            "fish_caught":{},
            "inventory":{"rods":{},"baits":{}}
        }
        save_data(data)
    return data["players"][str(user_id)]

def save_player(user_id, player):
    data = load_data()
    data["players"][str(user_id)] = player
    save_data(data)

def get_fish_by_name(name):
    for f in load_data()["fish"]:
        if f["name"].lower() == name.lower():
            return f
    return None

def get_item_by_name(category, name):
    for item in load_data()[category]:
        if item["name"].lower() == name.lower():
            return item
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

# ===== !help =====
@bot.command()
async def help(ctx):
    embed = discord.Embed(title="🎣 Fishing Bot Commands", color=0x1abc9c)
    embed.add_field(name="!cauca", value="Câu cá (1-5 con/lượt)", inline=False)
    embed.add_field(name="!banca <tên cá> <số lượng>", value="Bán cá", inline=False)
    embed.add_field(name="!banca all", value="Bán tất cả cá", inline=False)
    embed.add_field(name="!cuahang", value="Xem cửa hàng", inline=False)
    embed.add_field(name="!mua <tên vật phẩm> <số lượng>", value="Mua vật phẩm", inline=False)
    embed.add_field(name="!khodo", value="Xem kho đồ", inline=False)
    embed.add_field(name="!profile", value="Xem thông tin cá nhân", inline=False)
    embed.add_field(name="!chuyentien <@user> <số tiền>", value="Chuyển tiền (max 1,000,000 Coincat/ngày)", inline=False)
    embed.add_field(name="!admintang <@user> <số tiền>", value="Admin tăng tiền (chỉ admin)", inline=False)
    await ctx.send(embed=embed)

# ===== !cuahang =====
@bot.command()
async def cuahang(ctx):
    data = load_data()
    embed = discord.Embed(title="🏪 Cửa Hàng", color=0x3498db)
    rods = "\n".join([f"{r['name']} - {r['price']} Coincat - Luck: {r.get('luck',1)}" for r in data["rods"]]) or "Không có"
    baits = "\n".join([f"{b['name']} - {b['price']} Coincat - Luck: {b.get('luck',1)}" for b in data["baits"]]) or "Không có"
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
    player["inventory"][category][item["name"]] = player["inventory"][category].get(item["name"],0)+amount
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

# ===== Keep bot online trên Render =====
def run_flask():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_flask).start()

# ===== Initialize game data =====
init_game_data()

# ===== Run bot =====
bot.run("YOUR_BOT_TOKEN_HERE")
                     
