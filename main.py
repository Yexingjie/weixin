import os
import sys
import requests

# Windows本地运行暂停，Linux环境自动跳过
if os.name == "nt":
    input("程序执行完毕，按回车键关闭窗口")

# 从环境变量读取配置，不再读取config.txt
def get_env_config():
    config = {}
    config["APP_ID"] = os.getenv("WX_APP_ID")
    config["APP_SECRET"] = os.getenv("WX_APP_SECRET")
    config["TEMPLATE_ID"] = os.getenv("TEMPLATE_ID")
    config["OPENID"] = os.getenv("USER_OPENID")
    config["CITY"] = os.getenv("CITY")
    # 校验必填项
    for k, v in config.items():
        if not v:
            print(f"环境变量 {k} 为空，请检查GitHub Secrets配置")
            sys.exit(1)
    return config

# 加载配置
cfg = get_env_config()

# --------------------------
# 粘贴你自己的 天气查询、微信推送 业务代码
# --------------------------
# 测试打印配置，方便看日志校验
print("加载的城市：", cfg["CITY"])
print("接收人OpenID：", cfg["OPENID"])
