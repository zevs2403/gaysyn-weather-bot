from flask import Flask, request
import requests
import datetime
import os

app = Flask(name)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Геокоординати Гайсина
LAT = 48.8122
LON = 29.3892

@app.route("/")
def home():
    return "Bot is running."

@app.route("/send_weather", methods=["GET"])
def send_weather():
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&daily=weathercode,temperature_2m_min,temperature_2m_max,apparent_temperature_min,apparent_temperature_max,precipitation_sum,windspeed_10m_max&timezone=Europe%2FKyiv"
        response = requests.get(url)
        data = response.json()

        if "daily" not in data:
            return "❌ Помилка: немає даних daily."

        daily = data["daily"]
        days = []

        for i in range(3):
            date = daily["time"][i]
            weather_code = daily["weathercode"][i]
            temp_min = daily["temperature_2m_min"][i]
            temp_max = daily["temperature_2m_max"][i]
            app_temp_min = daily["apparent_temperature_min"][i]
            app_temp_max = daily["apparent_temperature_max"][i]
            wind = daily["windspeed_10m_max"][i]
            rain = daily["precipitation_sum"][i]

            desc = get_weather_description(weather_code)
            frost_note = ""
            if temp_min <= -5:
                frost_note = f" 🧊 Мороз. Відчувається як {app_temp_min}°C."

            rain_note = ""
            if rain > 0:
                rain_note = f" 🌧️ Дощ: {rain} мм."

            wind_note = ""
            if wind > 4:
                part = get_day_period(i)
                wind_note = f" 💨 Сильний вітер {part}."

            day_report = f"📅 {date}:\n{desc}, 🌡️ вдень до {temp_max}°C, 🌙 вночі до {temp_min}°C.{frost_note}{rain_note}{wind_note}"
            days.append(day_report)

        final_message = f"🌤️ Прогноз погоди на 3 дні для Гайсина:\n\n" + "\n\n".join(days)

        send_telegram(final_message)
        return "✅ Прогноз надіслано!"

    except Exception as e:
        return f"❌ Помилка: {str(e)}"

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }
    requests.post(url, data=payload)

def get_weather_description(code):
    weather_map = {
        0: "☀️ Ясно",
        1: "🌤️ Переважно ясно",
        2: "⛅ Мінлива хмарність",
        3: "☁️ Хмарно",
        45: "🌫️ Туман",
        48: "🌫️ Іній",
        51: "🌦️ Легкий дощ",
        61: "🌧️ Дощ",
        71: "🌨️ Сніг",
        95: "⛈️ Гроза"
    }
    return weather_map.get(code, "🌡️ Невідома погода")

def get_day_period(day_index):
    if day_index == 0:
        return "сьогодні"
    elif day_index == 1:
        return "завтра"
    else:
        return "післязавтра"

if __name__ == "__main__":
port = int(oc.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
