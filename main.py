import os
import requests
from flask import Flask, request
from telegram import Bot
from telegram.constants import ParseMode
from datetime import datetime, timedelta

app = Flask(__name__)
bot = Bot(token=os.environ["BOT_TOKEN"])

CITY_NAME = "Гайсин"
LATITUDE = 48.8125
LONGITUDE = 29.3903
TIMEZONE = "Europe/Kyiv"

def get_weather_forecast():
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={LATITUDE}&longitude={LONGITUDE}"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_hours"
        f"&hourly=wind_speed_10m,apparent_temperature,precipitation"
        f"&timezone={TIMEZONE}"
    )

    response = requests.get(url)
    data = response.json()

    forecast_text = f"🌤️ Прогноз погоди на 3 дні для {CITY_NAME}:\n\n"

    today = datetime.now().date()
    hourly_times = data["hourly"]["time"]
    hourly_wind = data["hourly"]["wind_speed_10m"]
    hourly_precip = data["hourly"]["precipitation"]
    hourly_apparent = data["hourly"]["apparent_temperature"]

    for i in range(3):
        date = today + timedelta(days=i)
        day_str = date.strftime("%d.%m.%Y")

        max_temp = data["daily"]["temperature_2m_max"][i]
        min_temp = data["daily"]["temperature_2m_min"][i]
        precipitation_hours = data["daily"]["precipitation_hours"][i]

        temp_info = f"🌡️ Вдень до {max_temp:.1f}°C, вночі {min_temp:.1f}°C"
        if min_temp <= -5:
            index = data["hourly"]["time"].index(f"{date}T00:00")
            feels_like = hourly_apparent[index]
            temp_info += f" (мороз, відчувається як {feels_like:.1f}°C)"

        # Дощ
        rain_hours = []
        for j, hour in enumerate(hourly_times):
            if hour.startswith(str(date)) and hourly_precip[j] > 0:
                rain_hours.append(hour[11:16])
        if rain_hours:
            start = rain_hours[0]
            end = rain_hours[-1]
            rain_info = f"🌧️ Дощ: з {start} до {end}"
        else:
            rain_info = "☀️ Дощ не очікується"

        # Вітер
        strong_wind_hours = []
        for j, hour in enumerate(hourly_times):
            if hour.startswith(str(date)) and hourly_wind[j] > 4:
                strong_wind_hours.append(int(hour[11:13]))

        wind_info = ""
        if strong_wind_hours:
            if any(6 <= h <= 11 for h in strong_wind_hours):
                wind_info = "💨 Вдень — сильний вітер"
            elif any(12 <= h <= 17 for h in strong_wind_hours):
                wind_info = "💨 Ввечері — сильний вітер"
            else:
                wind_info = "💨 Вночі — сильний вітер"

        forecast_text += (
            f"<b>{day_str}</b>\n"
            f"{temp_info}\n"
            f"{rain_info}\n"
            f"{wind_info}\n\n"
        )

    return forecast_text.strip()

@app.route("/", methods=["GET"])
def index():
    return "Бот працює!"

@app.route("/", methods=["POST"])
def webhook():
    update = request.get_json()

    # 🔎 Вивід у консоль для дебагу
    print("Отримано POST-запит:")
    print(update)

    if "message" in update and "text" in update["message"]:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"]["text"]

        if text.lower() in ["/start", "/weather", "погода"]:
            forecast = get_weather_forecast()
            bot.send_message(chat_id=chat_id, text=forecast, parse_mode=ParseMode.HTML)

    return "ok"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
