import urllib.request, json, os, mimetypes

OWNER = 'csdKK'
REPO = 'whale-desktop-pet'
TAG = 'v1.0.0'
TOKEN = os.environ.get('GITHUB_TOKEN', '')

if not TOKEN:
    print('ERROR: 请先设置 GITHUB_TOKEN 环境变量')
    exit(1)

# 获取 release
url = f'https://api.github.com/repos/{OWNER}/{REPO}/releases/tags/{TAG}'
req = urllib.request.Request(url, headers={'Authorization': f'token {TOKEN}', 'Accept': 'application/vnd.github+json'})
resp = urllib.request.urlopen(req)
release = json.loads(resp.read())
release_id = release['id']
upload_url = release['upload_url'].split('{')[0]
print(f'Release ID: {release_id}')
print(f'Upload URL: {upload_url}')

# 上传安装器 EXE
exe_path = r'E:\All-Code\python-Code\whale-desktop-pet\安装程序exe\WhalePetOnlineInstaller.exe'
exe_name = 'WhalePetOnlineInstaller.exe'
file_size = os.path.getsize(exe_path)
print(f'上传: {exe_name} ({file_size/1024/1024:.2f} MB)')

with open(exe_path, 'rb') as f:
    data = f.read()

upload_req = urllib.request.Request(
    f'{upload_url}?name={exe_name}',
    data=data,
    method='POST',
    headers={
        'Authorization': f'token {TOKEN}',
        'Content-Type': 'application/octet-stream',
        'Accept': 'application/vnd.github+json',
    }
)
try:
    resp = urllib.request.urlopen(upload_req)
    result = json.loads(resp.read())
    print(f'上传成功: {result["name"]} ({result["size"]/1024/1024:.2f} MB)')
    print(f'下载链接: {result["browser_download_url"]}')
except urllib.error.HTTPError as e:
    print(f'上传失败: {e.code} {e.reason}')
    print(e.read().decode())