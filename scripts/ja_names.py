"""日本語名の補完ルール。

ja_JP.lang に該当キーが無いアイテム（旧形式の data 値つきID、ポーション、タグなど）を
日本語にするためのフォールバック辞書とルールをまとめたモジュールです。

優先順位（build_data.py 側）:
  1. scripts/ja_overrides.json（手動の上書き）
  2. ja_JP.lang
  3. このモジュールの辞書・ルール
  4. en_US.lang / ID（英語のまま。data/untranslated.txt に記録される）
"""
import re

# ---------------------------------------------------------------- 色・木材
# 羊毛などの data 値の順番
COLORS16 = ["white", "orange", "magenta", "light_blue", "yellow", "lime", "pink", "gray",
            "light_gray", "cyan", "purple", "blue", "brown", "green", "red", "black"]
# 染料・旗の data 値の順番（羊毛とは逆順）
DYE16 = ["black", "red", "green", "brown", "blue", "purple", "cyan", "light_gray",
         "gray", "pink", "lime", "yellow", "light_blue", "magenta", "orange", "white"]
WOOD6 = ["oak", "spruce", "birch", "jungle", "acacia", "dark_oak"]

COLOR_JA = {
    "white": "白色", "orange": "橙色", "magenta": "赤紫色", "light_blue": "空色",
    "yellow": "黄色", "lime": "黄緑色", "pink": "桃色", "gray": "灰色",
    "light_gray": "薄灰色", "silver": "薄灰色", "cyan": "青緑色", "purple": "紫色",
    "blue": "青色", "brown": "茶色", "green": "緑色", "red": "赤色", "black": "黒色",
}
COLOR_ITEMS = {
    "wool": "羊毛", "carpet": "カーペット", "bed": "ベッド", "banner": "旗",
    "candle": "ろうそく", "concrete": "コンクリート", "concrete_powder": "コンクリートパウダー",
    "terracotta": "テラコッタ", "glazed_terracotta": "彩釉テラコッタ",
    "stained_glass": "色付きガラス", "stained_glass_pane": "色付きガラス板",
    "shulker_box": "シュルカーボックス", "dye": "染料", "harness": "ハーネス", "bundle": "バンドル",
}

WOOD_JA = {
    "oak": "オーク", "spruce": "トウヒ", "birch": "シラカバ", "jungle": "ジャングル",
    "acacia": "アカシア", "dark_oak": "ダークオーク", "mangrove": "マングローブ",
    "cherry": "サクラ", "pale_oak": "ペールオーク", "bamboo": "竹", "crimson": "真紅",
    "warped": "歪んだ",
}
WOOD_ITEMS = {
    "planks": "板材", "stairs": "階段", "slab": "ハーフブロック", "fence": "フェンス",
    "fence_gate": "フェンスゲート", "door": "ドア", "trapdoor": "トラップドア",
    "button": "ボタン", "pressure_plate": "感圧板", "sign": "看板",
    "hanging_sign": "吊り下げ式看板", "boat": "ボート", "chest_boat": "チェスト付きボート",
    "raft": "いかだ", "chest_raft": "チェスト付きいかだ", "log": "原木", "wood": "木",
    "leaves": "葉", "sapling": "苗木", "stem": "幹", "hyphae": "菌糸",
}

# ---------------------------------------------------------------- data値つき旧形式ID
# family: (data順のサブ名リスト, data順の新形式IDリスト)
def _tmpl(subs, fmt):
    return (list(subs), [fmt.format(s) for s in subs])

LEGACY = {
    "planks": _tmpl(WOOD6, "{}_planks"),
    "log": _tmpl(WOOD6[:4], "{}_log"),
    "log2": _tmpl(WOOD6[4:], "{}_log"),
    "leaves": _tmpl(WOOD6[:4], "{}_leaves"),
    "leaves2": _tmpl(WOOD6[4:], "{}_leaves"),
    "sapling": _tmpl(WOOD6, "{}_sapling"),
    "wooden_slab": _tmpl(WOOD6, "{}_slab"),
    "wool": _tmpl(COLORS16, "{}_wool"),
    "carpet": _tmpl(COLORS16, "{}_carpet"),
    "stained_glass": _tmpl(COLORS16, "{}_stained_glass"),
    "stained_glass_pane": _tmpl(COLORS16, "{}_stained_glass_pane"),
    "stained_hardened_clay": _tmpl(COLORS16, "{}_terracotta"),
    "concrete": _tmpl(COLORS16, "{}_concrete"),
    "concrete_powder": _tmpl(COLORS16, "{}_concrete_powder"),
    "banner": _tmpl(DYE16, "{}_banner"),
    "dye": (list(DYE16), ["ink_sac", "red_dye", "green_dye", "cocoa_beans", "lapis_lazuli",
                          "purple_dye", "cyan_dye", "light_gray_dye", "gray_dye", "pink_dye",
                          "lime_dye", "yellow_dye", "light_blue_dye", "magenta_dye",
                          "orange_dye", "bone_meal"]),
    "stone": (["stone", "granite", "granite_smooth", "diorite", "diorite_smooth", "andesite", "andesite_smooth"],
              ["stone", "granite", "polished_granite", "diorite", "polished_diorite", "andesite", "polished_andesite"]),
    "stonebrick": (["default", "mossy", "cracked", "chiseled"],
                   ["stone_bricks", "mossy_stone_bricks", "cracked_stone_bricks", "chiseled_stone_bricks"]),
    "sandstone": (["default", "heiroglyphs", "cut", "smooth"],
                  ["sandstone", "chiseled_sandstone", "cut_sandstone", "smooth_sandstone"]),
    "red_sandstone": (["default", "heiroglyphs", "cut", "smooth"],
                      ["red_sandstone", "chiseled_red_sandstone", "cut_red_sandstone", "smooth_red_sandstone"]),
    "quartz_block": (["default", "chiseled", "lines", "smooth"],
                     ["quartz_block", "chiseled_quartz_block", "quartz_pillar", "smooth_quartz"]),
    "sand": (["default", "red"], ["sand", "red_sand"]),
    "coal": (["coal", "charcoal"], ["coal", "charcoal"]),
    "golden_apple": (["golden_apple", "enchanted_golden_apple"], ["golden_apple", "enchanted_golden_apple"]),
}
# data を指定しない「何でもOK」な材料のときの表示名
FAMILY_ANY = {
    "planks": "板材（各種）", "log": "原木（各種）", "log2": "原木（各種）",
    "leaves": "葉（各種）", "leaves2": "葉（各種）", "sapling": "苗木（各種）",
    "wooden_slab": "木材のハーフブロック（各種）", "wool": "羊毛（各色）",
    "carpet": "カーペット（各色）", "stained_glass": "色付きガラス（各色）",
    "stained_glass_pane": "色付きガラス板（各色）", "stained_hardened_clay": "色付きテラコッタ（各色）",
    "concrete": "コンクリート（各色）", "concrete_powder": "コンクリートパウダー（各色）",
    "banner": "旗（各色）", "dye": "染料（各色）", "coal": "石炭または木炭",
}
# 旧形式IDの「ベース名のまま」（data=0扱い）を許可するもの
LEGACY_PLAIN = {"stone", "stonebrick", "sandstone", "red_sandstone", "quartz_block", "sand", "coal", "golden_apple"}

# 新形式ID -> (family, サブ名)  ja_JP.lang の旧キー検索用
FLAT_TO_LEGACY = {}
for _fam, (_subs, _flats) in LEGACY.items():
    for _s, _f in zip(_subs, _flats):
        FLAT_TO_LEGACY.setdefault(_f, (_fam, "silver" if _s == "light_gray" else _s))


def flatten_legacy(path, data, is_result):
    """旧形式 (path, data) を新形式IDへ。戻り値: (flat_id, any_name)。
    any_name が入っていれば「何でもOK」な材料。"""
    if path not in LEGACY:
        return path, None
    subs, flats = LEGACY[path]
    if data is None:
        if is_result or path in LEGACY_PLAIN:
            data = 0
        else:
            return path, FAMILY_ANY.get(path)
    if data in (-1, 32767):
        return path, FAMILY_ANY.get(path)
    if 0 <= data < len(flats):
        return flats[data], None
    return path, None


# ---------------------------------------------------------------- 単語辞書
DIRECT = {
    # 基本素材
    "stick": "棒", "coal": "石炭", "charcoal": "木炭", "iron_ingot": "鉄インゴット",
    "gold_ingot": "金インゴット", "copper_ingot": "銅インゴット", "netherite_ingot": "ネザライトインゴット",
    "netherite_scrap": "ネザライトの欠片", "diamond": "ダイヤモンド", "emerald": "エメラルド",
    "lapis_lazuli": "ラピスラズリ", "redstone": "レッドストーン", "quartz": "ネザークォーツ",
    "amethyst_shard": "アメジストの欠片", "iron_nugget": "鉄の塊", "gold_nugget": "金の塊",
    "copper_nugget": "銅の塊", "raw_iron": "鉄の原石", "raw_gold": "金の原石", "raw_copper": "銅の原石",
    "clay_ball": "粘土玉", "brick": "レンガ", "nether_brick": "ネザーレンガ", "paper": "紙",
    "book": "本", "writable_book": "本と羽根ペン", "leather": "革", "rabbit_hide": "ウサギの皮",
    "string": "糸", "feather": "羽根", "flint": "火打石", "gunpowder": "火薬",
    "slime_ball": "スライムボール", "honey_bottle": "ハチミツ入りの瓶", "honeycomb": "ハニカム",
    "sugar": "砂糖", "sugar_cane": "サトウキビ", "reeds": "サトウキビ", "egg": "卵", "wheat": "小麦",
    "wheat_seeds": "小麦の種", "bone": "骨", "bone_meal": "骨粉", "blaze_powder": "ブレイズパウダー",
    "blaze_rod": "ブレイズロッド", "ender_pearl": "エンダーパール", "ender_eye": "エンダーアイ",
    "eye_of_ender": "エンダーアイ", "magma_cream": "マグマクリーム", "ghast_tear": "ガストの涙",
    "fermented_spider_eye": "発酵したクモの目", "spider_eye": "クモの目",
    "glowstone_dust": "グロウストーンダスト", "glass_bottle": "ガラス瓶", "bowl": "ボウル",
    "bucket": "バケツ", "water_bucket": "水入りバケツ", "lava_bucket": "溶岩入りバケツ",
    "milk_bucket": "ミルク入りバケツ", "ink_sac": "イカスミ", "glow_ink_sac": "輝くイカスミ",
    "cocoa_beans": "カカオ豆", "prismarine_shard": "プリズマリンの欠片",
    "prismarine_crystals": "プリズマリンクリスタル", "heart_of_the_sea": "海のハート",
    "nautilus_shell": "オウムガイの殻", "phantom_membrane": "ファントムの皮膜",
    "turtle_scute": "カメのウロコ", "scute": "カメのウロコ", "armadillo_scute": "アルマジロのウロコ",
    "echo_shard": "エコーの欠片", "breeze_rod": "ブリーズロッド", "resin_clump": "樹脂塊",
    "resin_brick": "樹脂レンガ", "experience_bottle": "エンチャントの瓶", "emerald_block": "エメラルドブロック",
    # 道具・その他アイテム
    "flint_and_steel": "火打石と打ち金", "shears": "ハサミ", "compass": "コンパス",
    "recovery_compass": "回収コンパス", "clock": "時計", "empty_map": "空の地図", "map": "地図",
    "filled_map": "地図", "fishing_rod": "釣り竿", "carrot_on_a_stick": "ニンジン付きの棒",
    "warped_fungus_on_a_stick": "歪んだキノコ付きの棒", "bow": "弓", "crossbow": "クロスボウ",
    "arrow": "矢", "spectral_arrow": "光の矢", "tipped_arrow": "効果付きの矢", "trident": "トライデント",
    "shield": "盾", "lead": "リード", "name_tag": "名札", "spyglass": "望遠鏡", "brush": "ブラシ",
    "mace": "メイス", "firework_rocket": "ロケット花火", "firework_star": "花火の星",
    "elytra": "エリトラ", "saddle": "鞍", "bundle": "バンドル", "armor_stand": "防具立て",
    "item_frame": "額縁", "glow_frame": "輝く額縁", "glow_item_frame": "輝く額縁", "painting": "絵画",
    "flower_pot": "植木鉢", "decorated_pot": "飾り壺", "wolf_armor": "オオカミの鎧",
    "turtle_helmet": "カメの甲羅", "netherite_upgrade_smithing_template": "ネザライトのアップグレード鍛冶型",
    # 作業場所・機能ブロック
    "crafting_table": "作業台", "furnace": "かまど", "blast_furnace": "溶鉱炉", "smoker": "燻製器",
    "campfire": "焚き火", "soul_campfire": "魂の焚き火", "stonecutter": "石切台", "stonecutter_block": "石切台",
    "smithing_table": "鍛冶台", "fletching_table": "矢細工台", "cartography_table": "製図台",
    "loom": "機織り機", "grindstone": "砥石", "brewing_stand": "醸造台", "cauldron": "大釜",
    "enchanting_table": "エンチャントテーブル", "anvil": "金床", "beacon": "ビーコン", "conduit": "コンジット",
    "composter": "コンポスター", "barrel": "樽", "chest": "チェスト", "trapped_chest": "トラップチェスト",
    "ender_chest": "エンダーチェスト", "shulker_box": "シュルカーボックス", "undyed_shulker_box": "シュルカーボックス",
    "lectern": "書見台", "bookshelf": "本棚", "chiseled_bookshelf": "彫り込み入りの本棚",
    "jukebox": "ジュークボックス", "note_block": "音符ブロック", "bed": "ベッド", "lodestone": "ロードストーン",
    "crafter": "作製機", "respawn_anchor": "リスポーンアンカー", "bell": "鐘",
    # 光源・装飾
    "torch": "松明", "soul_torch": "魂の松明", "lantern": "ランタン", "soul_lantern": "魂のランタン",
    "sea_lantern": "シーランタン", "end_rod": "エンドロッド", "glowstone": "グロウストーン",
    "redstone_lamp": "レッドストーンランプ", "lit_redstone_lamp": "レッドストーンランプ",
    "jack_o_lantern": "ジャック・オ・ランタン", "lit_pumpkin": "ジャック・オ・ランタン",
    "carved_pumpkin": "くり抜かれたカボチャ", "pumpkin": "カボチャ", "melon_block": "スイカ", "melon": "スイカ",
    "chain": "鎖", "iron_chain": "鉄の鎖", "iron_bars": "鉄格子", "ladder": "はしご", "scaffolding": "足場",
    "glass": "ガラス", "glass_pane": "板ガラス", "tinted_glass": "遮光ガラス",
    "snow": "雪", "snow_block": "雪ブロック", "ice": "氷", "packed_ice": "氷塊", "blue_ice": "青氷",
    "clay": "粘土", "hay_block": "干し草の俵", "bone_block": "骨ブロック", "slime": "スライムブロック",
    "honey_block": "ハチミツブロック", "honeycomb_block": "ハニカムブロック",
    "dried_kelp_block": "乾燥した昆布ブロック", "sponge": "スポンジ", "wet_sponge": "濡れたスポンジ",
    "moss_block": "苔ブロック", "mud": "泥", "packed_mud": "固められた泥", "dirt": "土", "grass_block": "草ブロック",
    "coarse_dirt": "粗い土", "podzol": "ポドゾル", "sand": "砂", "red_sand": "赤い砂", "gravel": "砂利",
    "netherrack": "ネザーラック", "soul_sand": "ソウルサンド", "soul_soil": "ソウルソイル",
    "end_stone": "エンドストーン", "obsidian": "黒曜石", "cactus": "サボテン", "kelp": "昆布",
    "magma": "マグマブロック", "magma_block": "マグマブロック", "nether_wart_block": "ネザーウォートブロック",
    "warped_wart_block": "歪んだウォートブロック", "bamboo": "竹", "bamboo_block": "竹ブロック",
    "bamboo_mosaic": "竹のモザイク", "stripped_bamboo_block": "表皮を剥いだ竹ブロック",
    # 金属・鉱石ブロック
    "iron_block": "鉄ブロック", "gold_block": "金ブロック", "diamond_block": "ダイヤモンドブロック",
    "lapis_block": "ラピスラズリブロック", "redstone_block": "レッドストーンブロック", "coal_block": "石炭ブロック",
    "netherite_block": "ネザライトブロック", "copper_block": "銅ブロック", "raw_iron_block": "鉄の原石ブロック",
    "raw_gold_block": "金の原石ブロック", "raw_copper_block": "銅の原石ブロック", "amethyst_block": "アメジストブロック",
    "iron_ore": "鉄鉱石", "gold_ore": "金鉱石", "copper_ore": "銅鉱石", "coal_ore": "石炭鉱石",
    "diamond_ore": "ダイヤモンド鉱石", "emerald_ore": "エメラルド鉱石", "lapis_ore": "ラピスラズリ鉱石",
    "redstone_ore": "レッドストーン鉱石", "nether_gold_ore": "ネザーゴールド鉱石",
    "quartz_ore": "ネザークォーツ鉱石", "ancient_debris": "古代の残骸",
    # 石材
    "stone": "石", "cobblestone": "丸石", "stone_bricks": "石レンガ", "mossy_cobblestone": "苔むした丸石",
    "granite": "花崗岩", "diorite": "閃緑岩", "andesite": "安山岩", "sandstone": "砂岩",
    "red_sandstone": "赤い砂岩", "bricks": "レンガ", "brick_block": "レンガ", "nether_bricks": "ネザーレンガ",
    "red_nether_brick": "赤いネザーレンガ", "red_nether_bricks": "赤いネザーレンガ",
    "quartz_block": "ネザークォーツブロック", "quartz_bricks": "クォーツレンガ", "quartz_pillar": "柱状クォーツブロック",
    "prismarine": "プリズマリン", "prismarine_bricks": "プリズマリンレンガ", "dark_prismarine": "ダークプリズマリン",
    "purpur_block": "プルプァブロック", "purpur_pillar": "柱状プルプァブロック", "end_stone_bricks": "エンドストーンレンガ",
    "end_bricks": "エンドストーンレンガ", "deepslate": "深層岩", "cobbled_deepslate": "深層岩の丸石",
    "deepslate_bricks": "深層岩レンガ", "deepslate_tiles": "深層岩タイル", "blackstone": "ブラックストーン",
    "blackstone_bricks": "ブラックストーンレンガ", "tuff": "凝灰岩", "tuff_bricks": "凝灰岩レンガ",
    "mud_bricks": "泥レンガ", "resin_bricks": "樹脂レンガ", "copper": "銅ブロック", "cut_copper": "切り込み入りの銅ブロック",
    "stone_brick": "石レンガ", "end_stone_brick": "エンドストーンレンガ", "prismarine_brick": "プリズマリンレンガ",
    "deepslate_brick": "深層岩レンガ", "deepslate_tile": "深層岩タイル", "mud_brick": "泥レンガ",
    "tuff_brick": "凝灰岩レンガ", "polished_blackstone_brick": "磨かれたブラックストーンレンガ",
    "resin_brick_block": "樹脂レンガ", "purpur": "プルプァ", "smooth_quartz": "滑らかなネザークォーツブロック",
    "powered_rail": "パワードレール", "stonebrick": "石レンガ", "end_stone_bricks": "エンドストーンレンガ",
    "terracotta": "テラコッタ", "hardened_clay": "テラコッタ", "stone_bricks_cracked": "ひびの入った石レンガ",
    "polished_blackstone_bricks": "磨かれたブラックストーンレンガ", "smooth_stone": "滑らかな石",
    # レッドストーン
    "piston": "ピストン", "sticky_piston": "粘着ピストン", "observer": "オブザーバー", "dispenser": "ディスペンサー",
    "dropper": "ドロッパー", "hopper": "ホッパー", "repeater": "レッドストーンリピーター",
    "unpowered_repeater": "レッドストーンリピーター", "comparator": "レッドストーンコンパレーター",
    "unpowered_comparator": "レッドストーンコンパレーター", "lever": "レバー", "tripwire_hook": "トリップワイヤーフック",
    "daylight_detector": "日照センサー", "target": "ターゲット", "tnt": "TNT", "rail": "レール",
    "golden_rail": "パワードレール", "detector_rail": "ディテクターレール", "activator_rail": "アクティベーターレール",
    "minecart": "トロッコ", "chest_minecart": "チェスト付きトロッコ", "furnace_minecart": "かまど付きトロッコ",
    "hopper_minecart": "ホッパー付きトロッコ", "tnt_minecart": "TNT付きトロッコ", "lightning_rod": "避雷針",
    "redstone_torch": "レッドストーンの松明", "stone_button": "石のボタン", "stone_pressure_plate": "石の感圧板",
    "heavy_weighted_pressure_plate": "重量感圧板（重）", "light_weighted_pressure_plate": "重量感圧板（軽）",
    "polished_blackstone_button": "磨かれたブラックストーンのボタン",
    "polished_blackstone_pressure_plate": "磨かれたブラックストーンの感圧板",
    # 木材（旧IDのまま使われるもの）
    "wooden_door": "オークのドア", "wooden_button": "オークのボタン", "wooden_pressure_plate": "オークの感圧板",
    "trapdoor": "オークのトラップドア", "fence": "オークのフェンス", "fence_gate": "オークのフェンスゲート",
    "boat": "オークのボート", "sign": "オークの看板", "oak_sign": "オークの看板", "spruce_sign": "トウヒの看板",
    # 食料
    "bread": "パン", "cake": "ケーキ", "cookie": "クッキー", "pumpkin_pie": "パンプキンパイ",
    "mushroom_stew": "キノコシチュー", "rabbit_stew": "ウサギシチュー", "beetroot_soup": "ビートルートスープ",
    "suspicious_stew": "怪しげなシチュー", "golden_apple": "金のリンゴ", "enchanted_golden_apple": "エンチャントされた金のリンゴ",
    "golden_carrot": "金のニンジン", "glistering_melon_slice": "輝くスイカの薄切り", "melon_slice": "スイカの薄切り",
    "baked_potato": "ベイクドポテト", "cooked_beef": "ステーキ", "cooked_porkchop": "こんがり焼けた豚肉",
    "cooked_chicken": "焼き鳥", "cooked_mutton": "こんがり焼けた羊肉", "cooked_rabbit": "こんがり焼けたウサギ肉",
    "cooked_cod": "焼き鱈", "cooked_salmon": "焼き鮭", "dried_kelp": "乾燥した昆布", "beetroot": "ビートルート",
    "carrot": "ニンジン", "potato": "ジャガイモ", "apple": "リンゴ", "sweet_berries": "スイートベリー",
    "glow_berries": "グロウベリー", "beef": "生の牛肉", "porkchop": "生の豚肉", "chicken": "生の鶏肉",
    "mutton": "生の羊肉", "rabbit": "生のウサギ肉", "cod": "生鱈", "salmon": "生鮭", "tropical_fish": "熱帯魚",
    "pufferfish": "フグ", "rotten_flesh": "腐った肉", "chorus_fruit": "コーラスフルーツ",
    "popped_chorus_fruit": "焼いたコーラスフルーツ", "brown_mushroom": "茶キノコ", "red_mushroom": "赤キノコ",
    "pumpkin_seeds": "カボチャの種", "melon_seeds": "スイカの種", "beetroot_seeds": "ビートルートの種",
    "mushroom": "キノコ", "water_bottle": "水入りの瓶",
}

PREFIX_JA = {
    "waxed": "錆止めされた", "exposed": "風化した", "weathered": "錆びた", "oxidized": "酸化した",
    "polished": "磨かれた", "smooth": "滑らかな", "cut": "切り込み入りの", "chiseled": "模様入りの",
    "cracked": "ひびの入った", "mossy": "苔むした", "stripped": "表皮を剥いだ",
}
STRUCT_SUFFIX = {"stairs": "階段", "slab": "ハーフブロック", "wall": "壁"}

TOOL_MATS = {"wooden": "木", "stone": "石", "iron": "鉄", "golden": "金", "gold": "金",
             "diamond": "ダイヤモンド", "netherite": "ネザライト", "copper": "銅"}
TOOLS = {"sword": "剣", "pickaxe": "ツルハシ", "axe": "斧", "shovel": "ショベル", "hoe": "クワ", "spear": "槍"}
ARMOR_MATS = dict(TOOL_MATS, leather="革", chainmail="チェーン")
ARMOR = {"helmet": "ヘルメット", "chestplate": "チェストプレート", "leggings": "レギンス", "boots": "ブーツ"}
LEATHER_ARMOR = {"helmet": "帽子", "chestplate": "上着", "leggings": "ズボン", "boots": "ブーツ"}
HORSE_ARMOR_MATS = {"iron": "鉄", "golden": "金", "gold": "金", "diamond": "ダイヤモンド", "leather": "革", "copper": "銅"}


def _wood_join(w, suffix):
    return WOOD_JA[w] + ("" if w == "warped" else "の") + suffix


def compose(pid, _depth=0):
    """ID（ネームスペース無し・新形式）から日本語名を組み立てる。無理なら None。"""
    if not pid or _depth > 4:
        return None
    if pid in DIRECT:
        return DIRECT[pid]
    parts = pid.split("_")

    # 道具・防具
    if len(parts) == 2:
        mat, tool = parts
        if mat in TOOL_MATS and tool in TOOLS:
            return TOOL_MATS[mat] + "の" + TOOLS[tool]
        if mat == "leather" and tool in LEATHER_ARMOR:
            return "革の" + LEATHER_ARMOR[tool]
        if mat in ARMOR_MATS and tool in ARMOR:
            return ARMOR_MATS[mat] + "の" + ARMOR[tool]
    if len(parts) == 3 and parts[1] == "horse" and parts[2] == "armor" and parts[0] in HORSE_ARMOR_MATS:
        return HORSE_ARMOR_MATS[parts[0]] + "の馬鎧"

    # 色つき: white_wool など
    for color, cja in COLOR_JA.items():
        if pid.startswith(color + "_"):
            rest = pid[len(color) + 1:]
            if rest in COLOR_ITEMS:
                return cja + "の" + COLOR_ITEMS[rest]

    # 木材: oak_planks など
    for w in WOOD_JA:
        if pid.startswith(w + "_"):
            rest = pid[len(w) + 1:]
            if rest in WOOD_ITEMS:
                return _wood_join(w, WOOD_ITEMS[rest])

    # 深層岩の鉱石
    if pid.startswith("deepslate_") and pid.endswith("_ore"):
        base = compose(pid[len("deepslate_"):], _depth + 1)
        return "深層岩の" + base if base else None

    # 階段・ハーフブロック・壁
    for suf, sja in STRUCT_SUFFIX.items():
        if pid.endswith("_" + suf):
            base = pid[: -len(suf) - 1]
            if base in WOOD_JA:
                return _wood_join(base, sja)
            bname = compose(base, _depth + 1)
            if bname:
                if bname.endswith("ブロック") and ("銅" in bname or "クォーツ" in bname):
                    bname = bname[:-4]  # 切り込み入りの銅ブロック -> 切り込み入りの銅の階段
                return bname + "の" + sja

    # 接頭辞: polished_ / cut_ / waxed_ など
    head, _, rest = pid.partition("_")
    if head in PREFIX_JA and rest:
        base = compose(rest, _depth + 1)
        if base:
            return PREFIX_JA[head] + base
    return None


# ---------------------------------------------------------------- ポーション
POTION_CONTAINER = {
    "potion": "ポーション", "potion_type": "ポーション",
    "splash_potion": "スプラッシュポーション", "lingering_potion": "残留ポーション",
}
POTION_EFFECT = {
    "night_vision": "暗視", "invisibility": "透明化", "leaping": "跳躍", "fire_resistance": "火炎耐性",
    "swiftness": "俊敏", "swift": "俊敏", "slowness": "鈍足", "slow": "鈍足",
    "water_breathing": "水中呼吸", "healing": "治癒", "harming": "負傷", "poison": "毒",
    "regeneration": "再生", "strength": "力", "weakness": "弱化", "turtle_master": "カメの神",
    "slow_falling": "低速落下", "wind_charged": "風撃", "weaving": "粘着", "oozing": "滲出",
    "infestation": "虫食い",
}
POTION_BASE = {"awkward": "奇妙な", "mundane": "ありふれた", "thick": "濃厚な"}


def potion_name(path):
    """'potion_type:awkward' / 'splash_potion:long_swiftness' などを日本語化。非ポーションは None。"""
    head, _, tail = path.partition(":")
    container = POTION_CONTAINER.get(head)
    if not container:
        return None
    if not tail or tail.lstrip("-").isdigit():
        return container
    if tail == "water":
        return "水入りの瓶" if container == "ポーション" else container
    mod = ""
    if tail.startswith("long_"):
        tail, mod = tail[5:], "（延長）"
    elif tail.startswith("strong_"):
        tail, mod = tail[7:], "（強化）"
    if tail in POTION_BASE:
        return POTION_BASE[tail] + container
    if tail in POTION_EFFECT:
        return f"{POTION_EFFECT[tail]}の{container}{mod}"
    return None


# ---------------------------------------------------------------- タグ
TAG_JA = {
    "planks": "板材（各種）", "logs": "原木（各種）", "logs_that_burn": "燃える原木（各種）",
    "wooden_slabs": "木材のハーフブロック（各種）", "wooden_stairs": "木材の階段（各種）",
    "wooden_doors": "木のドア（各種）", "wooden_buttons": "木のボタン（各種）",
    "wooden_pressure_plates": "木の感圧板（各種）", "wooden_fences": "木のフェンス（各種）",
    "wooden_trapdoors": "木のトラップドア（各種）", "boats": "ボート（各種）", "chest_boats": "チェスト付きボート（各種）",
    "stone_crafting_materials": "丸石などの石材", "stone_tool_materials": "石のツールの材料（丸石など）",
    "stone_slabs": "石材のハーフブロック", "wool": "羊毛（各色）", "sand": "砂", "glass": "ガラス",
    "leaves": "葉（各種）", "coals": "石炭または木炭", "soul_fire_base_blocks": "ソウルサンド・ソウルソイル",
    "crimson_stems": "真紅の幹（各種）", "warped_stems": "歪んだ幹（各種）", "mangrove_logs": "マングローブの原木（各種）",
    "cherry_logs": "サクラの原木（各種）", "bamboo_blocks": "竹ブロック（各種）",
    "trimmable_armors": "装飾可能な防具", "trim_materials": "防具装飾の素材", "trim_templates": "防具装飾の鍛冶型",
    "terracotta": "テラコッタ（各色）", "concrete": "コンクリート（各色）", "candles": "ろうそく（各色）",
}
