"""
余额查询模块
支持多个 AI 提供商的账户余额查询
返回统一格式: {"balance": float, "currency": str, "is_available": bool, "error": str|None}
"""
import json
import urllib.request
import urllib.error


def _http_get(url: str, api_key: str, extra_headers: dict = None) -> dict:
    """发送 GET 请求，返回解析后的 JSON 或抛出异常"""
    headers = {"Authorization": f"Bearer {api_key}"}
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def query_deepseek(api_key: str) -> dict:
    data = _http_get("https://api.deepseek.com/user/balance", api_key)
    infos = data.get("balance_infos", [])
    if not infos:
        return {"balance": 0.0, "currency": "CNY", "is_available": False, "error": "余额接口返回结构异常"}
    info = (
        next((x for x in infos if x.get("currency") == "CNY" and float(x.get("total_balance", 0)) > 0), None)
        or next((x for x in infos if float(x.get("total_balance", 0)) > 0), None)
        or next((x for x in infos if x.get("currency") == "CNY"), None)
        or infos[0]
    )
    bal = float(info.get("total_balance", 0))
    return {"balance": bal, "currency": info.get("currency", "CNY"), "is_available": True, "error": None}


BALANCE_QUERY_FUNCS = {
    "deepseek": query_deepseek,
}

UNSUPPORTED_PROVIDERS = {
    "ollama": "本地模型无需查余额~",
    "openai": "我只能支持 DeepSeek 的查询余额哦",
    "claude": "我只能支持 DeepSeek 的查询余额哦",
    "qwen": "我只能支持 DeepSeek 的查询余额哦",
    "glm": "我只能支持 DeepSeek 的查询余额哦",
    "kimi": "我只能支持 DeepSeek 的查询余额哦",
    "ernie": "我只能支持 DeepSeek 的查询余额哦",
    "doubao": "我只能支持 DeepSeek 的查询余额哦",
    "spark": "我只能支持 DeepSeek 的查询余额哦",
    "stepfun": "我只能支持 DeepSeek 的查询余额哦",
    "minimax": "我只能支持 DeepSeek 的查询余额哦",
    "siliconflow": "我只能支持 DeepSeek 的查询余额哦",
    "gemini": "我只能支持 DeepSeek 的查询余额哦",
    "groq": "我只能支持 DeepSeek 的查询余额哦",
    "openrouter": "我只能支持 DeepSeek 的查询余额哦",
    "mistral": "我只能支持 DeepSeek 的查询余额哦",
    "custom": "我只能支持 DeepSeek 的查询余额哦",
}


def query_balance(provider: str, api_key: str) -> dict:
    """
    统一余额查询入口
    provider: AI 提供商标识（与 ai_chat.PROVIDERS 的 key 一致）
    返回: {"balance": float, "currency": str, "is_available": bool, "error": str|None}
    """
    if not api_key:
        return {"balance": 0.0, "currency": "", "is_available": False, "error": "未配置 API Key"}

    func = BALANCE_QUERY_FUNCS.get(provider)
    if func:
        try:
            return func(api_key)
        except urllib.error.HTTPError as e:
            msg = f"HTTP {e.code}"
            try:
                body = json.loads(e.read().decode("utf-8"))
                msg = body.get("msg", body.get("message", body.get("error", {}).get("message", msg)))
            except Exception:
                pass
            return {"balance": 0.0, "currency": "", "is_available": False, "error": msg}
        except Exception as e:
            return {"balance": 0.0, "currency": "", "is_available": False, "error": str(e)}

    reason = UNSUPPORTED_PROVIDERS.get(provider, "该提供商暂不支持余额查询")
    return {"balance": 0.0, "currency": "", "is_available": False, "error": reason}