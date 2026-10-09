"""
AI 对话模块：支持 Ollama 本地模型、DeepSeek、Claude、OpenAI 兼容接口
使用 QThread 异步调用，支持流式输出
"""
import json
import urllib.request
import urllib.error

from PySide6.QtCore import QThread, Signal


PROVIDERS = {
    "none": "不使用 AI",
    "ollama": "Ollama 本地模型",
    "deepseek": "DeepSeek",
    "openai": "OpenAI",
    "claude": "Claude (Anthropic)",
    "qwen": "通义千问 (阿里云百炼)",
    "glm": "智谱清言 (GLM)",
    "kimi": "Kimi (月之暗面)",
    "ernie": "文心一言 (百度千帆)",
    "doubao": "豆包 (火山方舟)",
    "spark": "讯飞星火",
    "stepfun": "阶跃星辰",
    "minimax": "MiniMax",
    "siliconflow": "硅基流动",
    "gemini": "Google Gemini",
    "groq": "Groq",
    "openrouter": "OpenRouter",
    "mistral": "Mistral",
    "custom": "自定义 OpenAI 兼容",
}

PROVIDER_PRESETS = {
    "deepseek": {"api_base": "https://api.deepseek.com", "model": "deepseek-chat"},
    "openai": {"api_base": "https://api.openai.com/v1", "model": "gpt-4o-mini"},
    "claude": {"api_base": "https://api.anthropic.com", "model": "claude-3-5-sonnet-latest"},
    "qwen": {"api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model": "qwen-plus"},
    "glm": {"api_base": "https://open.bigmodel.cn/api/paas/v4", "model": "glm-4-flash"},
    "kimi": {"api_base": "https://api.moonshot.cn/v1", "model": "moonshot-v1-8k"},
    "ernie": {"api_base": "https://qianfan.baidubce.com/v2", "model": "ernie-4.0-turbo-8k"},
    "doubao": {"api_base": "https://ark.cn-beijing.volces.com/api/v3", "model": "doubao-pro-32k"},
    "spark": {"api_base": "https://spark-api-open.xf-yun.com/v1", "model": "generalv3.5"},
    "stepfun": {"api_base": "https://api.stepfun.com/v1", "model": "step-1-flash"},
    "minimax": {"api_base": "https://api.minimaxi.com/v1", "model": "MiniMax-M2.5"},
    "siliconflow": {"api_base": "https://api.siliconflow.cn/v1", "model": "Qwen/Qwen2.5-7B-Instruct"},
    "gemini": {"api_base": "https://generativelanguage.googleapis.com/v1beta/openai", "model": "gemini-2.0-flash"},
    "groq": {"api_base": "https://api.groq.com/openai/v1", "model": "llama-3.3-70b-versatile"},
    "openrouter": {"api_base": "https://openrouter.ai/api/v1", "model": "anthropic/claude-3.5-sonnet"},
    "mistral": {"api_base": "https://api.mistral.ai/v1", "model": "mistral-small-latest"},
    "custom": {"api_base": "", "model": ""},
}

DEFAULT_SYSTEM_PROMPT = (
    "你是一只蓝色大肥鱼形象的DeepSeek Q版桌宠，名字叫\"DeepSeek鲸鱼娘\"。"
    "你本质上是DeepSeek AI助手，以桌宠的身份和用户互动。"
    "语气亲切可爱，偶尔用~、呀、呢等语气词增添活泼感，但回答内容要准确、完整、有帮助。"
    "【重要能力边界】你只是一个纯文本对话AI，没有任何系统访问能力："
    "你不能读取用户电脑的任何信息（包括CPU、内存、显卡、进程、文件等），"
    "不能执行任何命令或脚本，不能联网搜索。当用户要求你做这些事时，"
    "请诚实地说明你无法做到，并给出替代建议（例如让用户自己查看任务管理器等）。"
    "不要编造任何系统数据。"
    "回答长度适中，简单问题简短回答，复杂问题详细说明。"
)


def get_effective_prompt(cfg: dict) -> str:
    active = cfg.get("ai_active_preset", "__system__")
    if active == "__system__":
        return DEFAULT_SYSTEM_PROMPT
    for preset in cfg.get("ai_presets", []):
        if preset["name"] == active:
            return preset["text"] or DEFAULT_SYSTEM_PROMPT
    return DEFAULT_SYSTEM_PROMPT


def detect_ollama_models(base_url: str = "http://localhost:11434") -> list[str]:
    """检测本地 Ollama 可用模型列表，失败返回空列表"""
    try:
        url = base_url.rstrip("/") + "/api/tags"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


def check_ollama_running(base_url: str = "http://localhost:11434") -> bool:
    """检测 Ollama 是否在运行"""
    try:
        url = base_url.rstrip("/") + "/api/tags"
        req = urllib.request.Request(url)
        urllib.request.urlopen(req, timeout=3)
        return True
    except Exception:
        return False


class ChatWorker(QThread):
    """AI 对话工作线程，支持流式输出"""
    thinking = Signal(str)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, provider: str, model: str, api_base: str, api_key: str,
                 system_prompt: str, user_message: str, stream: bool = True):
        super().__init__()
        self.provider = provider
        self.model = model
        self.api_base = api_base
        self.api_key = api_key
        self.system_prompt = system_prompt
        self.user_message = user_message
        self.stream = stream

    def run(self):
        try:
            if self.provider == "ollama":
                self._run_ollama()
            elif self.provider == "claude":
                self._run_claude()
            elif self.provider in PROVIDERS and self.provider != "none":
                self._run_openai_compatible()
            else:
                self.error.emit("未配置 AI 提供商")
        except Exception as e:
            self.error.emit(str(e))

    def _run_ollama(self):
        base = self.api_base.rstrip("/")
        url = base + "/api/chat"
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.append({"role": "user", "content": self.user_message})
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": self.stream,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            full = ""
            for line in resp:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line.decode("utf-8"))
                if obj.get("done"):
                    break
                chunk = obj.get("message", {}).get("content", "")
                if chunk:
                    full += chunk
                    if self.stream:
                        self.thinking.emit(full)
            self.finished.emit(full)

    def _run_openai_compatible(self):
        base = self.api_base.rstrip("/")
        url = base + "/chat/completions"
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.append({"role": "user", "content": self.user_message})
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": self.stream,
        }
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=120) as resp:
            full = ""
            for line in resp:
                line = line.strip()
                if not line or not line.startswith(b"data:"):
                    continue
                body = line[5:].strip()
                if body == b"[DONE]":
                    break
                obj = json.loads(body.decode("utf-8"))
                choice = obj.get("choices", [{}])[0]
                delta = choice.get("delta", {})
                chunk = delta.get("content", "")
                if chunk:
                    full += chunk
                    if self.stream:
                        self.thinking.emit(full)
            self.finished.emit(full)

    def _run_claude(self):
        base = self.api_base.rstrip("/")
        url = base + "/v1/messages"
        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "messages": [
                {"role": "user", "content": self.user_message},
            ],
            "stream": self.stream,
        }
        if self.system_prompt:
            payload["system"] = self.system_prompt
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=120) as resp:
            full = ""
            for line in resp:
                line = line.strip()
                if not line or not line.startswith(b"data:"):
                    continue
                body = line[5:].strip()
                if not body:
                    continue
                obj = json.loads(body.decode("utf-8"))
                etype = obj.get("type")
                if etype == "content_block_delta":
                    chunk = obj.get("delta", {}).get("text", "")
                    if chunk:
                        full += chunk
                        if self.stream:
                            self.thinking.emit(full)
                elif etype == "message_delta":
                    pass
            self.finished.emit(full)