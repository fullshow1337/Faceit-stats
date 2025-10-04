#!/usr/bin/env python3
"""
Тест производительности для сравнения старого и нового API клиентов
"""

import asyncio
import time
import httpx
import os
import sys
from dotenv import load_dotenv
from api_clients.fast_api_client_httpx import FastFaceitClientHttpx

# Загружаем переменные окружения
load_dotenv()

async def test_fast_client():
    """Тестирует быстрый клиент"""
    api_key = os.getenv("FACEIT_API_KEY")
    if not api_key:
        print("FACEIT_API_KEY not found")
        return
    
    # Тестовый Steam ID
    steam_id = "76561198003886164"  # iAmBeMaX4 (игрок с баном)
    
    print("Testing Fast Client...")
    start_time = time.time()
    
    try:
        async with FastFaceitClientHttpx(api_key) as client:
            result = await client.get_complete_player_data(steam_id)
            
            if result:
                print(f"✅ Success! Processing time: {result.get('processing_time', 0):.2f} seconds")
                print(f"Player: {result.get('nickname')}")
                print(f"ELO: {result.get('faceit', {}).get('elo')}")
                print(f"Level: {result.get('faceit', {}).get('level')}")
                print(f"Matches in history: {len(result.get('match_history', []))}")
                print(f"Bans: {len(result.get('bans', []))}")
                
                # Выводим статистику
                stats = result.get('stats', {})
                if stats:
                    print("\n📊 Player Statistics:")
                    print(f"  Win Rate: {stats.get('win_rate_percent', 'N/A')}%")
                    print(f"  Headshot %: {stats.get('headshot_percent', 'N/A')}%")
                    print(f"  ADR: {stats.get('adr', 'N/A')}")
                    print(f"  K/D Ratio: {stats.get('kd_ratio', 'N/A')}")
                    print(f"  Total Matches: {stats.get('matches', 'N/A')}")
                    print(f"  Wins: {stats.get('wins', 'N/A')}")
                    print(f"  Average Kills: {stats.get('average_kills', 'N/A')}")
                    print(f"  Average Deaths: {stats.get('average_deaths', 'N/A')}")
                    print(f"  Average Assists: {stats.get('average_assists', 'N/A')}")
                
                # Выводим историю матчей
                match_history = result.get('match_history', [])
                if match_history:
                    print(f"\n🎮 Recent Matches ({len(match_history)}):")
                    for i, match in enumerate(match_history):  # Показываем все матчи
                        print(f"  {i+1}. {match.get('result', 'Unknown')} - {match.get('map', 'Unknown')} - K/D/A: {match.get('kills', 0)}/{match.get('deaths', 0)}/{match.get('assists', 0)}")
                
                # Выводим баны
                bans = result.get('bans', [])
                if bans:
                    print(f"\n🚫 Active Bans ({len(bans)}):")
                    for i, ban in enumerate(bans, 1):
                        print(f"  Ban #{i}:")
                        print(f"    Type: {ban.get('type', 'Unknown')}")
                        print(f"    Reason: {ban.get('reason', 'Unknown')}")
                        
                        # Показываем даты если есть
                        if ban.get('starts_at'):
                            try:
                                from datetime import datetime
                                starts_at = datetime.fromisoformat(ban['starts_at'].replace('Z', '+00:00'))
                                print(f"    Starts: {starts_at.strftime('%d.%m.%Y %H:%M')}")
                            except:
                                print(f"    Starts: {ban.get('starts_at', 'Unknown')}")
                        
                        if ban.get('ends_at'):
                            try:
                                from datetime import datetime
                                ends_at = datetime.fromisoformat(ban['ends_at'].replace('Z', '+00:00'))
                                print(f"    Ends: {ends_at.strftime('%d.%m.%Y %H:%M')}")
                            except:
                                print(f"    Ends: {ban.get('ends_at', 'Unknown')}")
                        else:
                            print(f"    Status: Permanent ban")
                else:
                    print("\n✅ No active bans")
                
            else:
                print("❌ No result returned")
                
    except Exception as e:
        print(f"❌ Error: {e}")
    
    total_time = time.time() - start_time
    print(f"\n⏱️ Total test time: {total_time:.2f} seconds")

async def test_direct_api_calls():
    """Тестирует прямые API вызовы"""
    api_key = os.getenv("FACEIT_API_KEY")
    if not api_key:
        print("FACEIT_API_KEY not found")
        return
    
    steam_id = "76561198003886164"  # iAmBeMaX4 (игрок с баном)
    
    print("\nTesting Direct API Calls...")
    start_time = time.time()
    
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        async with httpx.AsyncClient() as client:
            # Получаем информацию об игроке
            player_url = f"https://open.faceit.com/data/v4/players?game=cs2&game_player_id={steam_id}"
            player_response = await client.get(player_url, headers=headers)
            
            if player_response.status_code == 200:
                player_data = player_response.json()
                player_id = player_data.get("player_id")
                
                print(f"✅ Player found: {player_data.get('nickname')}")
                
                # Параллельно получаем статистику и матчи
                stats_url = f"https://open.faceit.com/data/v4/players/{player_id}/stats/cs2"
                matches_url = f"https://open.faceit.com/data/v4/players/{player_id}/history?game=cs2&offset=0&limit=5"
                
                stats_response, matches_response = await asyncio.gather(
                    client.get(stats_url, headers=headers),
                    client.get(matches_url, headers=headers)
                )
                
                if stats_response.status_code == 200:
                    stats = stats_response.json()
                    print(f"✅ Stats retrieved")
                
                if matches_response.status_code == 200:
                    matches = matches_response.json()
                    print(f"✅ Matches retrieved: {len(matches.get('items', []))}")
                
            else:
                print(f"❌ Player not found: {player_response.status_code}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
    
    total_time = time.time() - start_time
    print(f"Total test time: {total_time:.2f} seconds")

if __name__ == "__main__":
    print("Performance Test for FACEIT API")
    print("=" * 40)
    
    # Запускаем тесты
    asyncio.run(test_fast_client())
    asyncio.run(test_direct_api_calls())
    
    print("\n" + "=" * 40)
    print("Test completed!") 