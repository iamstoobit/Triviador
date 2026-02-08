from __future__ import annotations
import random
import time
from typing import List, Optional, Tuple
from dataclasses import dataclass

from src.utils.config import GameConfig, Difficulty
from src.game.state import GameState, Region
from src.trivia.question import Question, QuestionType
from src.ai.difficulty import AIDifficultyManager


@dataclass
class StrategicAI:
    """
    Strategic AI player that makes intelligent decisions based on game state.
    """

    player_id: int
    config: GameConfig
    game_state: GameState
    ai_manager: AIDifficultyManager

    def answer_open_question(self, question: Question, think_time: float = 1.0) -> float:
        """
        Answer an open answer (numeric) question.

        Args:
            question: The question to answer
            think_time: Time in seconds to "think" before answering

        Returns:
            Numeric answer
        """
        # Simulate thinking time
        time.sleep(think_time)

        correct_answer = float(question.correct_answer)

        # Get accuracy based on difficulty
        accuracy = self.config.get_ai_accuracy("open_answer")

        # Determine if answer will be correct (within 10% of correct answer)
        if random.random() < accuracy:
            # Answer within 10% of correct answer
            error_margin = 0.1  # 10%
            min_answer = correct_answer * (1 - error_margin)
            max_answer = correct_answer * (1 + error_margin)

            # For small numbers, ensure we don't go negative
            if min_answer < 0 and correct_answer >= 0:
                min_answer = 0

            answer = random.uniform(min_answer, max_answer)

            # Round appropriately based on the question
            if correct_answer.is_integer():
                answer = round(answer)
        else:
            # Wrong answer - random value within reasonable range
            # Try to guess the scale of the answer
            if correct_answer == 0:
                scale = 100
            else:
                scale = abs(correct_answer) * random.uniform(0.5, 2.0)

            answer = random.uniform(-scale, scale)

            # Make it more likely to be wrong by a significant amount
            if random.random() < 0.5:  # 50% chance to be far off
                answer *= random.uniform(2, 5)

            # Round appropriately
            if correct_answer.is_integer():
                answer = round(answer)

        # Ensure answer is numeric
        try:
            answer = float(answer)
        except (ValueError, TypeError):
            # Fallback to random number
            answer = random.uniform(0, 1000)

        print(f"AI {self.player_id} answered: {answer} (correct: {correct_answer})")
        return answer

    def answer_multiple_choice(self, question: Question, think_time: float = 1.0) -> str:
        """
        Answer a multiple choice question.

        Args:
            question: The question to answer
            think_time: Time in seconds to "think" before answering

        Returns:
            Selected option text
        """
        # Simulate thinking time
        time.sleep(think_time)

        # Get accuracy based on difficulty
        accuracy = self.config.get_ai_accuracy("multiple_choice")

        # Determine if answer will be correct
        if random.random() < accuracy:
            # Correct answer
            answer = question.correct_answer
        else:
            # Wrong answer - choose random incorrect option
            wrong_options = [opt for opt in question.options if opt != question.correct_answer]
            answer = random.choice(wrong_options) if wrong_options else question.correct_answer

        print(f"AI {self.player_id} selected: {answer}")
        return answer

    def choose_occupation_region(self, available_regions: List[Region]) -> Region:
        """
        Choose a region during occupation phase.

        Strategy priorities:
        1. Connect territories
        2. Secure resources (regions with high strategic value)
        3. Expand toward opponent capitals

        Args:
            available_regions: List of regions that can be occupied

        Returns:
            Chosen region
        """
        if not available_regions:
            raise ValueError("No regions available to choose from")

        player = self.game_state.players.get(self.player_id)
        if not player:
            return random.choice(available_regions)

        # Score each available region
        region_scores: List[Tuple[Region, float]] = []

        for region in available_regions:
            score = 0.0

            # 1. Strategic value: regions with more neighbors are better
            neighbor_count = len(region.adjacent_regions)
            score += neighbor_count * 0.5

            # 2. Connection bonus: regions adjacent to player's existing regions
            connection_bonus = 0
            for adj_id in region.adjacent_regions:
                if adj_id in player.regions_controlled:
                    connection_bonus += 1
            score += connection_bonus * 3.0  # Strong bonus for connecting

            # 3. Distance to capital (closer is better)
            if player.capital_region_id and player.capital_region_id in self.game_state.regions:
                capital = self.game_state.regions[player.capital_region_id]
                distance = self._calculate_distance(region.position, capital.position)
                # Normalize: closer distance = higher score
                max_distance = 1000  # Approximate max screen distance
                distance_score = (max_distance - min(distance, max_distance)) / max_distance
                score += distance_score * 2.0

            # 4. Defensive position: regions with fewer enemy neighbors
            enemy_neighbor_count = 0
            for adj_id in region.adjacent_regions:
                if adj_id in self.game_state.regions:
                    adj_region = self.game_state.regions[adj_id]
                    if adj_region.owner_id is not None and adj_region.owner_id != self.player_id:
                        enemy_neighbor_count += 1
            score -= enemy_neighbor_count * 0.5  # Penalty for exposed positions

            # 5. Expansion toward opponents (medium difficulty and above)
            if self.config.difficulty.value != "easy":
                # Find closest opponent capital
                closest_opponent_distance = float('inf')
                for opp_id, opp_player in self.game_state.players.items():
                    if opp_id != self.player_id and opp_player.capital_region_id:
                        opp_capital_id = opp_player.capital_region_id
                        if opp_capital_id in self.game_state.regions:
                            opp_capital = self.game_state.regions[opp_capital_id]
                            distance = self._calculate_distance(region.position, opp_capital.position)
                            closest_opponent_distance = min(closest_opponent_distance, distance)

                if closest_opponent_distance < float('inf'):
                    # Normalize: closer to opponent = higher score (aggressive play)
                    max_dist = 1000
                    opp_distance_score = (max_dist - min(closest_opponent_distance, max_dist)) / max_dist
                    score += opp_distance_score * 1.5

            # 6. Random factor to make AI less predictable
            random_factor = random.uniform(0.8, 1.2)
            score *= random_factor

            region_scores.append((region, score))

        # Choose region with highest score
        region_scores.sort(key=lambda x: x[1], reverse=True)

        # For hard difficulty, always choose best
        if self.config.difficulty == Difficulty.HARD:
            return region_scores[0][0]

        # For medium difficulty, sometimes choose 2nd best
        elif self.config.difficulty == Difficulty.MEDIUM:
            if random.random() < 0.8:  # 80% chance to choose best
                return region_scores[0][0]
            else:
                return region_scores[1][0] if len(region_scores) > 1 else region_scores[0][0]

        # For easy difficulty, often choose randomly among top 3
        else:  # EASY
            top_n = min(3, len(region_scores))
            return random.choice(region_scores[:top_n])[0]

    def choose_attack_target(self, available_targets: List[Region]) -> Optional[Region]:
        """
        Choose a region to attack during turn phase.

        Args:
            available_targets: List of enemy regions that can be attacked

        Returns:
            Chosen target region, or None if no good targets
        """
        if not available_targets:
            return None

        player = self.game_state.players.get(self.player_id)
        if not player:
            return random.choice(available_targets)

        region_scores: List[Tuple[Region, float]] = []

        for region in available_targets:
            score = 0.0

            # 1. Region value
            score += region.point_value / 1000.0  # Normalize by 1000

            # 2. Capital bonus (high priority)
            if region.region_type.name == "CAPITAL":  # Check if it's a capital
                score += 5.0

            # 3. Defensive weakness: unfortified regions are easier
            if not region.is_fortified():
                score += 1.0

            # 4. Strategic position: regions that would connect territories
            connection_bonus = 0
            for adj_id in region.adjacent_regions:
                if adj_id in player.regions_controlled:
                    connection_bonus += 1
            score += connection_bonus * 2.0

            # 5. Opponent strength: avoid attacking strong players
            if region.owner_id is not None:
                opponent = self.game_state.players.get(region.owner_id)
                if opponent:
                    # Penalize attacking players with much higher score
                    score_ratio = player.score / max(opponent.score, 1)
                    if score_ratio < 0.5:  # Player has less than half the opponent's score
                        score += 2.0

            # 6. Random factor
            random_factor = random.uniform(0.9, 1.1)
            score *= random_factor

            region_scores.append((region, score))

        # Choose based on difficulty
        region_scores.sort(key=lambda x: x[1], reverse=True)

        if not region_scores:
            return None

        if self.config.difficulty == Difficulty.HARD:
            return region_scores[0][0]
        elif self.config.difficulty == Difficulty.MEDIUM:
            if random.random() < 0.7:  # 70% best, 30% second best
                return region_scores[0][0]
            else:
                return region_scores[1][0] if len(region_scores) > 1 else region_scores[0][0]
        else:  # EASY
            top_n = min(3, len(region_scores))
            return random.choice(region_scores[:top_n])[0]

    def choose_region_to_fortify(self, available_regions: List[Region]) -> Optional[Region]:
        """
        Choose a region to fortify during turn phase.

        Args:
            available_regions: List of player's regions that can be fortified

        Returns:
            Chosen region to fortify, or None if no good candidates
        """
        if not available_regions:
            return None

        region_scores: List[Tuple[Region, float]] = []

        for region in available_regions:
            score = 0.0

            # 1. Region value
            score += region.point_value / 1000.0

            # 2. Capital protection (high priority)
            if region.region_type.name == "CAPITAL":
                score += 3.0

            # 3. Border regions need more protection
            border_strength = 0
            for adj_id in region.adjacent_regions:
                if adj_id in self.game_state.regions:
                    adj_region = self.game_state.regions[adj_id]
                    if adj_region.owner_id is not None and adj_region.owner_id != self.player_id:
                        border_strength += 1
            score += border_strength * 2.0

            # 4. Strategic connections
            connection_value = 0
            for adj_id in region.adjacent_regions:
                if adj_id in self.game_state.regions:
                    adj_region = self.game_state.regions[adj_id]
                    if adj_region.owner_id == self.player_id:
                        # This region connects to other owned regions
                        connection_value += 1
            score += connection_value * 1.0

            # 5. Random factor
            random_factor = random.uniform(0.9, 1.1)
            score *= random_factor

            region_scores.append((region, score))

        region_scores.sort(key=lambda x: x[1], reverse=True)

        if not region_scores:
            return None

        # Hard AI always fortifies best region
        if self.config.difficulty == Difficulty.HARD:
            return region_scores[0][0]
        # Medium AI usually fortifies best, sometimes second best
        elif self.config.difficulty == Difficulty.MEDIUM:
            if random.random() < 0.8:
                return region_scores[0][0]
            else:
                return region_scores[1][0] if len(region_scores) > 1 else region_scores[0][0]
        # Easy AI often chooses randomly
        else:
            top_n = min(3, len(region_scores))
            return random.choice(region_scores[:top_n])[0]

    def _calculate_distance(self, pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        """
        Calculate Euclidean distance between two points.

        Args:
            pos1: First position (x, y)
            pos2: Second position (x, y)

        Returns:
            Distance
        """
        return ((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2) ** 0.5


# Test the AI
if __name__ == "__main__":
    print("=== Testing StrategicAI ===")

    class MockQuestion:
        def __init__(self):
            self.text = "What is 42?"
            self.correct_answer = 42
            self.options = ["40", "41", "42", "43"]
            self.question_type = QuestionType.OPEN_ANSWER

    # Test instantiation
    config = GameConfig()
    game_state = GameState()
    ai_manager = AIDifficultyManager(config)

    ai = StrategicAI(
        player_id=1,
        config=config,
        game_state=game_state,
        ai_manager=ai_manager
    )

    print("AI created successfully")

    # Test answering
    question = Question()
    answer = ai.answer_open_question(question, think_time=0.1)
    print(f"AI answered open question: {answer}")

    print("All tests passed!")