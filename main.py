import os
import sys
import requests
from datetime import datetime

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
        # 校验必填字段
        need_keys = ["APP_ID", "APP_SECRET", "TEMPLATE_ID", "OPENID", "CITY", "LOVE_START_DATE"]
        for k in need_keys:
            if k not in config or not config[k]:
                print(f"配置文件缺少必填项：{k}")
                sys.exit(1)
        return config
    except Exception as err:
        print("读取config.txt失败：", err)
        print("当前目录所有文件：", os.listdir("."))
        sys.exit(1)

# 加载配置文件
cfg = read_config()

# 打印调试信息
print("加载城市：", cfg["CITY"])
print("接收人OpenID：", cfg["OPENID"])

# 获取微信access_token
def get_token(appid, appsecret):
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={appsecret}"
    res = requests.get(url)
    data = res.json()
    print("Token获取返回：", data)
    if "access_token" not in data:
        print("access_token 获取失败！")
        sys.exit(1)
    return data["access_token"]

# 获取天气数据（你自行替换真实天气接口）
def get_weather(city_name):
    # 此处替换成你的天气API请求代码
    # 示例静态结构，对接真实接口后删除固定值
    today = datetime.now().strftime("%m月%d日")
    # 计算相爱天数
    love_start = datetime.strptime(cfg["LOVE_START_DATE"], "%Y-%m-%d")
    love_days = (datetime.now() - love_start).days

    weather_info = {
        "date": {"value": today},
        "region": {"value": city_name},
        "weather": {"value": "晴"},
        "min_temp": {"value": "25℃"},
        "max_temp": {"value": "33℃"},
        "temp": {"value": "28℃"},
        "wind_dir": {"value": "东南风"},
        "pm2p5": {"value": "12"},
        "category": {"value": "优"},
        "sunrise": {"value": "05:10"},
        "sunset": {"value": "19:05"},
        "love_day": {"value": str(love_days)},
        "birthday1": {"value": cfg.get("BIRTHDAY1", "")},
        "birthday2": {"value": cfg.get("BIRTHDAY2", "")},
        "birthday3": {"value": cfg.get("BIRTHDAY3", "")},
        "proposal": {"value": "今日适合出门"},
        "chp": {"value": ""},
        "note_en": {"value": "Good day"},
        "note_ch": {"value": "祝你今日顺利"}
    }
    return weather_info

# 发送微信模板消息
def send_weixin_msg(token, touser, template_id, data):
    send_url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={token}"
    post_data = {
        "touser": touser,
        "template_id": template_id,
        "data": data
    }
    resp = requests.post(send_url, json=post_data)
    print("========微信推送完整返回信息========")
    print(resp.json())
    return resp.json()

# 主程序入口
if __name__ == "__main__":
    # 1. 获取access_token
    access_token = get_token(cfg["APP_ID"], cfg["APP_SECRET"])
    # 2. 获取天气+日期数据
    weather_data = get_weather(cfg["CITY"])
    # 3. 发送模板消息
    send_result = send_weixin_msg(access_token, cfg["OPENID"], cfg["TEMPLATE_ID"], weather_data)
    if send_result.get("errcode") == 0:
        print("✅ 消息推送成功，前往公众号服务通知查看")
    else:
        print("❌ 推送失败，查看上方返回码排查问题")
