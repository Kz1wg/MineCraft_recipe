#!/usr/bin/env python3
"""Mojang/bedrock-samples から日本語対応のレシピ索引 data/recipes.json を生成する。

日本語名の解決順:
  1. scripts/ja_overrides.json（手動の上書き）
  2. resource_pack/texts/ja_JP.lang
  3. scripts/ja_names.py（旧形式data値の変換・辞書・ルール）
  4. en_US.lang / ID（英語のまま。data/untranslated.txt に記録）
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ja_names as J  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("BEDROCK_SOURCE", ROOT / "source"))
OUT = ROOT / "data" / "recipes.json"
UNTRANSLATED_OUT = ROOT / "data" / "untranslated.txt"
OVERRIDES_PATH = Path(__file__).resolve().parent / "ja_overrides.json"
RECIPES_DIR = SOURCE / "behavior_pack" / "recipes"
TEXT_DIR = SOURCE / "resource_pack" / "texts"


# ------------------------------------------------------------------ 言語ファイル
def read_lang(path):
    result = {}
    if not path.exists():
        return result
    for line in path.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        v = re.split(r"\t+#", v, maxsplit=1)[0].strip()  # 行末コメント（タブ+#）を除去
        if v:
            result[k.strip()] = v
    return result


def read_overrides(path):
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as e:  # noqa: BLE001
        print(f"WARNING: {path.name} を読み込めませんでした: {e}")
        return {}
    out = {}
    for k, v in raw.items():
        if k.startswith("_") or not isinstance(v, str) or not v.strip():
            continue
        out[k.replace("minecraft:", "").strip()] = v.strip()
    return out


ja = read_lang(TEXT_DIR / "ja_JP.lang")
en = read_lang(TEXT_DIR / "en_US.lang")
OVERRIDES = read_overrides(OVERRIDES_PATH)
UNRESOLVED = {}  # flat id -> 画面に出る暫定名


# ------------------------------------------------------------------ 名前解決
def human_id(value):
    value = str(value or "").split(":")[-1].replace("_", " ").replace(".", " ")
    return value[:1].upper() + value[1:]


def parse_ref(value):
    """'minecraft:planks:2' -> ('minecraft', 'planks', 2)"""
    s = str(value).strip()
    ns, path = "minecraft", s
    if ":" in s:
        ns, _, path = s.partition(":")
    data = None
    m = re.match(r"^(.*?):(-?\d+)$", path)
    if m:
        path, data = m.group(1), int(m.group(2))
    return ns, path, data


def lang_keys(ns, flat):
    keys = [f"item.{flat}.name", f"tile.{flat}.name", f"item.{ns}.{flat}.name",
            f"tile.{ns}.{flat}.name", f"item.{flat}", f"tile.{flat}"]
    if flat in J.FLAT_TO_LEGACY:
        fam, sub = J.FLAT_TO_LEGACY[flat]
        keys += [f"tile.{fam}.{sub}.name", f"item.{fam}.{sub}.name"]
    for color in J.COLOR_JA:  # white_bed -> item.bed.white.name など
        if flat.startswith(color + "_"):
            rest = flat[len(color) + 1:]
            sub = "silver" if color == "light_gray" else color
            keys += [f"item.{rest}.{sub}.name", f"tile.{rest}.{sub}.name"]
    for wood in J.WOOD_JA:
        if flat.startswith(wood + "_"):
            rest = flat[len(wood) + 1:]
            keys += [f"tile.{rest}.{wood}.name", f"item.{rest}.{wood}.name"]
    return keys


def resolve(value, data=None, is_result=False):
    """アイテム参照 -> (日本語名, 正規化ID)"""
    if not isinstance(value, str) or not value.strip():
        return "", ""
    ns, path, sdata = parse_ref(value)
    if data is None:
        data = sdata

    pn = J.potion_name(path)
    if pn:
        return pn, path.replace(":", "_")

    flat, any_name = J.flatten_legacy(path, data, is_result)
    if any_name:
        return any_name, flat
    if flat in OVERRIDES:
        return OVERRIDES[flat], flat

    keys = lang_keys(ns, flat)
    for k in keys:
        if k in ja:
            return ja[k], flat
    composed = J.compose(flat)
    if composed:
        return composed, flat

    for k in keys:
        if k in en:
            UNRESOLVED[flat] = en[k]
            return en[k], flat
    UNRESOLVED[flat] = human_id(flat)
    return human_id(flat), flat


def tag_name(tag):
    t = str(tag).lstrip("#").replace("minecraft:", "")
    key = "#" + t
    if key in OVERRIDES or t in OVERRIDES:
        return OVERRIDES.get(key) or OVERRIDES[t], key
    if t in J.TAG_JA:
        return J.TAG_JA[t], key
    for cand in (t, t[:-1] if t.endswith("s") else "", t[:-2] if t.endswith("es") else ""):
        c = J.compose(cand) if cand else None
        if c:
            return c + "（各種）", key
    UNRESOLVED[key] = "タグ：" + human_id(t)
    return "タグ：" + human_id(t), key


def descriptor(obj, is_result=False):
    """材料1件 -> {"name","count","id"}。候補リストは「A／B」にまとめる。"""
    if isinstance(obj, str):
        if obj.startswith("#"):
            n, i = tag_name(obj)
        else:
            n, i = resolve(obj, is_result=is_result)
        return {"name": n, "count": 1, "id": i}
    if isinstance(obj, list):
        ds = [descriptor(x, is_result) for x in obj if x]
        if not ds:
            return {"name": "", "count": 1, "id": ""}
        names = []
        for d in ds:
            if d["name"] not in names:
                names.append(d["name"])
        return {"name": "／".join(names), "count": ds[0]["count"], "id": ds[0]["id"]}
    if not isinstance(obj, dict):
        return {"name": str(obj), "count": 1, "id": ""}
    count = int(obj.get("count", 1) or 1)
    if obj.get("tag"):
        n, i = tag_name(obj["tag"])
        return {"name": n, "count": count, "id": i}
    val = obj.get("item") or obj.get("name") or obj.get("id") or ""
    n, i = resolve(val, obj.get("data"), is_result)
    return {"name": n, "count": count, "id": i}


def normalize_list(value, role=""):
    """入力の形（単体・リスト・入れ子）を問わず descriptor のリストにする。"""
    if value is None or value == "":
        return []
    if isinstance(value, list):
        out = []
        for x in value:
            out.extend(normalize_list(x, role))
        return out
    if isinstance(value, dict):
        if any(k in value for k in ("item", "tag", "name", "id")):
            d = descriptor(value)
            if role:
                d["role"] = role
            return [d]
        out = []
        for v in value.values():
            if isinstance(v, (dict, list, str)):
                out.extend(normalize_list(v, role))
        return out
    d = descriptor(value)
    if role:
        d["role"] = role
    return [d]


def merge_ingredients(items):
    """同じ材料をまとめて個数を合算。"""
    out = []
    for d in items:
        if not d.get("name"):
            continue
        found = next((x for x in out if x["name"] == d["name"] and x.get("role") == d.get("role")), None)
        if found:
            found["count"] += d["count"]
        else:
            out.append(dict(d))
    return out


def output_info(value):
    if isinstance(value, dict):
        item = value.get("item") or value.get("name") or value.get("id") or ""
        name, rid = resolve(item, value.get("data"), True)
        return name, int(value.get("count", 1) or 1), rid
    name, rid = resolve(value, None, True)
    return name, 1, rid


# ------------------------------------------------------------------ カテゴリ・絵文字
TOOL_TOKENS = {"sword", "axe", "pickaxe", "shovel", "hoe", "helmet", "chestplate", "leggings", "boots",
               "bow", "crossbow", "shield", "trident", "shears", "spear", "mace", "brush", "spyglass",
               "bucket", "elytra", "saddle", "lead", "bundle"}
TOOL_IDS = {"fishing_rod", "flint_and_steel", "carrot_on_a_stick", "warped_fungus_on_a_stick",
            "name_tag", "turtle_helmet", "wolf_armor", "compass", "recovery_compass", "clock", "empty_map"}
FOOD_TOKENS = {"bread", "cake", "pie", "stew", "soup", "cookie", "cooked", "apple", "carrot", "potato",
               "beetroot", "melon", "kelp", "beef", "porkchop", "chicken", "mutton", "rabbit", "cod",
               "salmon", "berries", "honey"}
REDSTONE_TOKENS = {"redstone", "piston", "repeater", "comparator", "observer", "dropper", "dispenser",
                   "hopper", "lever", "tripwire", "daylight", "detector", "target", "tnt", "rail",
                   "minecart", "boat", "raft", "crafter", "lightning"}
BUILD_TOKENS = {"planks", "stairs", "slab", "wall", "fence", "gate", "door", "trapdoor", "button",
                "plate", "glass", "pane", "brick", "bricks", "wool", "concrete", "terracotta", "sign",
                "torch", "lantern", "chest", "barrel", "bed", "candle", "carpet", "banner", "shelf",
                "bookshelf", "ladder", "stone", "cobblestone", "sandstone", "quartz", "prismarine",
                "purpur", "deepslate", "blackstone", "tuff", "mud", "log", "wood", "stem", "hyphae",
                "scaffolding", "pillar", "lamp", "frame", "pot", "painting", "campfire"}
MATERIAL_TOKENS = {"ingot", "nugget", "block", "dye", "paper", "stick", "string", "leather", "powder",
                   "crystal", "shard", "map", "book", "arrow", "firework", "dust", "pearl", "eye",
                   "rod", "scrap", "ball", "bottle"}


def tokens_of(name_id):
    return set(re.split(r"[_:]+", name_id.lower()))


def category_for(name_id, station):
    n = name_id.lower()
    t = tokens_of(n)
    if station == "brewing_stand":
        return "醸造"
    if n in TOOL_IDS or (t & TOOL_TOKENS and "block" not in t) or ("armor" in t and "stand" not in t):
        return "道具・装備"
    if t & FOOD_TOKENS and "block" not in t:
        return "食料"
    if "potion" in t:
        return "醸造"
    if t & REDSTONE_TOKENS:
        return "レッドストーン・乗り物"
    if t & BUILD_TOKENS:
        return "建築"
    if t & MATERIAL_TOKENS:
        return "素材"
    return "その他"


EMOJI_RULES = [
    ({"sword", "mace", "spear"}, "⚔️"), ({"bow", "crossbow", "arrow"}, "🏹"), ({"pickaxe"}, "⛏️"),
    ({"axe"}, "🪓"), ({"shovel", "hoe", "shears"}, "🔧"), ({"trident"}, "🔱"),
    ({"helmet", "chestplate", "leggings", "boots", "armor", "shield"}, "🛡️"),
    ({"bread"}, "🍞"), ({"cake"}, "🍰"), ({"cookie"}, "🍪"), ({"pie"}, "🥧"), ({"stew", "soup"}, "🍲"),
    ({"apple"}, "🍎"), ({"carrot"}, "🥕"), ({"potato"}, "🥔"), ({"cod", "salmon", "fish"}, "🐟"),
    ({"beef", "porkchop", "chicken", "mutton", "rabbit", "cooked"}, "🍖"),
    ({"potion"}, "🧪"), ({"boat", "raft"}, "🛶"), ({"door", "trapdoor", "gate"}, "🚪"),
    ({"torch", "lantern", "candle", "lamp"}, "🕯️"), ({"bed"}, "🛏️"), ({"chest", "barrel", "box"}, "📦"),
    ({"rail", "minecart"}, "🚋"), ({"book", "paper", "map"}, "📘"), ({"glass", "pane"}, "🪟"),
    ({"wool", "carpet", "banner"}, "🧶"), ({"dye"}, "🎨"), ({"redstone", "repeater", "comparator", "piston"}, "🔴"),
    ({"tnt"}, "💥"), ({"furnace", "campfire", "smoker"}, "🔥"), ({"ingot", "nugget"}, "🔩"),
    ({"diamond", "emerald", "quartz", "amethyst"}, "💎"),
]


def emoji_for(name_id):
    t = tokens_of(name_id)
    for keys, emo in EMOJI_RULES:
        if t & keys:
            return emo
    return "🧱"


# ------------------------------------------------------------------ レシピ解析
STATIONS = {"crafting_table", "stonecutter", "furnace", "blast_furnace", "smoker", "campfire",
            "soul_campfire", "smithing_table", "brewing_stand", "cartography_table"}


def parse_file(path):
    try:
        raw = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:  # noqa: BLE001
        return None
    if not isinstance(raw, dict):
        return None
    typkey = next((k for k in raw if k.startswith("minecraft:recipe_")), None)
    if not typkey:
        return None
    body = raw[typkey]
    if not isinstance(body, dict):
        return None
    ident = (body.get("description") or {}).get("identifier") or path.stem
    name_id = ident.split(":")[-1]
    tags = body.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]
    tags = [str(x) for x in tags]
    stations = [x for x in tags if x in STATIONS]
    if not stations:
        if "furnace" in typkey:
            stations = ["furnace"]
        elif "brewing" in typkey:
            stations = ["brewing_stand"]
        elif "smithing" in typkey:
            stations = ["smithing_table"]
        elif "stonecut" in typkey:
            stations = ["stonecutter"]
        else:
            stations = ["crafting_table"]

    ingredients, grid = [], []
    out_name, out_count, out_id = "", 1, ""
    typ, typ_label = "other", "特殊"

    if typkey.endswith("recipe_shaped"):
        typ, typ_label = "shaped", "配置あり"
        pattern = body.get("pattern", [])
        key = body.get("key", {})
        raw_items = []
        for row in pattern[:3]:
            cells = []
            for ch in row[:3]:
                if ch == " ":
                    cells.append("")
                else:
                    d = descriptor(key.get(ch, {}))
                    cells.append(d["name"])
                    raw_items.append(d)
            grid.extend(cells + [""] * (3 - len(cells)))
        grid = (grid + [""] * 9)[:9]
        ingredients = merge_ingredients(raw_items)
        out_name, out_count, out_id = output_info(body.get("result"))
    elif typkey.endswith("recipe_shapeless"):
        typ, typ_label = "shapeless", "配置自由"
        ingredients = merge_ingredients(normalize_list(body.get("ingredients")))
        out_name, out_count, out_id = output_info(body.get("result"))
    elif any(k in typkey for k in ("recipe_furnace", "recipe_blast_furnace", "recipe_smoker", "recipe_campfire")):
        typ, typ_label = "process", "精錬・加熱"
        ingredients = merge_ingredients(normalize_list(body.get("input"), "入力"))
        out_name, out_count, out_id = output_info(body.get("output", body.get("output ")))
    elif "recipe_brewing" in typkey:
        typ, typ_label = "brewing", "醸造"
        ingredients = merge_ingredients(normalize_list(body.get("input"), "ベース")
                                        + normalize_list(body.get("reagent"), "材料"))
        out_name, out_count, out_id = output_info(body.get("output", body.get("output ")))
    elif "recipe_smithing" in typkey:
        typ, typ_label = "smithing", "鍛冶"
        ingredients = merge_ingredients(normalize_list(body.get("template"), "テンプレート")
                                        + normalize_list(body.get("base"), "ベース")
                                        + normalize_list(body.get("addition"), "素材"))
        out_name, out_count, out_id = output_info(body.get("result"))
        if "recipe_smithing_trim" in typkey:
            base_name = descriptor(body.get("base"))["name"] if body.get("base") else ""
            out_name = (base_name + "の装飾") if base_name else "防具の装飾（トリム）"
    else:
        return None

    if not out_name:
        out_name, out_id = resolve(name_id, None, True)
    if not out_name or not ingredients:
        return None
    station = stations[0]
    cat_id = out_id or name_id
    return {
        "id": str(ident),
        "name": out_name,
        "output": out_name,
        "outputId": out_id,
        "outputCount": out_count,
        "ingredients": ingredients,
        "grid": grid,
        "stations": stations,
        "type": typ,
        "typeLabel": typ_label,
        "category": category_for(cat_id, station),
        "emoji": emoji_for(cat_id),
        "special": "",
        "stationText": " / ".join(stations),
    }


def find_version():
    for p in [SOURCE / "version.json", SOURCE / "version.txt", SOURCE / "manifest.json"]:
        if p.exists():
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
                for k in ("version", "minecraft_version", "name"):
                    if k in d:
                        return str(d[k])
            except Exception:  # noqa: BLE001
                pass
    return "公式サンプルデータ main"


def main():
    if not RECIPES_DIR.exists():
        raise SystemExit(f"Recipe directory not found: {RECIPES_DIR}")
    if not ja:
        print("WARNING: ja_JP.lang が見つかりません。辞書・ルールだけで日本語化します。")
    records, skipped = [], []
    for p in sorted(RECIPES_DIR.rglob("*.json")):
        try:
            r = parse_file(p)
        except Exception as e:  # noqa: BLE001  1ファイルの失敗で全体を止めない
            skipped.append(f"{p.name}: {type(e).__name__}: {e}")
            continue
        if r:
            records.append(r)
    unique = {r["id"]: r for r in records}
    records = sorted(unique.values(), key=lambda r: (r["name"], r["id"]))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {"source": "Mojang/bedrock-samples", "gameVersion": find_version(),
               "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%d UTC"),
               "recipeCount": len(records), "recipes": records}
    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    lines = [f"{k}\t{v}" for k, v in sorted(UNRESOLVED.items())]
    header = ("# 日本語名を解決できずに英語表示になっているID（ID<TAB>画面に出る名前）\n"
              "# scripts/ja_overrides.json に  \"ID\": \"日本語名\"  を足すと次回ビルドから日本語になります。\n")
    UNTRANSLATED_OUT.write_text(header + "\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    print(f"Wrote {len(records)} recipes to {OUT}")
    print(f"Japanese name lookups: ja_JP.lang={len(ja)} keys, overrides={len(OVERRIDES)}")
    print(f"Untranslated ids: {len(UNRESOLVED)} (see {UNTRANSLATED_OUT.name})")
    for line in lines[:40]:
        print("  -", line.replace("\t", " -> "))
    if skipped:
        print(f"Skipped {len(skipped)} files due to errors:")
        for s in skipped[:20]:
            print("  -", s)


if __name__ == "__main__":
    main()
