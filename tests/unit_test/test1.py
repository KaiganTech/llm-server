# 地区
import json
import requests
import pytz
from datetime import datetime

def get_location_by_ip():
    """通过公共IP地址获取地理位置信息"""
    try:
        # 使用ipapi.co服务（免费，无需API密钥）
        response = requests.get('https://ipapi.co/json/', timeout=10)
        data = response.json()
        
        return {
            "ip": data.get('ip', '未知'),
            "城市": data.get('city', '未知'),
            "地区": data.get('region', '未知'),
            "省份": data.get('region', '未知'),
            "国家": data.get('country_name', '未知'),
            "国家代码": data.get('country_code', '未知'),
            "时区": data.get('timezone', '未知'),
            "经纬度": f"{data.get('latitude', '未知')}, {data.get('longitude', '未知')}",
            "运营商": data.get('org', '未知')
        }
    except Exception as e:
        return {"error": f"获取位置信息失败: {str(e)}"}


# 时间
def get_current_time(time_zone):
    """获取当前时间"""
    # 获取当前时间（可指定时区）
    current_tz = pytz.timezone(time_zone)
    current_time = datetime.now(current_tz)
    
    # 格式化时间
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S %Z%z")
    weekday = current_time.strftime("%A")
    
    return {
        "date": current_time.strftime("%Y-%m-%d"),
        "time": current_time.strftime("%H:%M:%S"),
        "weekday": weekday,
        "full_time": formatted_time
    }


# langchain_tavily：支持网络搜索
def get_weather_real(city_name, api_key):
    """使用Tavily API获取实时天气"""
    try:
        url = f"https://api.tavily.com/v1/weather?city={city_name}"
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(url, headers=headers)
        data = response.json()
        return data
    except Exception as e:
        return {"error": f"获取天气信息失败: {str(e)}"}
  
if __name__ == "__main__":
    # 完整版本
    location_info = get_location_by_ip()
    
    print("\n" + "=" * 50)
    print("简化版地区信息:")
    for key, value in location_info.items():
        print(f"{key}: {value}")
    time_zone = location_info.get('时区', 'Asia/Shanghai')
    time_info = get_current_time(time_zone)
    print("\n当前时间:")
    for key, value in time_info.items():
        print(f"{key}: {value}")
    
    