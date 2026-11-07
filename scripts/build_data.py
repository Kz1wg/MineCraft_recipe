#!/usr/bin/env python3
"""Build a Japanese-friendly static recipe index from Mojang/bedrock-samples."""
import json, re, os
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("BEDROCK_SOURCE", ROOT / "source"))
OUT = ROOT / "data" / "recipes.json"
RECIPES_DIR = SOURCE / "behavior_pack" / "recipes"
TEXT_DIR = SOURCE / "resource_pack" / "texts"

def read_lang(path):
    result = {}
    if not path.exists():
        return result
    for line in path.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
        line=line.strip()
        if not line or line.startswith("#") or "=" not in line: continue
        k,v=line.split("=",1)
        result[k.strip()]=v.strip()
    return result

ja = read_lang(TEXT_DIR / "ja_JP.lang")
en = read_lang(TEXT_DIR / "en_US.lang")

def human_id(value):
    if not isinstance(value,str): return str(value or "")
    value=value.split(":")[-1].replace("_"," ").replace("."," ")
    return value[:1].upper()+value[1:]

def item_name(value):
    if isinstance(value,dict):
        value=value.get("item") or value.get("tag") or value.get("name") or value.get("id") or ""
    if not isinstance(value,str): return str(value or "")
    if value.startswith("#"): return "タグ：" + human_id(value[1:])
    ns,_,path=value.partition(":")
    if not _:
        ns,path="minecraft",ns
    candidates=[]
    for key in (f"item.{path}.name", f"tile.{path}.name", f"item.{ns}.{path}.name",
                f"tile.{ns}.{path}.name", f"item.{path}", f"tile.{path}"):
        candidates.append(key)
    for d in (ja,en):
        for key in candidates:
            if key in d: return d[key]
    return human_id(path)

TAG_NAMES = {
    "minecraft:planks": "板材（各種）",
    "minecraft:stone_crafting_materials": "丸石などの石材",
    "minecraft:wooden_slabs": "木材のハーフブロック",
    "minecraft:stone_slabs": "石材のハーフブロック",
    "minecraft:logs": "原木（各種）",
    "minecraft:wool": "羊毛（各色）",
    "minecraft:sand": "砂",
    "minecraft:glass": "ガラス",
    "minecraft:leaves": "葉（各種）",
    "minecraft:coals": "石炭または木炭",
}

def descriptor(obj):
    if isinstance(obj,str): return {"name":item_name(obj),"count":1}
    if isinstance(obj,list):
        return [descriptor(x) for x in obj]
    if not isinstance(obj,dict): return {"name":str(obj),"count":1}
    val=obj.get("item") or obj.get("tag") or obj.get("name") or obj.get("id") or ""
    if obj.get("tag"):
        tag=str(obj["tag"])
        return {"name":TAG_NAMES.get(tag, "タグ：" + human_id(tag)),"count":int(obj.get("count",1) or 1)}
    return {"name":item_name(val),"count":int(obj.get("count",1) or 1)}

def normalize_list(value):
    if value is None: return []
    if isinstance(value,list):
        out=[]
        for x in value: out.extend(normalize_list(x))
        return out
    if isinstance(value,dict):
        # Bedrock item descriptor can be a single object or a mapping with nested items.
        if "item" in value or "tag" in value or "name" in value or "id" in value:
            return [descriptor(value)]
        out=[]
        for k,v in value.items():
            if isinstance(v,(dict,list)):
                out.extend(normalize_list(v))
            elif isinstance(v,str):
                out.append(descriptor(v))
        return out
    return [descriptor(value)]

def output_info(value):
    if isinstance(value,dict):
        item=value.get("item") or value.get("name") or value.get("id") or ""
        return item_name(item), int(value.get("count",1) or 1)
    return item_name(value),1

def category_for(name, station, typ):
    n=name.lower()
    if station=="brewing_stand": return "醸造"
    if any(x in n for x in ["sword","axe","pickaxe","shovel","hoe","helmet","chestplate","leggings","boots","bow","crossbow","shield","trident","fishing_rod","armor","armour","mace"]): return "道具・装備"
    if any(x in n for x in ["bread","cake","pie","stew","soup","cookie","cooked","potion","apple","fish","meat","carrot","potato","beetroot","rabbit","melon_slice"]): return "食料"
    if any(x in n for x in ["planks","stairs","slab","wall","fence","door","trapdoor","button","pressure_plate","glass","brick","wool","concrete","terracotta","sign","boat","raft","torch","lantern","chest","barrel","bed","candle","carpet","banner","shelf"]): return "建築"
    if any(x in n for x in ["ingot","nugget","block","dye","paper","stick","string","leather","brick","powder","crystal","shard","compass","clock","map","book","arrow","firework"]): return "素材"
    return "その他"

def emoji_for(name):
    n=name.lower()
    for keys,emo in [
        (["sword","axe","pickaxe","shovel","hoe","bow","crossbow","trident"],"⚔️"),
        (["helmet","chestplate","leggings","boots","armor"],"🛡️"),
        (["bread","cake","cookie","stew","soup","apple","fish","meat","carrot","potato"],"🍎"),
        (["potion"],"🧪"),(["boat","raft"],"🛶"),(["door","trapdoor"],"🚪"),
        (["torch","lantern","candle"],"🕯️"),(["bed"],"🛏️"),(["chest","barrel"],"📦"),
        (["rail","minecart"],"🚋"),(["book","paper"],"📘"),(["glass"],"🪟"),
    ]:
        if any(k in n for k in keys): return emo
    return "🧱"

def parse_file(path):
    try: raw=json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception: return None
    if not isinstance(raw,dict): return None
    typkey=next((k for k in raw if k.startswith("minecraft:recipe_")),None)
    if not typkey: return None
    body=raw[typkey]
    if not isinstance(body,dict): return None
    ident=(body.get("description") or {}).get("identifier") or path.stem
    name_id=ident.split(":")[-1]
    tags=body.get("tags",[])
    if isinstance(tags,str): tags=[tags]
    tags=[str(x) for x in tags]
    stations=[x for x in tags if x in {"crafting_table","stonecutter","furnace","blast_furnace","smoker","campfire","soul_campfire","smithing_table","brewing_stand","cartography_table"}]
    if not stations:
        # Certain recipe data files omit tags or use a specialized type.
        if "furnace" in typkey: stations=["furnace"]
        elif "brewing" in typkey: stations=["brewing_stand"]
        elif "smithing" in typkey: stations=["smithing_table"]
        elif "stonecut" in typkey: stations=["stonecutter"]
        else: stations=["crafting_table"]
    ingredients=[]; grid=[]; special=""; out_name=""; out_count=1
    typ="other"; typ_label="特殊"
    if typkey.endswith("recipe_shaped"):
        typ="shaped";typ_label="配置あり"
        pattern=body.get("pattern",[])
        key=body.get("key",{})
        for row in pattern[:3]:
            row_cells=[]
            for ch in row[:3]:
                if ch==" ":
                    row_cells.append("")
                else:
                    d=descriptor(key.get(ch,{}))
                    row_cells.append(d["name"])
                    found=next((x for x in ingredients if x["name"]==d["name"]),None)
                    if found: found["count"]+=d["count"]
                    else: ingredients.append(dict(d))
            grid.extend(row_cells + [""] * (3-len(row_cells)))
        while len(grid)<9: grid.append("")
        if len(grid)>9: grid=grid[:9]
        out_name,out_count=output_info(body.get("result"))
    elif typkey.endswith("recipe_shapeless"):
        typ="shapeless";typ_label="配置自由"
        ingredients=normalize_list(body.get("ingredients"))
        out_name,out_count=output_info(body.get("result"))
    elif "recipe_furnace" in typkey or "recipe_blast_furnace" in typkey or "recipe_smoker" in typkey or "recipe_campfire" in typkey:
        typ="process";typ_label="精錬・加熱"
        ingredients=normalize_list(body.get("input"))
        out_name,out_count=output_info(body.get("output", body.get("output ")))
    elif "recipe_brewing" in typkey:
        typ="brewing";typ_label="醸造"
        ingredients=normalize_list([body.get("input"),body.get("reagent")])
        out_name,out_count=output_info(body.get("output", body.get("output ")))
    elif "recipe_smithing" in typkey:
        typ="smithing";typ_label="鍛冶"
        ingredients=normalize_list([body.get("template"),body.get("base"),body.get("addition")])
        out_name,out_count=output_info(body.get("result"))
        if "recipe_smithing_trim" in typkey:
            out_name=(item_name(body.get("base")) + "の装飾") if body.get("base") else "防具の装飾（トリム）"
    else:
        return None
    if not out_name: out_name=item_name(name_id)
    # Drop invalid entries without any meaningful output.
    if not out_name: return None
    if not ingredients and typ not in ("other",): return None
    station=stations[0] if stations else ""
    return {
        "id":str(ident),
        "name":out_name,
        "output":out_name,
        "outputCount":out_count,
        "ingredients":ingredients,
        "grid":grid,
        "stations":stations,
        "type":typ,
        "typeLabel":typ_label,
        "category":category_for(name_id,station,typ),
        "emoji":emoji_for(name_id),
        "special":special,
        "stationText":" / ".join(stations)
    }

def find_version():
    for p in [SOURCE/"version.json", SOURCE/"version.txt", SOURCE/"manifest.json"]:
        if p.exists():
            try:
                d=json.loads(p.read_text(encoding="utf-8"))
                for k in ("version","minecraft_version","name"):
                    if k in d: return str(d[k])
            except Exception: pass
    return "公式サンプルデータ main"

def main():
    if not RECIPES_DIR.exists():
        raise SystemExit(f"Recipe directory not found: {RECIPES_DIR}")
    records=[]
    for p in sorted(RECIPES_DIR.rglob("*.json")):
        r=parse_file(p)
        if r: records.append(r)
    # Keep distinct recipes, but avoid exact duplicate IDs.
    unique={r["id"]:r for r in records}
    records=list(unique.values())
    records.sort(key=lambda r:(r["name"],r["id"]))
    OUT.parent.mkdir(parents=True,exist_ok=True)
    payload={"source":"Mojang/bedrock-samples","gameVersion":find_version(),
             "generatedAt":datetime.now(timezone.utc).strftime("%Y-%m-%d UTC"),
             "recipeCount":len(records),"recipes":records}
    OUT.write_text(json.dumps(payload,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    print(f"Wrote {len(records)} recipes to {OUT}")
if __name__=="__main__": main()
