# splatoon3-bot
  <a href="https://www.kookapp.cn/app/oauth2/authorize?id=23970&permissions=675840&client_id=eg8iC9ZeLKLj46G_&redirect_uri=&scope=bot">
    <img src="https://img.shields.io/badge/Kook-splatoon3-orange?style=flat-square" alt="QQ Chat">
  </a>
  <a href="https://t.me/splatoon3_bot">
    <img src="https://img.shields.io/badge/telegram-splatoon3bot-blue?style=flat-square" alt="Telegram">
  </a>


## 机器人[使用文档](https://docs.qq.com/sheet/DUkZHRWtCUkR0d2Nr?tab=BB08J2)

## 自己搭建指南

服务器需要安装2.30版本以上git，deno引擎，deno安装参考https://www.denojs.cn/

python >= 3.9
1. python -m pip install --user pipx
2. python -m pipx ensurepath
3. pipx install nb-cli
4. python -m venv .venv
5. source .venv/bin/activate
6. pip install -r requirements.txt
7. cp .env.sample .env
8. edit .env
9. nb run --reload
