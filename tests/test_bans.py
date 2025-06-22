#!/usr/bin/env python3
"""
Тест для проверки работы с банами игроков
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from api_clients.fast_api_client_httpx import FastFaceitClientHttpx

# Загружаем переменные окружения
load_dotenv()

async def test_bans_for_player(steam_id: str):
    """Тестирует получение банов для конкретного игрока"""
    api_key = os.getenv("FACEIT_API_KEY")
    if not api_key:
        print("FACEIT_API_KEY not found")
        return
    
    print(f"Testing bans for Steam ID: {steam_id}")
    print("=" * 50)
    
    try:
        async with FastFaceitClientHttpx(api_key) as client:
            # Получаем полную информацию об игроке
            result = await client.get_complete_player_data(steam_id)
            
            if result:
                print(f"✅ Player found: {result.get('nickname')}")
                print(f"Player ID: {result.get('player_id')}")
                
                # Проверяем обработанные баны
                bans = result.get('bans', [])
                print(f"\n🚫 Processed bans found: {len(bans)}")
                
                if bans:
                    print("\n📋 Processed Ban Details:")
                    for i, ban in enumerate(bans, 1):
                        print(f"\n  Ban #{i}:")
                        print(f"    Reason: {ban.get('reason', 'Unknown')}")
                        print(f"    Start Date: {ban.get('start_date', 'Unknown')}")
                        print(f"    End Date: {ban.get('end_date', 'Unknown')}")
                else:
                    print("✅ No active bans found")
                
                # Также тестируем прямой запрос к API банов для сравнения
                print(f"\n🔍 Testing direct bans API call for comparison...")
                player_id = result.get('player_id')
                if player_id:
                    direct_bans = await client.get_player_bans(player_id)
                    print(f"Direct API call returned {len(direct_bans)} raw bans")
                    
                    if direct_bans:
                        print("Raw ban data from API:")
                        for i, ban in enumerate(direct_bans[:2], 1):  # Показываем только первые 2
                            print(f"  Raw Ban {i}: {ban}")
                
            else:
                print("❌ Player not found")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

async def test_multiple_players():
    """Тестирует несколько игроков для поиска банов"""
    # Список Steam ID для тестирования
    test_steam_ids = [
        "76561199566504859",  # fullshow- (текущий тестовый игрок)
        # Добавьте другие Steam ID для тестирования
    ]
    
    print("Testing multiple players for bans...")
    print("=" * 50)
    
    for steam_id in test_steam_ids:
        await test_bans_for_player(steam_id)
        print("\n" + "=" * 50)

if __name__ == "__main__":
    print("Ban Testing for FACEIT API")
    print("=" * 50)
    
    # Тестируем текущего игрока
    asyncio.run(test_bans_for_player("76561199566504859"))
    
    # Если хотите протестировать других игроков, раскомментируйте:
    # asyncio.run(test_multiple_players()) 