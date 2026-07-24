import os
import sys
import requests
from datetime import datetime
from zhdate import ZhDate

# Windows本地运行暂停，Linux环境自动跳过
if os.name == "nt":
    input("程序执行完毕，按回车键关闭窗口")

# 读取config.txt配置函数
def read_config():
    try:
        with open("config.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
        config = {}
        for line in lines:
            line = line.strip()
            if not line or "=" not in line:
                continue
            key, value = line.split("=", 1)
            config[key.strip()] = value.strip()
        # 必填字段校验
        need_keys = ["APP_ID", "APP_SECRET", "TEMPLATE_ID", "OPENID_LIST", "CITY", "LOVE_START_DATE"]
        for k in need_keys:
            if k not in config or not config[k]:
                print(f"配置文件缺少必填项：{k}")
                sys.exit(1)
        # 拆分多用户OpenID
        config["OPENID_LIST"] = config["OPENID_LIST"].split(",")
        print("待推送用户列表：", config["OPENID_LIST"])
        return config
    except Exception as err:
        print("读取config.txt失败：", err)
        print("当前目录所有文件：", os.listdir("."))
        sys.exit(1)

# 加载配置
cfg = read_config()

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

# 计算农历生日距离今天还有多少天
def get_birthday_diff(lunar_str):
    if not lunar_str:
        return ""
    # 解析农历生日：农历年 月 日
    lunar_year, lunar_month, lunar_day = map(int, lunar_str.split("-"))
    today = datetime.now()
    this_year = today.year
    # 今年的农历生日转公历
    birth_lunar = ZhDate(this_year, lunar_month, lunar_day)
    birth_solar = birth_lunar.to_datetime()
    diff = (birth_solar - today).days
    # 今年生日已过，算明年
    if diff < 0:
        birth_lunar_next = ZhDate(this_year + 1, lunar_month, lunar_day)
        birth_solar_next = birth_lunar_next.to_datetime()
        diff = (birth_solar_next - today).days
    return f"还有{diff}天"

# 组装天气、生日、纪念日全部模板数据
def get_weather(city_name):
    today = datetime.now().strftime("%m月%d日")
    # 相恋天数计算
    love_start = datetime.strptime(cfg["LOVE_START_DATE"], "%Y-%m-%d")
    love_days = (datetime.now() - love_start).days

    # 计算三个农历生日剩余天数
    bir1 = get_birthday_diff(cfg.get("BIRTHDAY1_LUNAR", ""))
    bir2 = get_birthday_diff(cfg.get("BIRTHDAY2_LUNAR", ""))
    bir3 = get_birthday_diff(cfg.get("BIRTHDAY3_LUNAR", ""))

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
        "birthday1": {"value": bir1},
        "birthday2": {"value": bir2},
        "birthday3": {"value": bir3},
        "proposal": {"value": "今日适合出门"},
        "chp": {"value": ""},
        "note_en": {"value": "Good day"},
        "note_ch": {"value": "祝你今日顺利"}
    }
    return weather_info

# 单人推送函数
def send_weixin_msg(token, touser, template_id, data):
    send_url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={token}"
    post_data = {
        "touser": touser,
        "template_id": template_id,
        "data": data
    }
    resp = requests.post(send_url, json=post_data)
    print(f"===== 推送用户 {touser} 返回信息 =====")
    print(resp.json())
    return resp.json()

# 主程序
if __name__ == "__main__":
    access_token = get_token(cfg["APP_ID"], cfg["APP_SECRET"])
    weather_data = get_weather(cfg["CITY"])
    # 循环给所有关注人推送
    for openid in cfg["OPENID_LIST"]:
        send_result = send_weixin_msg(access_token, openid, cfg["TEMPLATE_ID"], weather_data)
        if send_result.get("errcode") == 0:
            print(f"✅ 用户 {openid} 推送成功")
        else:
            print(f"❌ 用户 {openid} 推送失败，查看上方返回码")
