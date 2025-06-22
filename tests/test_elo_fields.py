#!/usr/bin/env python3
"""
Тест для проверки доступных полей ELO в FACEIT API
"""

import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_clients.fast_api_client_httpx import FastFaceitClientHttpx

# Загружаем переменные окружения
load_dotenv()

async def test_elo_fields(steam_id: str):
    """Тестирует доступные поля ELO в API"""
    api_key = os.getenv("FACEIT_API_KEY")
    if not api_key:
        print("FACEIT_API_KEY not found")
        return
    
    print(f"Testing ELO fields for Steam ID: {steam_id}")
    print("=" * 60)
    
    try:
        async with FastFaceitClientHttpx(api_key) as client:
            # Получаем основную информацию об игроке
            player_data = await client.get_player_by_steam_id(steam_id)
            if not player_data:
                print("Player not found")
                return
            
            player_id = player_data.get("player_id")
            if not player_id:
                print("Player ID not found")
                return
            
            print("🔍 Player Data Fields:")
            print(f"Available fields: {list(player_data.keys())}")
            
            # Проверяем games/cs2
            if "games" in player_data and "cs2" in player_data["games"]:
                cs2_data = player_data["games"]["cs2"]
                print(f"\n🎮 CS2 Game Data:")
                print(f"Available CS2 fields: {list(cs2_data.keys())}")
                print(f"CS2 data: {json.dumps(cs2_data, indent=2)}")
            
            # Проверяем games/csgo
            if "games" in player_data and "csgo" in player_data["games"]:
                csgo_data = player_data["games"]["csgo"]
                print(f"\n🎮 CSGO Game Data:")
                print(f"Available CSGO fields: {list(csgo_data.keys())}")
                print(f"CSGO data: {json.dumps(csgo_data, indent=2)}")
            
            # Получаем статистику
            stats = await client.get_player_stats(player_id)
            if stats:
                print(f"\n📊 Stats Data:")
                print(f"Available stats fields: {list(stats.keys())}")
                
                if "lifetime" in stats:
                    lifetime = stats["lifetime"]
                    print(f"\n📈 Lifetime Stats:")
                    print(f"Available lifetime fields: {list(lifetime.keys())}")
                    
                    # Ищем все поля, связанные с ELO
                    elo_fields = [field for field in lifetime.keys() if 'elo' in field.lower() or 'peak' in field.lower() or 'max' in field.lower()]
                    if elo_fields:
                        print(f"\n🎯 ELO-related fields found: {elo_fields}")
                        for field in elo_fields:
                            print(f"  {field}: {lifetime[field]}")
                    else:
                        print("\n❌ No ELO-related fields found in lifetime stats")
                    
                    # Показываем все числовые поля
                    numeric_fields = []
                    for field, value in lifetime.items():
                        if isinstance(value, (int, float)) and value > 0:
                            numeric_fields.append((field, value))
                    
                    if numeric_fields:
                        print(f"\n📊 All numeric fields:")
                        for field, value in sorted(numeric_fields, key=lambda x: x[1], reverse=True):
                            print(f"  {field}: {value}")
                else:
                    print("❌ No lifetime stats found")
            else:
                print("❌ No stats data found")
            
            # Проверяем другие возможные места для ELO
            print(f"\n🔍 Other possible ELO fields in player_data:")
            for key, value in player_data.items():
                if isinstance(value, (int, float)) and value > 1000:  # ELO обычно > 1000
                    print(f"  {key}: {value}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Тестируем с известным игроком
    steam_id = "76561198376323869"  # Swisstec
    asyncio.run(test_elo_fields(steam_id)) 