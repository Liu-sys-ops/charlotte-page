# 前后端联调与部署说明

## 1. 本地联调

后端：

```powershell
cd todo-api
.\start_api.bat
```

前端（不要直接双击 index.html，用 HTTP 服务避免 file:// 的 origin 问题）：

```powershell
cd 新建文件夹
python -m http.server 8080
```

打开：

```text
http://127.0.0.1:8080/index.html#todo
```

## 2. 配置项

后端地址只在 `config.js` 中配置：

```js
window.APP_CONFIG = {
  API_BASE_URL: "http://127.0.0.1:5000"
};
```

`app.js` 只读取 `window.APP_CONFIG.API_BASE_URL`，业务代码中没有写死后端地址。

## 3. CORS

后端 `app.py` 使用 `after_request` 给所有响应加：

```python
response.headers["Access-Control-Allow-Origin"] = "*"
response.headers["Access-Control-Allow-Headers"] = "Content-Type"
response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
```

验证预检请求：

```powershell
curl.exe -i -X OPTIONS "http://127.0.0.1:5000/api/todos" `
  -H "Origin: http://127.0.0.1:8080" `
  -H "Access-Control-Request-Method: POST" `
  -H "Access-Control-Request-Headers: content-type"
```

应看到 `HTTP/1.1 200 OK` 和 `Access-Control-Allow-Origin: *`。

## 4. 部署后端到 Render

1. 把 `todo-api` 文件夹上传到 GitHub 仓库。
2. Render 新建 Web Service，连接仓库。
3. Root Directory 填 `todo-api`。
4. Build Command：`pip install -r requirements.txt`
5. Start Command：`gunicorn app:app`
6. 部署完成后打开：

```text
https://你的服务名.onrender.com/api/todos
```

看到 `{"code":0,"data":[],"msg":"ok"}` 就成功。

注意：Render 免费实例的本地文件系统是临时的，刷新页面数据在，但重新部署可能清空 SQLite。作业演示够用；要长期保存，挂载 Render Disk 或换 Postgres。

## 5. 部署前端到 GitHub Pages

1. 修改 `config.js`：

```js
window.APP_CONFIG = {
  API_BASE_URL: "https://你的服务名.onrender.com"
};
```

2. 把 `index.html`、`config.js`、`app.js`、`demo.js`、`data.json`、`bgm.mp3`、`images/` 上传到 GitHub Pages 仓库。
3. 打开 `https://liu-sys-ops.github.io/charlotte-page/`，按 `Ctrl + F5`。
4. 进入“待办清单”，应能看到 loading → empty/成功列表；新增、删除后自动刷新。

## 6. 线上白屏/请求失败排查顺序

1. 直接打开后端 `/api/todos`，确认后端活着。
2. 看 `config.js` 是否是线上 HTTPS 地址，末尾不要多斜杠。
3. F12 → Console 看是否有 CORS 或 Mixed Content 报错。
4. F12 → Network 看请求 URL、状态码、响应头 `Access-Control-Allow-Origin`。
5. GitHub Pages 是 HTTPS，后端必须 HTTPS；不能写 `http://127.0.0.1:5000`。
6. 改完 `config.js` 必须 `Ctrl + F5`，浏览器会缓存旧配置。

## 7. 真实 CORS 报错记录

复现方式：前端跑在 `http://127.0.0.1:8080`，后端临时换成一个没有 CORS 头的 5003 端口。

Console 原文：

```text
Access to fetch at 'http://127.0.0.1:5003/api/todos' from origin 'http://127.0.0.1:8080' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
TypeError: Failed to fetch
```

解决：在 Flask 的 `after_request` 中加 `Access-Control-Allow-Origin: *`，并允许 `Content-Type` 请求头；重新发 OPTIONS 预检返回 200，GET 返回 200。
