# 临时 CORS 服务器：向浏览器前端提供【技能内归档的工作流副本】（只服务本机 127.0.0.1）
# 用法：复制到 D 盘任意目录（严禁 C 盘！），后台运行：
#   cd D:/xxx && python serve_wf.py
# 验证：curl -s http://127.0.0.1:8765/ping  →  pong
# 取工作流：curl http://127.0.0.1:8765/wf/<URL编码文件名>.json
#
# ⚠️ 固定副本机制：WF_DIR 指向技能库 workflows/ 目录，而非作者的实时工作流目录。
#   作者在原位置更新工作流不影响这里加载的副本——每次行为一致，稳定可靠。
#   新增工作流：把 json 拷进 workflows/<工作流名>/ 即可，无需改本脚本。
import http.server
import urllib.parse

# 技能库工作流归档根目录（所有工作流副本平铺/分子目录存放于此）
WF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'workflows') + os.sep

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/wf/'):
            fname = urllib.parse.unquote(self.path[4:])
            try:
                data = open(WF_DIR + fname, 'rb').read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(data)
            except Exception:
                self.send_response(404)
                self.end_headers()
        elif self.path == '/ping':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'pong')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *a):
        pass

http.server.HTTPServer(('127.0.0.1', 8765), Handler).serve_forever()
