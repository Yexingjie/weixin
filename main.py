import os
import sys
import requests

# Windows本地运行暂停，Linux环境自动跳过
if os.name == "nt":
    input("程序执行完毕，按回车键关闭窗口")

# 读取config.txt配置函数
def read_config():
    try:
        # 强制utf-8编码，兼容Linux中文
        with open("config.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
        config = {}
        for line in lines:
            line = line.strip()
            if not line or "=" not in line:
                continue
            key, value = line.split("=", 1)
            config[key.strip()] = value.strip()
        return config
    except Exception as err:
        print("读取配置文件失败：", err)
        print("当前目录所有文件：", os.listdir("."))
        sys.exit(1)

# 加载配置
cfg = read_config()

# --------------------------
# 在这里粘贴你自己的 天气查询、微信推送 业务代码
# --------------------------
