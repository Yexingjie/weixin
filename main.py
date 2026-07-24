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

# 测试打印配置，方便看日志校验
print("加载的城市：", cfg["CITY"])
print("接收人OpenID：", cfg["OPENID"])

# --------------------------
# 1. 获取微信access_token
def get_token(appid, appsecret):
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={appsecret}"
    res = requests.get(url)
    data = res.json()
    print("获取Token返回：", data)
    if "access_token" not in data:
        print("Token获取失败！")
        sys.exit(1)
    return data["access_token"]

# 2. 获取天气（和风天气示例，你替换成自己的天气接口）
def get_weather(city_name):
    # 这里替换成你自己的天气接口代码，返回模板需要的所有字段
    weather_data = {
        "date": {"value": "2026-07-24"},
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
        "love_day": {"value": "777"},
        "birthday1": {"value": ""},
        "birthday2": {"value": ""},
        "birthday3": {"value": ""},
        "proposal": {"value": "今日适合出门"},
        "chp": {"value": ""},
        "note_en": {"value": "Good day"},
        "note_ch": {"value": "祝你今日顺利"}
    }
    return weather_data

# 3. 发送微信模板消息
def send_msg(token, openid, template_id, weather_info):
    send_url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={token}"
    post_json = {
        "touser": openid,
        "template_id": template_id,
        "data": weather_info
    }
    resp = requests.post(send_url, json=post_json)
    # 核心调试打印：输出微信官方返回结果，直接看到失败原因
    print("====================微信推送返回结果====================")
    print(resp.json())
    return resp.json()

# 主执行流程
if __name__ == "__main__":
    # 获取token
    access_token = get_token(cfg["APP_ID"], cfg["APP_SECRET"])
    # 获取天气数据
    weather_info = get_weather(cfg["CITY"])
    # 发送消息
    send_result = send_msg(access_token, cfg["OPENID"], cfg["TEMPLATE_ID"], weather_info)
    if send_result.get("errcode") == 0:
        print("✅ 消息推送请求发送成功，请去公众号服务通知查看")
    else:
        print("❌ 推送失败，查看上方返回码排查问题")

