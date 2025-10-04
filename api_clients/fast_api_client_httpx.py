import httpx
import asyncio
import json
import time
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime
 

# Отключаем DEBUG логирование для HTTP клиентов
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

class FastFaceitClientHttpx:
    """Быстрый клиент для прямых запросов к FACEIT API с использованием httpx"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://open.faceit.com/data/v4"
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self.client = None
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            headers=self.headers,
            timeout=httpx.Timeout(10.0)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    async def check_image_availability(self, image_url: str) -> bool:
        """Проверяет доступность изображения по URL"""
        if not image_url:
            return False
        
        try:
            # Делаем HEAD запрос для проверки доступности изображения
            response = await self.client.head(image_url, timeout=5.0)
            
            # Проверяем статус код и content-type
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                if content_type.startswith('image/'):
                    logger.debug(f"Image is available: {image_url}")
                    return True
                else:
                    logger.warning(f"URL is not an image (content-type: {content_type}): {image_url}")
                    return False
            else:
                logger.warning(f"Image not available (status: {response.status_code}): {image_url}")
                return False
                
        except Exception as e:
            logger.warning(f"Error checking image availability: {e} for URL: {image_url}")
            return False
    
    async def get_player_by_steam_id(self, steam_id: str) -> Optional[Dict]:
        """Получает информацию об игроке по Steam ID"""
        try:
            # Правильный URL для поиска игрока по Steam ID
            url = f"{self.base_url}/players?game=cs2&game_player_id={steam_id}"
            logger.debug(f"Requesting player data from: {url}")
            
            response = await self.client.get(url, headers=self.headers)
            
            if response is None:
                logger.error("Response is None")
                return None
                
            logger.debug(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"Player data received: {data}")
                
                # API возвращает объект напрямую
                if isinstance(data, dict) and data.get("player_id"):
                    return data
                
                logger.warning("No player found in response")
                return None
            elif response.status_code == 404:
                logger.warning(f"Player not found for Steam ID: {steam_id}")
                return None
            else:
                logger.error(f"Error getting player: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Exception getting player: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def get_player_stats(self, player_id: str) -> Optional[Dict]:
        """Получает статистику игрока"""
        url = f"{self.base_url}/players/{player_id}/stats/cs2"
        
        try:
            response = await self.client.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error getting stats: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Exception getting stats: {e}")
            return None
    
    async def get_player_matches(self, player_id: str, limit: int = 30) -> List[Dict]:
        """Получает последние матчи игрока"""
        url = f"{self.base_url}/players/{player_id}/history?game=cs2&offset=0&limit={limit}"
        
        try:
            response = await self.client.get(url)
            if response.status_code == 200:
                data = response.json()
                return data.get("items", [])
            else:
                logger.error(f"Error getting matches: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Exception getting matches: {e}")
            return []
    
    async def get_match_details(self, match_id: str) -> Optional[Dict]:
        """Получает детали матча"""
        url = f"{self.base_url}/matches/{match_id}"
        
        try:
            response = await self.client.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error getting match details: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Exception getting match details: {e}")
            return None
    
    async def get_match_stats(self, match_id: str) -> Optional[Dict]:
        """Получает статистику матча"""
        url = f"{self.base_url}/matches/{match_id}/stats"
        
        try:
            response = await self.client.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error getting match stats: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Exception getting match stats: {e}")
            return None
    
    async def get_player_bans(self, player_id: str) -> List[Dict]:
        """Получает баны игрока"""
        try:
            url = f"{self.base_url}/players/{player_id}/bans"
            response = await self.client.get(url, headers=self.headers)
            response.raise_for_status()
            
            bans_data = response.json()
            logger.debug(f"Raw bans data for player {player_id}: {bans_data}")
            
            # Проверяем структуру ответа
            if isinstance(bans_data, dict):
                bans = bans_data.get("items", [])
            elif isinstance(bans_data, list):
                bans = bans_data
            else:
                bans = []
            
            logger.info(f"Found {len(bans)} bans for player {player_id}")
            return bans
            
        except Exception as e:
            logger.error(f"Error fetching bans for player {player_id}: {e}")
            return []
    
    async def get_complete_player_data(self, steam_id: str) -> Optional[Dict]:
        """Получает полную информацию об игроке за один раз"""
        start_time = time.time()
        
        # Получаем основную информацию об игроке
        player_data = await self.get_player_by_steam_id(steam_id)
        if not player_data:
            return None
        
        player_id = player_data.get("player_id")
        if not player_id:
            return None
        
        # Параллельно получаем все данные
        tasks = [
            self.get_player_stats(player_id),
            self.get_player_matches(player_id, 30),  # Получаем 30 матчей для расчета статистики
            self.get_player_bans(player_id)
        ]
        
        stats, matches, bans = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обрабатываем исключения
        if isinstance(stats, Exception):
            logger.error(f"Error getting stats: {stats}")
            stats = None
        if isinstance(matches, Exception):
            logger.error(f"Error getting matches: {matches}")
            matches = []
        if isinstance(bans, Exception):
            logger.error(f"Error getting bans: {bans}")
            bans = []
        
        # Получаем детали матчей параллельно (все 30 для расчета статистики)
        match_details_tasks = []
        match_stats_tasks = []
        
        for match in matches[:30]:  # Берем первые 30 матчей для расчета статистики
            match_id = match.get("match_id")
            if match_id:
                match_details_tasks.append(self.get_match_details(match_id))
                match_stats_tasks.append(self.get_match_stats(match_id))
        
        # Выполняем запросы параллельно
        match_details_results = await asyncio.gather(*match_details_tasks, return_exceptions=True)
        match_stats_results = await asyncio.gather(*match_stats_tasks, return_exceptions=True)
        
        # Обрабатываем результаты матчей (все 30 для расчета статистики)
        processed_matches = []
        logger.info(f"Processing {len(matches)} matches for player {player_data.get('nickname')}")
        
        for i, match in enumerate(matches[:30]):
            if i < len(match_details_results) and i < len(match_stats_results):
                details = match_details_results[i] if not isinstance(match_details_results[i], Exception) else None
                stats_data = match_stats_results[i] if not isinstance(match_stats_results[i], Exception) else None
                
                if details and stats_data:
                    processed_matches.append({
                        "match_id": match.get("match_id"),
                        "date": details.get("started_at"),
                        
                        "result": self._determine_match_result(details, stats_data, player_id),
                        "score": self._get_match_score(stats_data),
                        "map": self._get_match_map(stats_data),
                        "mode": self._get_match_mode(stats_data),
                        "kills": self._safe_int(self._get_player_kills(stats_data, player_id)),
                        "deaths": self._safe_int(self._get_player_deaths(stats_data, player_id)),
                        "assists": self._safe_int(self._get_player_assists(stats_data, player_id)),
                        "match_url": f"https://www.faceit.com/en/cs2/room/{match.get('match_id')}"
                    })
                else:
                    logger.debug(f"Failed to process match {i+1}: details={details is not None}, stats={stats_data is not None}")
            else:
                logger.debug(f"Index out of range for match {i+1}")
        
        logger.info(f"Successfully processed {len(processed_matches)} matches out of {len(matches[:30])}")
        
        # Проверяем доступность баннера
        banner_url = player_data.get("cover_image")
        valid_banner = None
        if banner_url:
            is_banner_available = await self.check_image_availability(banner_url)
            if is_banner_available:
                valid_banner = banner_url
                logger.info(f"Banner is available for player {player_data.get('nickname')}: {banner_url}")
            else:
                logger.warning(f"Banner is not available for player {player_data.get('nickname')}: {banner_url}")
        
        # Формируем финальный ответ в старом формате для совместимости
        result = {
            "player_id": player_id,
            "nickname": player_data.get("nickname"),
            "avatar": player_data.get("avatar"),
            "banner": valid_banner,  # Добавляем только доступный banner или None
            "country": player_data.get("country"),
            "steam": {
                "nickname": player_data.get("steam_nickname"),  # Добавляем steam nickname
                "id_64": steam_id,
                "profile_url": f"https://steamcommunity.com/profiles/{steam_id}"
            },
            "faceit": {
                "url": f"https://www.faceit.com/ru/players/{player_data.get('nickname')}",
                "elo": self._safe_int(self._get_elo_from_stats(stats) or self._get_elo_from_player_data(player_data)),
                "level": self._safe_int(self._get_level_from_stats(stats) or self._get_level_from_player_data(player_data)),
                "csgo_elo": self._safe_int(self._get_csgo_elo_from_player_data(player_data))  # Добавляем CSGO ELO
            },
            "stats": self._process_stats(stats),
            "match_history": processed_matches[:5],  # Показываем только первые 5 матчей в истории
            "bans": self._process_bans(bans),
            "games": player_data.get("games", {}),  # Добавляем games для совместимости
            "processing_time": time.time() - start_time
        }
        
        # Если некоторые статистики не найдены, попробуем вычислить их из истории матчей (по 30 последним матчам)
        if result["stats"].get("average_kills") is None and processed_matches:
            total_kills = sum(match.get("kills", 0) for match in processed_matches)
            result["stats"]["average_kills"] = int(round(total_kills / len(processed_matches)))
            logger.info(f"Computed average_kills from last {len(processed_matches)} matches: {result['stats']['average_kills']}")
        elif result["stats"].get("average_kills") is not None:
            # Округляем значение из API
            result["stats"]["average_kills"] = int(round(float(result["stats"]["average_kills"])))
        
        if result["stats"].get("average_deaths") is None and processed_matches:
            total_deaths = sum(match.get("deaths", 0) for match in processed_matches)
            result["stats"]["average_deaths"] = int(round(total_deaths / len(processed_matches)))
            logger.info(f"Computed average_deaths from last {len(processed_matches)} matches: {result['stats']['average_deaths']}")
        elif result["stats"].get("average_deaths") is not None:
            # Округляем значение из API
            result["stats"]["average_deaths"] = int(round(float(result["stats"]["average_deaths"])))
        
        if result["stats"].get("average_assists") is None and processed_matches:
            total_assists = sum(match.get("assists", 0) for match in processed_matches)
            result["stats"]["average_assists"] = int(round(total_assists / len(processed_matches)))
            logger.info(f"Computed average_assists from last {len(processed_matches)} matches: {result['stats']['average_assists']}")
        elif result["stats"].get("average_assists") is not None:
            # Округляем значение из API
            result["stats"]["average_assists"] = int(round(float(result["stats"]["average_assists"])))
        
        # Добавляем last_30_matches_avg_kills для совместимости (рассчитывается по 30 матчам, но отображается только 5)
        if result["stats"].get("average_kills") is not None:
            result["stats"]["last_30_matches_avg_kills"] = result["stats"]["average_kills"]
        else:
            result["stats"]["last_30_matches_avg_kills"] = 0
        
        # Добавляем recent_results для совместимости
        result["stats"]["recent_results"] = []
        
        # Безопасное преобразование всех числовых значений для фронтенда
        def safe_float(value):
            try:
                return float(value) if value is not None else 0.0
            except (ValueError, TypeError):
                return 0.0

        def safe_int(value):
            try:
                return int(value) if value is not None else 0
            except (ValueError, TypeError):
                return 0
        
        # Преобразуем все числовые поля
        stats = result["stats"]
        stats["win_rate_percent"] = safe_float(stats.get("win_rate_percent"))
        stats["headshot_percent"] = safe_float(stats.get("headshot_percent"))
        stats["adr"] = safe_float(stats.get("adr"))
        stats["kd_ratio"] = safe_float(stats.get("kd_ratio"))
        stats["matches"] = safe_int(stats.get("matches"))
        stats["wins"] = safe_int(stats.get("wins"))
        stats["longest_win_streak"] = safe_int(stats.get("longest_win_streak"))
        stats["current_win_streak"] = safe_int(stats.get("current_win_streak"))
        stats["average_kills"] = safe_int(stats.get("average_kills"))
        stats["average_deaths"] = safe_int(stats.get("average_deaths"))
        stats["average_assists"] = safe_int(stats.get("average_assists"))
        stats["average_mvps"] = safe_int(stats.get("average_mvps"))
        stats["last_30_matches_avg_kills"] = safe_int(stats.get("last_30_matches_avg_kills"))
        
        logger.info(f"Complete player data retrieved in {result['processing_time']:.2f} seconds")
        return result
    

    def _determine_match_result(self, match_details: Dict, stats_data: Optional[Dict], player_id: str) -> str:
        """Определяет результат матча для игрока"""
        try:
            if not match_details:
                return "Unknown"

            # Попробуем использовать явного победителя матча
            results_block = match_details.get("results", {}) if isinstance(match_details.get("results"), dict) else {}
            winner_team_id = results_block.get("winner") or results_block.get("winner_id") or results_block.get("winner_faction")

            # Найдем к какой команде относится игрок
            player_team_id = None
            player_faction_key = None
            teams_block = match_details.get("teams")
            iterable_teams = teams_block.values() if isinstance(teams_block, dict) else (teams_block or [])
            for team in iterable_teams:
                # team может быть dict со структурой {team_id, players: [{player_id: ...}]}
                team_id = team.get("team_id") or team.get("faction_id") or team.get("id")
                team_players = (team.get("players") or []) + (team.get("roster") or [])
                for p in team_players:
                    if str(p.get("player_id")) == str(player_id):
                        player_team_id = team_id
                        # Если teams представлен как dict, попробуем запомнить ключ фракции
                        if isinstance(teams_block, dict):
                            for key, t in teams_block.items():
                                if t is team:
                                    player_faction_key = key  # faction1/faction2
                                    break
                        break
                if player_team_id:
                    break

            # Сопоставляем победителя
            if winner_team_id:
                # Если победитель указан как faction1/faction2, сравним по ключу фракции
                if str(winner_team_id) in ("faction1", "faction2", "team1", "team2"):
                    if player_faction_key and str(player_faction_key) == str(winner_team_id):
                        return "Win"
                    elif player_faction_key:
                        return "Lose"
                # Иначе сравним по team_id
                if player_team_id and str(winner_team_id) == str(player_team_id):
                    return "Win"
                if player_team_id:
                    return "Lose"

            # Фоллбек: сравниваем раунды по score и принадлежность игрока к команде A/B
            try:
                # Получаем строку счета, стараясь учесть разные форматы
                results = match_details.get("results", {}) if isinstance(match_details.get("results"), dict) else {}
                score_str = results.get("score") or results.get("score_str")
                if not score_str and stats_data:
                    score_str = self._get_match_score(stats_data)

                # Нормализуем разделитель
                if isinstance(score_str, str):
                    score_norm = (
                        score_str.replace(" ", "")
                        .replace("-", "/")
                        .replace(":", "/")
                    )
                else:
                    score_norm = None

                # Часто score приходит как "16/14" или "13/11"
                if isinstance(score_norm, str) and "/" in score_norm:
                    left, right = score_norm.split("/", 1)
                    left_val = int(str(left).strip())
                    right_val = int(str(right).strip())

                    player_faction = None
                    team_index = None

                    # 1) Через factions/teams в match_details (dict)
                    factions = match_details.get("factions") or (match_details.get("teams") if isinstance(match_details.get("teams"), dict) else None)
                    if isinstance(factions, dict) and player_faction is None and team_index is None:
                        for key, team in factions.items():
                            team_players = (team.get("players") or []) + (team.get("roster") or [])
                            for p in team_players:
                                if str(p.get("player_id")) == str(player_id):
                                    player_faction = key
                                    if key in ("faction1", "team1", "1", 1, "left"):
                                        team_index = 0
                                    elif key in ("faction2", "team2", "2", 2, "right"):
                                        team_index = 1
                                    break
                            if player_faction is not None:
                                break

                    # 2) Через teams в match_details (list)
                    if team_index is None and isinstance(match_details.get("teams"), list):
                        for idx, t in enumerate(match_details.get("teams") or []):
                            team_players = (t.get("players") or []) + (t.get("roster") or [])
                            for p in team_players:
                                if str(p.get("player_id")) == str(player_id):
                                    team_index = idx
                                    break
                            if team_index is not None:
                                break

                    # 3) Через все rounds[*].teams в stats_data (list или dict)
                    if team_index is None and stats_data and isinstance(stats_data.get("rounds"), list):
                        for r in stats_data.get("rounds") or []:
                            rnd_teams = r.get("teams")
                            if isinstance(rnd_teams, list):
                                for idx, t in enumerate(rnd_teams):
                                    for p in t.get("players", []):
                                        if str(p.get("player_id")) == str(player_id):
                                            team_index = idx
                                            break
                                    if team_index is not None:
                                        break
                            elif isinstance(rnd_teams, dict):
                                for key, t in rnd_teams.items():
                                    for p in t.get("players", []):
                                        if str(p.get("player_id")) == str(player_id):
                                            player_faction = key
                                            if key in ("faction1", "team1", "1", 1, "left"):
                                                team_index = 0
                                            elif key in ("faction2", "team2", "2", 2, "right"):
                                                team_index = 1
                                            break
                                    if team_index is not None:
                                        break
                            if team_index is not None:
                                break

                    # Если игрок в левой команде — оцениваем левый счет, иначе правый
                    if player_faction in ("faction1", "team1", "1", 1, "left") or team_index == 0:
                        if left_val > right_val:
                            return "Win"
                        elif left_val < right_val:
                            return "Lose"
                        else:
                            return "Draw"
                    elif player_faction in ("faction2", "team2", "2", 2, "right") or team_index == 1:
                        if right_val > left_val:
                            return "Win"
                        elif right_val < left_val:
                            return "Lose"
                        else:
                            return "Draw"
                    # Если не удалось определить фракцию игрока — просто сравним стороны как Unknown
                    if left_val == right_val:
                        return "Draw"
                    # Без знания стороны определить нельзя корректно
                    return "Unknown"
            except Exception:
                pass

            return "Unknown"
        except Exception:
            return "Unknown"
    
    def _get_match_score(self, stats_data: Dict) -> str:
        """Получает счет матча"""
        if stats_data and "rounds" in stats_data:
            first_round = stats_data["rounds"][0] if stats_data["rounds"] else {}
            return first_round.get("round_stats", {}).get("Score", "0-0")
        return "0-0"
    
    def _get_match_map(self, stats_data: Dict) -> str:
        """Получает карту матча"""
        if stats_data and "rounds" in stats_data:
            first_round = stats_data["rounds"][0] if stats_data["rounds"] else {}
            return first_round.get("round_stats", {}).get("Map", "Unknown")
        return "Unknown"
    
    def _get_match_mode(self, stats_data: Dict) -> str:
        """Получает режим матча"""
        if stats_data and "rounds" in stats_data:
            first_round = stats_data["rounds"][0] if stats_data["rounds"] else {}
            game_mode = first_round.get("game_mode", "Unknown")
            
            # Преобразуем в читаемый формат
            if game_mode == "5v5":
                return "Competitive"
            elif game_mode == "2v2":
                return "Wingman"
            else:
                return game_mode
        return "Unknown"
    
    def _get_player_kills(self, stats_data: Dict, player_id: str) -> int:
        """Получает количество убийств игрока"""
        if stats_data and "rounds" in stats_data:
            for round_data in stats_data["rounds"]:
                for team in round_data.get("teams", []):
                    for player in team.get("players", []):
                        if str(player.get("player_id")) == str(player_id):
                            return int(player.get("player_stats", {}).get("Kills", 0))
        return 0
    
    def _get_player_deaths(self, stats_data: Dict, player_id: str) -> int:
        """Получает количество смертей игрока"""
        if stats_data and "rounds" in stats_data:
            for round_data in stats_data["rounds"]:
                for team in round_data.get("teams", []):
                    for player in team.get("players", []):
                        if str(player.get("player_id")) == str(player_id):
                            return int(player.get("player_stats", {}).get("Deaths", 0))
        return 0
    
    def _get_player_assists(self, stats_data: Dict, player_id: str) -> int:
        """Получает количество ассистов игрока"""
        if stats_data and "rounds" in stats_data:
            for round_data in stats_data["rounds"]:
                for team in round_data.get("teams", []):
                    for player in team.get("players", []):
                        if str(player.get("player_id")) == str(player_id):
                            return int(player.get("player_stats", {}).get("Assists", 0))
        return 0
    
    def _get_elo_from_player_data(self, player_data: Dict) -> Optional[int]:
        """Получает CS2 ELO из основной информации об игроке"""
        # Пробуем получить из games/cs2
        if "games" in player_data:
            cs2_data = player_data["games"].get("cs2", {})
            elo = cs2_data.get("faceit_elo")
            if elo is None:
                elo = cs2_data.get("elo")
            if elo is not None:
                logger.debug(f"Found CS2 ELO in games/cs2: {elo}")
                return elo
        
        # Пробуем другие поля
        elo = player_data.get("faceit_elo")
        if elo is None:
            elo = player_data.get("elo")
        if elo is not None:
            logger.debug(f"Found CS2 ELO in player_data: {elo}")
        return elo
    
    def _get_level_from_player_data(self, player_data: Dict) -> Optional[int]:
        """Получает уровень из основной информации об игроке"""
        # Пробуем получить из games/cs2
        if "games" in player_data:
            cs2_data = player_data["games"].get("cs2", {})
            level = cs2_data.get("skill_level")
            if level is None:
                level = cs2_data.get("level")
            if level is not None:
                logger.debug(f"Found Level in games/cs2: {level}")
                return level
        
        # Пробуем другие поля
        level = player_data.get("skill_level")
        if level is None:
            level = player_data.get("level")
        if level is not None:
            logger.debug(f"Found Level in player_data: {level}")
        return level
    
    def _get_elo_from_stats(self, stats: Dict) -> Optional[int]:
        """Получает ELO из статистики"""
        if stats and "lifetime" in stats:
            # Пробуем разные поля для ELO
            elo = stats["lifetime"].get("Current Elo")
            if elo is None:
                elo = stats["lifetime"].get("Elo")
            if elo is None:
                elo = stats["lifetime"].get("faceit_elo")
            if elo is not None:
                logger.debug(f"Found ELO in stats: {elo}")
            return elo
        return None
    
    def _get_level_from_stats(self, stats: Dict) -> Optional[int]:
        """Получает уровень из статистики"""
        if stats and "lifetime" in stats:
            # Пробуем разные поля для уровня
            level = stats["lifetime"].get("Current Level")
            if level is None:
                level = stats["lifetime"].get("Level")
            if level is None:
                level = stats["lifetime"].get("skill_level")
            if level is not None:
                logger.debug(f"Found Level in stats: {level}")
            return level
        return None
    
    def _process_stats(self, stats: Dict) -> Dict:
        """Обрабатывает статистику игрока"""
        if not stats or "lifetime" not in stats:
            return {}
        
        lifetime = stats["lifetime"]
        
        # Отладочная информация - показываем доступные поля
        logger.debug(f"Available lifetime stats fields: {list(lifetime.keys())}")
        
        # Пробуем разные варианты названий полей
        def get_stat_value(field_names, default=None):
            for field_name in field_names:
                value = lifetime.get(field_name)
                if value is not None:
                    logger.debug(f"Found {field_names[0]} as '{field_name}': {value}")
                    return value
            logger.debug(f"Not found any of {field_names}, using default: {default}")
            return default
        
        return {
            "win_rate_percent": get_stat_value(["Win Rate %", "Win Rate", "win_rate"]),
            "headshot_percent": get_stat_value(["Average Headshots %", "Average Headshots", "headshot_percent"]),
            "adr": get_stat_value(["ADR", "Average Damage per Round"]),
            "kd_ratio": get_stat_value(["Average K/D Ratio", "K/D Ratio", "kd_ratio"]),
            "matches": get_stat_value(["Matches", "Total Matches", "matches"]),
            "wins": get_stat_value(["Wins", "Total Wins", "wins"]),
            "longest_win_streak": get_stat_value(["Longest Win Streak", "longest_win_streak"]),
            "current_win_streak": get_stat_value(["Current Win Streak", "current_win_streak"]),
            "average_kills": get_stat_value(["Average Kills", "Kills", "average_kills", "Avg Kills"]),
            "average_deaths": get_stat_value(["Average Deaths", "Deaths", "average_deaths", "Avg Deaths"]),
            "average_assists": get_stat_value(["Average Assists", "Assists", "average_assists", "Avg Assists"]),
            "average_mvps": get_stat_value(["Average MVPs", "MVPs", "average_mvps", "Avg MVPs"])
        }
    
    def _process_bans(self, bans: List[Dict]) -> List[Dict]:
        """Обрабатывает баны игрока - показывает только активные"""
        processed_bans = []
        current_time = datetime.now()
        
        for ban in bans:
            try:
                starts_at = ban.get("starts_at")
                ends_at = ban.get("ends_at")
                
                # Парсим даты
                starts_at_dt = None
                ends_at_dt = None
                
                if starts_at:
                    try:
                        # Обрабатываем разные форматы дат
                        if isinstance(starts_at, str):
                            starts_at_dt = datetime.fromisoformat(starts_at.replace('Z', '+00:00'))
                            # Убираем timezone info для сравнения
                            starts_at_dt = starts_at_dt.replace(tzinfo=None)
                        else:
                            starts_at_dt = datetime.fromtimestamp(starts_at)
                    except Exception as e:
                        logger.warning(f"Failed to parse starts_at: {starts_at}, error: {e}")
                
                if ends_at:
                    try:
                        # Обрабатываем разные форматы дат
                        if isinstance(ends_at, str):
                            ends_at_dt = datetime.fromisoformat(ends_at.replace('Z', '+00:00'))
                            # Убираем timezone info для сравнения
                            ends_at_dt = ends_at_dt.replace(tzinfo=None)
                        else:
                            ends_at_dt = datetime.fromtimestamp(ends_at)
                    except Exception as e:
                        logger.warning(f"Failed to parse ends_at: {ends_at}, error: {e}")
                
                # Проверяем, активен ли бан
                is_active = False
                
                if ends_at_dt:
                    # Бан с датой окончания - проверяем, не истек ли
                    if ends_at_dt > current_time:
                        is_active = True
                else:
                    # Бан без даты окончания = навсегда = активен
                    is_active = True
                
                # Показываем только активные баны
                if is_active:
                    # Форматируем даты
                    formatted_start = None
                    formatted_end = None
                    
                    if starts_at_dt:
                        try:
                            formatted_start = starts_at_dt.strftime("%d.%m.%Y")
                        except Exception as e:
                            logger.warning(f"Failed to format start date: {e}")
                    
                    if ends_at_dt:
                        try:
                            formatted_end = ends_at_dt.strftime("%d.%m.%Y")
                        except Exception as e:
                            logger.warning(f"Failed to format end date: {e}")
                    
                    # Определяем окончание бана
                    end_info = "permanent"
                    if formatted_end:
                        end_info = formatted_end
                    
                    processed_bans.append({
                        "reason": ban.get("reason"),
                        "start_date": formatted_start,
                        "end_date": end_info
                    })
                    
                    logger.info(f"Active ban found: reason={ban.get('reason')}, start={formatted_start}, end={end_info}")
                else:
                    logger.debug(f"Skipping expired ban: reason={ban.get('reason')}")
                
            except Exception as e:
                logger.error(f"Error processing ban {ban}: {e}")
        
        return processed_bans

    def _safe_int(self, value):
        try:
            return int(value) if value is not None else 0
        except (ValueError, TypeError):
            return 0

    def _get_csgo_elo_from_player_data(self, player_data: Dict) -> Optional[int]:
        """Получает CSGO ELO из основной информации об игроке"""
        # Пробуем получить из games/csgo
        if "games" in player_data:
            csgo_data = player_data["games"].get("csgo", {})
            elo = csgo_data.get("faceit_elo")
            if elo is None:
                elo = csgo_data.get("elo")
            if elo is not None:
                logger.debug(f"Found CSGO ELO in games/csgo: {elo}")
                return elo
        
        # Пробуем другие поля
        elo = player_data.get("csgo_faceit_elo")
        if elo is None:
            elo = player_data.get("csgo_elo")
        if elo is not None:
            logger.debug(f"Found CSGO ELO in player_data: {elo}")
        return elo

    def _get_level_from_player_data(self, player_data: Dict) -> Optional[int]:
        """Получает уровень из основной информации об игроке"""
        # Пробуем получить из games/cs2
        if "games" in player_data:
            cs2_data = player_data["games"].get("cs2", {})
            level = cs2_data.get("skill_level")
            if level is None:
                level = cs2_data.get("level")
            if level is not None:
                logger.debug(f"Found Level in games/cs2: {level}")
                return level
        
        # Пробуем другие поля
        level = player_data.get("skill_level")
        if level is None:
            level = player_data.get("level")
        if level is not None:
            logger.debug(f"Found Level in player_data: {level}")
        return level
    
    def _get_elo_from_stats(self, stats: Dict) -> Optional[int]:
        """Получает ELO из статистики"""
        if stats and "lifetime" in stats:
            # Пробуем разные поля для ELO
            elo = stats["lifetime"].get("Current Elo")
            if elo is None:
                elo = stats["lifetime"].get("Elo")
            if elo is None:
                elo = stats["lifetime"].get("faceit_elo")
            if elo is not None:
                logger.debug(f"Found ELO in stats: {elo}")
            return elo
        return None
    
    def _get_level_from_stats(self, stats: Dict) -> Optional[int]:
        """Получает уровень из статистики"""
        if stats and "lifetime" in stats:
            # Пробуем разные поля для уровня
            level = stats["lifetime"].get("Current Level")
            if level is None:
                level = stats["lifetime"].get("Level")
            if level is None:
                level = stats["lifetime"].get("skill_level")
            if level is not None:
                logger.debug(f"Found Level in stats: {level}")
            return level
        return None
    
    def _process_stats(self, stats: Dict) -> Dict:
        """Обрабатывает статистику игрока"""
        if not stats or "lifetime" not in stats:
            return {}
        
        lifetime = stats["lifetime"]
        
        # Отладочная информация - показываем доступные поля
        logger.debug(f"Available lifetime stats fields: {list(lifetime.keys())}")
        
        # Пробуем разные варианты названий полей
        def get_stat_value(field_names, default=None):
            for field_name in field_names:
                value = lifetime.get(field_name)
                if value is not None:
                    logger.debug(f"Found {field_names[0]} as '{field_name}': {value}")
                    return value
            logger.debug(f"Not found any of {field_names}, using default: {default}")
            return default
        
        return {
            "win_rate_percent": get_stat_value(["Win Rate %", "Win Rate", "win_rate"]),
            "headshot_percent": get_stat_value(["Average Headshots %", "Average Headshots", "headshot_percent"]),
            "adr": get_stat_value(["ADR", "Average Damage per Round"]),
            "kd_ratio": get_stat_value(["Average K/D Ratio", "K/D Ratio", "kd_ratio"]),
            "matches": get_stat_value(["Matches", "Total Matches", "matches"]),
            "wins": get_stat_value(["Wins", "Total Wins", "wins"]),
            "longest_win_streak": get_stat_value(["Longest Win Streak", "longest_win_streak"]),
            "current_win_streak": get_stat_value(["Current Win Streak", "current_win_streak"]),
            "average_kills": get_stat_value(["Average Kills", "Kills", "average_kills", "Avg Kills"]),
            "average_deaths": get_stat_value(["Average Deaths", "Deaths", "average_deaths", "Avg Deaths"]),
            "average_assists": get_stat_value(["Average Assists", "Assists", "average_assists", "Avg Assists"]),
            "average_mvps": get_stat_value(["Average MVPs", "MVPs", "average_mvps", "Avg MVPs"])
        } 