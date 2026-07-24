import os
import sys
import requests
from datetime import datetime
from zhdate import ZhDate

# Windows本地运行暂停，Linux自动跳过
if os.name == "nt":
    input("程序执行完毕，按回车键关闭窗口")

# 读取config.txt
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
        # 全部必填项
        need_keys = [
            "APP_ID", "APP_SECRET", "TEMPLATE_ID", "OPENID_LIST",
            "CITY", "LOVE_START_DATE", "WEATHER_SOURCE",
            "HEFENG_KEY", "HEFENG_CITY_ID",
            "TIANXING_KEY", "TIANXING_CITY"
        ]
        for k in need_keys:
            if k not in config or not config[k]:
                print(f"配置缺失必填项：{k}")
                sys.exit(1)
        # 拆分多用户OpenID
        config["OPENID_LIST"] = config["OPENID_LIST"].split(",")
        print("推送用户列表：", config["OPENID_LIST"])
        print("当前选用天气接口：", config["WEATHER_SOURCE"])
        return config
    except Exception as err:
        print("读取config失败：", err)
        print("目录文件：", os.listdir("."))
        sys.exit(1)

cfg = read_config()

# 获取微信Token
def get_token(appid, appsecret):
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={appsecret}"
    res = requests.get(url)
    data = res.json()
    print("Token获取返回：", data)
    if "access_token" not in data:
        print("Token获取失败！")
        sys.exit(1)
    return data["access_token"]

# 农历生日计算剩余天数（修复重复文字）
def get_birthday_diff(lunar_str):
    if not lunar_str:
        return ""
    ly, lm, ld = map(int, lunar_str.split("-"))
    today = datetime.now()
    this_year = today.year
    birth_lunar = ZhDate(this_year, lm, ld)
    birth_solar = birth_lunar.to_datetime()
    diff = (birth_solar - today).days
    if diff < 0:
        birth_next = ZhDate(this_year + 1, lm, ld)
        birth_solar_next = birth_next.to_datetime()
        diff = (birth_solar_next - today).days
    # 只输出数字，去掉“还有”
    return str(diff)

# 和风天气数据源
def get_hefeng_data(city_name):
    hf_key = cfg["HEFENG_KEY"]
    city_id = cfg["HEFENG_CITY_ID"]
    today_str = datetime.now().strftime("%Y%m%d")
    # 实时天气、日出日落、空气质量
    weather_res = requests.get(f"https://devapi.qweather.com/v7/weather/now?location={city_id}&key={hf_key}").json()
    sun_res = requests.get(f"https://devapi.qweather.com/v7/astronomy/sun?location={city_id}&date={today_str}&key={hf_key}").json()
    air_res = requests.get(f"https://devapi.qweather.com/v7/air/now?location={city_id}&key={hf_key}").json()

    temp_now = weather_res["now"]["temp"]
    temp_min = weather_res["now"]["tempMin"]
    temp_max = weather_res["now"]["tempMax"]
    weather_text = weather_res["now"]["text"]
    wind_dir = weather_res["now"]["windDir"]
    sunrise = sun_res["sunrise"]
    sunset = sun_res["sunset"]
    pm25 = air_res["now"]["pm2p5"]
    air_level = air_res["now"]["level"]

    return {
        "temp_now": temp_now,
        "temp_min": temp_min,
        "temp_max": temp_max,
        "weather_text": weather_text,
        "wind_dir": wind_dir,
        "sunrise": sunrise,
        "sunset": sunset,
        "pm25": pm25,
        "air_level": air_level
    }

# 天行数据数据源（修复键名判断错误）
def get_tianxing_data(city_name):
    tx_key = cfg["TIANXING_KEY"]
    tx_city = cfg["TIANXING_CITY"]
    # 新版https域名
    url = f"https://api.tianapi.com/tianqi/index?key={tx_key}&city={tx_city}"
    resp = requests.get(url)
    res = resp.json()
    # 打印完整返回日志
    print("=====天行完整返回JSON=====")
    print(res)
    # 修正判断：天行外层是 newslist，不是 result
    if res.get("code") != 200 or "newslist" not in res:
        print("❌ 天行天气接口请求失败，无法获取数据")
        sys.exit(1)
    # 取今日第一条数据 newslist[0]
    data = res["newslist"][0]
    return {
        "temp_now": data["real"],
        "temp_min": data["lowest"],
        "temp_max": data["highest"],
        "weather_text": data["weather"],
        "wind_dir": data["wind"],
        "sunrise": data["sunrise"],
        "sunset": data["sunset"],
        "pm25": data["pcpn"],
        "air_level": data["tips"]
    }

# 统一组装模板消息数据
def get_weather_template(city_name):
    today_date = datetime.now().strftime("%m月%d日")
    # 相恋天数
    love_start = datetime.strptime(cfg["LOVE_START_DATE"], "%Y-%m-%d")
    love_days = (datetime.now() - love_start).days
    # 生日倒计时
    bir1 = get_birthday_diff(cfg.get("BIRTHDAY1_LUNAR", ""))
    bir2 = get_birthday_diff(cfg.get("BIRTHDAY2_LUNAR", ""))
    bir3 = get_birthday_diff(cfg.get("BIRTHDAY3_LUNAR", ""))

    # 根据配置选择接口
    source = cfg["WEATHER_SOURCE"]
    if source == "hefeng":
        w = get_hefeng_data(city_name)
    elif source == "tianxing":
        w = get_tianxing_data(city_name)
    else:
        print("WEATHER_SOURCE 只能填 hefeng 或 tianxing")
        sys.exit(1)

    template_data = {
    "date": {"value": today_date},
    "region": {"value": city_name},
    "weather": {"value": weather_text},
    "min_temp": {"value": f"{w['temp_min']}℃"},
    "max_temp": {"value": f"{w['temp_max']}℃"},
    "temp": {"value": f"{w['temp_now']}℃"},
    "wind_dir": {"value": w["wind_dir"]},
    "pm25": {"value": w["pm25"]},
    "category": {"value": w["air_level"]},
    "sunrise": {"value": w["sunrise"]},
    "sunset": {"value": w["sunset"]},
    # 相爱天数 粉色 #FF69B4
    "love_day": {"value": str(love_days), "color": "#FF69B4"},
    # 生日粉色
    "birthday1": {"value": bir1, "color": "#FF69B4"},
    "birthday2": {"value": bir2, "color": "#FF69B4"},
    "birthday3": {"value": bir3, "color": "#FF69B4"},
    # 今日建议 暖橙色
    "proposal": {"value": "今日适合出门", "color": "#FF7F50"},
    "chp": {"value": ""},
    "note_en": {"value": "Good day"},
    "note_ch": {"value": "祝你今日顺利", "color": "#FF69B4"}
}

# 单用户推送
def send_msg(token, touser, template_id, data):
    send_url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={token}"
    post = {
        "touser": touser,# 组装天气、生日、纪念日全部模板数据（适配天行数据+彩色文字）
def get_weather(city_name):
    from datetime import datetime
    today_date = datetime.now().strftime("%m月%d日")
    # 相恋起始日期
    love_start = datetime.strptime(cfg["LOVE_START_DATE"], "%Y-%m-%d")
    love_days = (datetime.now() - love_start).days

    # 读取天行实时天气
    tx_key = cfg["TIANXING_KEY"]
    tx_city = cfg["TIANXING_CITY"]
    url = f"https://api.tianapi.com/tianqi/index?key={tx_key}&city={tx_city}"
    resp = requests.get(url)
    res = resp.json()
    data = res["newslist"][0]

    # 正确变量名，不要写 weather_text
    weather = data["weather"]
    temp_now = data["real"]
    temp_min = data["lowest"]
    temp_max = data["highest"]
    wind_dir = data["wind"]
    sunrise = data["sunrise"]
    sunset = data["sunset"]
    pm25 = data["pcpn"]
    air_tips = data["tips"]

    # 计算农历生日剩余天数
    bir1 = get_birthday_diff(cfg.get("BIRTHDAY1_LUNAR", ""))
    bir2 = get_birthday_diff(cfg.get("BIRTHDAY2_LUNAR", ""))
    bir3 = get_birthday_diff(cfg.get("BIRTHDAY3_LUNAR", ""))

    template_data = {
        "date": {"value": today_date},
        "region": {"value": city_name},
        "weather": {"value": weather},
        "min_temp": {"value": f"{temp_min}℃"},
        "max_temp": {"value": f"{temp_max}℃"},
        "temp": {"value": f"{temp_now}℃"},
        "wind_dir": {"value": wind_dir},
        "pm2p5": {"value": pm25},
        "category": {"value": air_tips},
        "sunrise": {"value": sunrise},
        "sunset": {"value": sunset},
        "love_day": {"value": str(love_days), "color": "#FF69B4"},
        "birthday1": {"value": bir1, "color": "#FF69B4"},
        "birthday2": {"value": bir2, "color": "#FF69B4"},
        "birthday3": {"value": bir3, "color": "#FF69B4"},
        "proposal": {"value": "今日适合出门", "color": "#FF7F50"},
        "chp": {"value": ""},
        "note_en": {"value": "Good day"},
        "note_ch": {"value": "祝你今日顺利", "color": "#FF69B4"}
    }
    return template_data
        "template_id": template_id,
        "data": data
    }
    resp = requests.post(send_url, json=post)
    print(f"===== 用户 {touser} 推送返回 =====")
    print(resp.json())
    return resp.json()

# 主程序
if __name__ == "__main__":
    token = get_token(cfg["APP_ID"], cfg["APP_SECRET"])
    template_info = get_weather_template(cfg["CITY"])
    # 循环推送多人
    for openid in cfg["OPENID_LIST"]:
        ret = send_msg(token, openid, cfg["TEMPLATE_ID"], template_info)
        if ret.get("errcode") == 0:
            print(f"✅ {openid} 推送成功")
        else:
            print(f"❌ {openid} 推送失败")
