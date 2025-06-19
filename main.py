import os
import requests
import asyncio
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

        temp_info = f"🌡️ Вдень до {max_temp:.1f}°C, вночі {min_temp:.1f}°C"
        if min_temp <= -5:
            index = hourly_times.index(f"{date}T00:00")
            feels_like = hourly_apparent[index]
            temp_info += f" (мороз, відчувається як {feels_like:.1f}°C)"

        rain_hours = [hour[11:16] for j, hour in enumerate(hourly_times)
                      if hour.startswith(str(date)) and hourly_precip[j] > 0]
        rain_info = f"🌧️ Дощ: з {rain_hours[0]} до {rain_hours[-1]}" if rain_hours else "☀️ Дощ не очікується"

        strong_wind_hours = [int(hour[11:13]) for j, hour in enumerate(hourly_times)
                             if hour.startswith(str(date)) and hourly_wind[j] > 4]
        if strong_wind_hours:
            if any(6 <= h <= 11 for h in strong_wind_hours):
                wind_info = "💨 Вдень — сильний вітер"
            elif any(12 <= h <= 17 for h in strong_wind_hours):
                wind_info = "💨 Ввечері — сильний вітер"
            else:
                wind_info = "💨 Вночі — сильний вітер"
        else:
            wind_info = ""

        forecast_text += (
            f"<b>{day_str}</b>\n"
            f"{temp_info}\n"
            f"{rain_info}\n"
            f"{wind_info}\n\n"
        )

    return forecast_text.strip()

# Асинхронний відправник
async def send_forecast_async(chat_id: int, text: str):
    await bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML)

@app.route("/", methods=["GET"])
def index():
    return "Бот працює!"

@app.route("/", methods=["POST"])
def webhook():
    update = request.get_json()
    print("🔔 Отримано POST-запит:", update)

    if "message" in update and "text" in update["message"]:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"]["text"].lower()

        if text in ["/start", "/weather", "погода"]:
            forecast = get_weather_forecast()
            # ❗ ВАЖЛИВО: використовуємо asyncio.run для запуску async-функції у Flask
            asyncio.run(send_forecast_async(chat_id, forecast))

    return "ok"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
