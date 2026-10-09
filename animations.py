"""
鲸鱼娘桌宠 - 动画目录
所有106个GIF动画按功能分类，文件名用拼音（与 assets/gif/ 下一致）
"""
import os
import random

GIF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "gif")
GIF_HD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "gif_hd")

IDLE = ["daiji-huxi-xiuxian"]
TURN = ["dongzhangxiwang"]
DRAG = ["beishubiao-tuozhuai-xuankong-fankui"]

CLICKS = [
    "dianji-huiying-kaixin-yuedong",
    "dianji-huiying-haixiu-jingya",
    "dianji-huiying-aojiao-shengqi-ceshen-zhanshi",
    "dianji-huiying-naoyang-gegexiao",
    "dianji-huiying-yuanqi-huishou",
]

MOVES = [
    "pangxie-zoulu",
    "yuandi-piaofu-tabu",
    "yuandi-zuozhuan-benpao",
]

SMALL_ACTIONS = [
    "youxian-hengga", "chaoda-shenlanyao", "yuandi-qiaoji-zhuomian-hudong",
    "yuandi-zhongli-xiadun-yasuo", "haqian-liantian", "yuandi-xiaoqi-chenmian",
    "nvpu-quxi-liyi", "beixiayitiao-zhamao", "xiaofudu-yuandi-360du-xuanzhuan-zhanshi",
    "touchi-lingshi-bei-zhuazhu", "yong-jingyu-weiba-paidadi", "da-keshui-bei-jingxing",
    "zhao-jingzi", "zhengti-huanzhuang-shise", "qingkuai-jilu", "xie-daima",
    "yaoshan-naliang", "chenjian-shuaya",
]

PLAY = [
    "yuandi-zhuanxin-wan-mofang", "yuandi-dunxia-wan-wanju-qiche", "jingyu-tu-paopao-texiao",
    "yuandi-tiaoyue-zhuasui-touding-wupin", "wan-youxi-qijibaituai", "wan-shuiqiang",
    "xiaotiqin-yanzou", "lanjing-xianshi", "youya-nvpuwu", "qingkuai-yaobaiwu",
    "keai-zhaiwu", "chui-qiqiu", "dongwu-huanrao", "fang-fengzheng", "chai-liwu",
    "bian-gezi", "puke-moshu", "chou-tuoluo", "chui-dizi",
    "hudie-mifeng-huanrao-touding-kaihua", "lu-mao", "pingkong-shenghua", "qi-muma",
    "sanqiu-paojie", "ti-jianzi", "xiawuziqi", "dangqiuqian",
]

EAT = [
    "chi-baifan", "dakou-chi-lingshi", "chi-token", "chi-zaocan", "chi-wucan",
    "chi-wancan", "chi-bingqilin-ronghua", "chi-dazhaxie", "chi-tanghulu",
    "chi-changshoumian", "chi-xigua", "shuan-huoguo",
]

SEASONAL = [
    "beiluoye-yanmo", "zhongqiu-shangyue-chi-yuebing", "duixueren", "fang-yanhua",
    "chi-zongzi", "chi-niangao", "chi-qingtuan", "chi-labazhou", "chi-chongyanggao",
    "shou-hongbao", "xie-fuzi", "chuanzhenqiqiao", "wu-shitou", "taotang-nanguadeng",
    "cha-zhuyu-shangju", "fanghedeng", "menghua-xiaoyouling", "zhuangdian-shengdanshu",
    "fang-kongmingdeng", "chitangyuan", "chijiaozi",
]

TEXT = ["shia-chishenme", "shendu-sikao-suisuinian"]

BALANCE = [
    "qian-dai-man-yi",
    "jin-dai-ding-dang",
    "qian-dai-ru-chang",
    "shu-jin-zhou-mei",
    "dai-kong-ru-xi",
    "fen-wen-bu-sheng",
]

WHISPER = [
    "suisuinian-cazhuo-suisuinian",
    "suisuinian-fadai-suisuinian",
    "suisuinian-duiping-suisuinian",
]

WORK_STATUS = [
    "gongzuozhuangtai-sikao-maopao",
    "gongzuozhuangtai-manglu-dianan",
    "gongzuozhuangtai-qingdian-guidang",
    "gongzuozhuangtai-yuandi-duobu-zhangwang",
    "gongzuozhuangtai-queyue-qingzhu",
    "gongzuozhuangtai-chuitou-tanqi-maohan",
]

RANDOM_POOL = SMALL_ACTIONS + PLAY + EAT + SEASONAL + TEXT + WHISPER + WORK_STATUS

CATEGORIES = {
    "待机": IDLE,
    "转向": TURN,
    "拖拽": DRAG,
    "点击回应": CLICKS,
    "移动": MOVES,
    "小动作": SMALL_ACTIONS,
    "玩耍": PLAY,
    "吃什么": EAT,
    "时节": SEASONAL,
    "文字": TEXT,
    "余额": BALANCE,
    "碎碎念": WHISPER,
    "工作状态": WORK_STATUS,
}


def gif_path(name: str) -> str:
    webp_path = os.path.join(GIF_HD_DIR, name + ".webp")
    if os.path.exists(webp_path):
        return webp_path
    hd_gif_path = os.path.join(GIF_HD_DIR, name + ".gif")
    if os.path.exists(hd_gif_path):
        return hd_gif_path
    return os.path.join(GIF_DIR, name + ".gif")


def all_animations() -> list[str]:
    names = []
    for v in CATEGORIES.values():
        names.extend(v)
    return names


def pick_random(exclude: str | None = None) -> str:
    pool = [a for a in RANDOM_POOL if a != exclude]
    return random.choice(pool)


def pick_click(exclude: str | None = None) -> str:
    pool = [a for a in CLICKS if a != exclude]
    return random.choice(pool)


def balance_animation(used_percent: float) -> str:
    if used_percent >= 100:
        return BALANCE[5]
    idx = int(used_percent // 20)
    return BALANCE[min(idx, 5)]