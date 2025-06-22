#!/usr/bin/env python3
"""
Тест для проверки расчета Avg. Kills по 30 матчам (но отображение только 5 матчей в истории)
"""

import asyncio
import os
import sys
from api_clients.fast_api_client_httpx import FastFaceitClientHttpx

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_30_matches_calculation():
    """Тестирует расчет статистики по 30 матчам, но отображение только 5 в истории"""
    
    # Получаем API ключ из переменной окружения
    api_key = os.getenv("FACEIT_API_KEY")
    if not api_key:
        print("❌ Ошибка: FACEIT_API_KEY не найден в переменных окружения")
        return
    
    # Steam ID для тестирования (можно заменить на любой другой)
    steam_id = "76561198000000000"  # Замените на реальный Steam ID
    
    print(f"🔍 Тестируем расчет Avg. Kills по 30 матчам для Steam ID: {steam_id}")
    print("📋 Match History будет показывать только 5 последних матчей")
    print("=" * 70)
    
    async with FastFaceitClientHttpx(api_key) as client:
        try:
            # Получаем данные игрока
            print("📡 Получаем данные игрока...")
            player_data = await client.get_complete_player_data(steam_id)
            
            if not player_data:
                print("❌ Не удалось получить данные игрока")
                return
            
            print(f"✅ Данные получены за {player_data['processing_time']:.2f} секунд")
            print()
            
            # Выводим основную информацию
            print(f"👤 Игрок: {player_data['nickname']}")
            print(f"🎮 Steam ID: {player_data['steam']['id_64']}")
            print(f"🏆 FACEIT ELO: {player_data['faceit']['elo']}")
            print(f"📊 Уровень: {player_data['faceit']['level']}")
            print()
            
            # Выводим статистику
            stats = player_data['stats']
            print("📈 СТАТИСТИКА (рассчитана по 30 последним матчам):")
            print(f"   • Avg. Kills: {stats.get('average_kills', 'N/A')}")
            print(f"   • Avg. Deaths: {stats.get('average_deaths', 'N/A')}")
            print(f"   • Avg. Assists: {stats.get('average_assists', 'N/A')}")
            print(f"   • Last 30 Matches Avg Kills: {stats.get('last_30_matches_avg_kills', 'N/A')}")
            print(f"   • Win Rate: {stats.get('win_rate_percent', 'N/A')}%")
            print(f"   • ADR: {stats.get('adr', 'N/A')}")
            print(f"   • K/D Ratio: {stats.get('kd_ratio', 'N/A')}")
            print()
            
            # Выводим информацию о матчах (только 5 отображаемых)
            match_history = player_data['match_history']
            print(f"🎯 MATCH HISTORY (отображается только {len(match_history)} последних матчей):")
            
            if match_history:
                # Показываем детали каждого матча
                print("📋 Последние матчи:")
                for i, match in enumerate(match_history):
                    print(f"   {i+1}. {match['map']} | {match['kills']}/{match['deaths']}/{match['assists']} | {match['result']} | {match['mode']}")
                
                # Показываем статистику по отображаемым матчам
                total_kills = sum(match.get('kills', 0) for match in match_history)
                total_deaths = sum(match.get('deaths', 0) for match in match_history)
                total_assists = sum(match.get('assists', 0) for match in match_history)
                
                print()
                print(f"📊 Статистика по отображаемым {len(match_history)} матчам:")
                print(f"   • Всего убийств: {total_kills}")
                print(f"   • Всего смертей: {total_deaths}")
                print(f"   • Всего ассистов: {total_assists}")
                print(f"   • Среднее убийств: {total_kills / len(match_history):.1f}")
                print(f"   • Среднее смертей: {total_deaths / len(match_history):.1f}")
                print(f"   • Среднее ассистов: {total_assists / len(match_history):.1f}")
                
                print()
                print("💡 Примечание: Avg. Kills в статистике выше рассчитан по 30 матчам,")
                print("   но в Match History показаны только последние 5 матчей для удобства просмотра.")
            else:
                print("   ❌ Нет данных о матчах")
            
            print()
            print("✅ Тест завершен успешно!")
            
        except Exception as e:
            print(f"❌ Ошибка при выполнении теста: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_30_matches_calculation()) 