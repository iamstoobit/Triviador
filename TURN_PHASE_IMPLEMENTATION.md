# Turn Phase Implementation

## Overview
The turn phase has been fully implemented in `src/game/core.py` with complete support for both human and AI players. The implementation follows a similar structure to the occupation phase but with strategic decision-making via the StrategicAI class.

## Main Components Implemented

### 1. **turn_phase()** - Main Game Loop
**Location:** `core.py:791-871`

The core turn phase method that orchestrates the entire turn system:

```
Flow:
1. Get turn order using state.get_player_turn_order()
2. Initialize total_turns = alive_players × max_turns_per_player
3. Loop while current_turn < total_turns:
   - Determine current player via round-robin
   - Get available actions via logic.get_available_actions(player_id)
   - If player is HUMAN: _execute_human_turn()
   - If player is AI: _execute_ai_turn()
   - Increment turn counter if action completed
   - Check for early game end (≤1 players alive)
4. Call end_turn_phase() when complete
```

Key Features:
- Round-robin player rotation
- Automatic skipping of dead players
- Early game termination when only 0-1 players remain
- Proper state management (current_player_id, current_phase, current_turn)

---

### 2. **_execute_human_turn()** - Human Player Actions
**Location:** `core.py:874-934`

Handles human player turns with UI integration:

**Process:**
1. Highlight available regions using `_highlight_available_regions()`
2. Display message prompting region selection
3. Wait for player click in game loop
4. Execute selected action (attack or fortify)
5. Unhighlight regions

**Key Features:**
- 60-second timeout for action selection
- Auto-selects action if timeout occurs
- Proper UI state management
- Region highlighting shows both attack and fortify targets

---

### 3. **_execute_ai_turn()** - AI Player Actions
**Location:** `core.py:936-989`

Fully leverages StrategicAI class methods for intelligent decision-making:

**Decision Priority:**
1. **Attack Phase:** 
   - Gets all attackable regions from `available_actions['attack']`
   - Uses `StrategicAI.choose_attack_target(attack_targets)` to select best target
   - Considers: region value, capital status, fortification level, strategic connections, opponent strength

2. **Fortify Phase:** (if no good attacks available)
   - Gets all fortifiable regions from `available_actions['fortify']`
   - Uses `StrategicAI.choose_region_to_fortify(fortify_targets)` to select best region
   - Considers: region value, capital protection, border strength, strategic connections

**Key Features:**
- Uses StrategicAI methods to determine actions
- Follows difficulty-based strategy (EASY, MEDIUM, HARD)
- Proper AI logging for debugging
- Falls back gracefully if no actions available

---

### 4. **_execute_turn_action()** - Action Resolution
**Location:** `core.py:991-1036`

Executes either attack or fortify action:

**Attack Logic:**
- Validates via `logic.can_attack_region()`
- Calls `_start_turn_battle()` to initiate battle
- Triggers complete battle flow with questions

**Fortify Logic:**
- Validates via `logic.can_fortify_region()`
- Executes via `logic.fortify_region()`
- Plays sound effect if available
- Draws changes and brief pause for visual feedback

**Returns:** True if action was successful

---

### 5. **_start_turn_battle()** - Battle Initiation
**Location:** `core.py:1038-1060`

Initiates a battle sequence:

**Setup:**
- Determines battle type (BATTLE or CAPITAL_ATTACK)
- Creates BattleResult object with attacker/defender/region info
- Calls `start_battle_question_flow()` for full battle resolution

---

### 6. **start_battle_question_flow()** - Complete Battle Resolution
**Location:** `core.py:1115-1178`

Full battle flow with trivia question:

**Process:**
1. Get multiple choice question from database
2. Get answers from both players:
   - If human: `_get_human_battle_answer()` via UI
   - If AI: `StrategicAI.answer_multiple_choice()` via AI
3. Resolve battle via `logic.resolve_battle()`
4. Apply results via `_apply_battle_result()`

**Key Features:**
- Handles both human and AI players
- Uses difficulty-based AI accuracy
- Blocks until both answers received
- Updates game state with battle outcome

---

### 7. **_get_human_battle_answer()** - Human Battle Questions
**Location:** `core.py:1180-1212`

Gets human player's answer for battle questions:

**Process:**
1. Shows question via `screen_manager.show_multiple_choice_question()`
2. Sets timeout based on `config.battle_question_time`
3. Waits in game loop for answer
4. Returns player's selected answer or None on timeout

**Key Features:**
- Full UI integration
- Timeout handling
- Proper event loop management

---

### 8. **_apply_battle_result()** - Battle Outcome Application
**Location:** `core.py:1214-1256`

Applies battle results to game state:

**If Attacker Wins:**
- Transfers region ownership
- Updates player regions_controlled
- Resets fortification level
- Awards points via `logic.calculate_region_value()`

**If Defender Wins:**
- Awards defender bonus points if applicable
- Logs victory

**Logging:** Detailed logging of all state changes

---

### 9. **_highlight_available_regions()** - Visual Feedback
**Location:** `core.py:1062-1086`

Highlights selectable regions for human players:

**Features:**
- Attack targets marked with `highlight_type = "attack"`
- Fortify targets marked with `highlight_type = "fortify"`
- Sets `is_selectable = True` for highlighting in UI
- Logs number of highlighted regions

---

### 10. **_unhighlight_all_regions()** - Cleanup
**Location:** `core.py:1088-1093`

Removes all region highlighting after turn completion:

**Process:**
- Sets `is_selectable = False`
- Clears `highlight_type` attribute
- Prepares for next turn's highlights

---

### 11. **handle_turn_region_click()** - Input Handler
**Location:** `core.py:1095-1110`

Handles mouse clicks on regions during turn phase:

**Logic:**
- Checks if region is selectable
- Determines action type based on ownership:
  - Player owns region → "fortify"
  - Enemy region → "attack"
- Sets selected region and action
- Ends region selection

---

### 12. **end_turn_phase()** - Phase Conclusion
**Location:** `core.py:1258-1272`

Concludes the turn phase:

**Process:**
1. Check for game winner via `logic.check_game_over()`
2. If winner found: set GAME_OVER phase
3. Otherwise: end game naturally
4. Logging of phase conclusion

---

## Integration with Existing Systems

### StrategicAI Methods Used:
- `choose_attack_target(targets: List[Region]) -> Optional[Region]`
- `choose_region_to_fortify(targets: List[Region]) -> Optional[Region]`
- `answer_multiple_choice(question, think_time) -> str`

### GameLogic Methods Used:
- `get_available_actions(player_id) -> Dict[str, List[int]]`
- `can_attack_region(attacker_id, region_id) -> bool`
- `can_fortify_region(player_id, region_id) -> bool`
- `fortify_region(player_id, region_id) -> bool`
- `resolve_battle(...) -> BattleResult`
- `calculate_region_value(region) -> int`
- `check_game_over() -> Optional[int]`

### GameState Methods Used:
- `get_player_turn_order() -> List[int]`
- `get_alive_players() -> List[Player]`
- `get_player_regions(player_id) -> List[Region]`

### UI/Screen Integration:
- `screen_manager.show_multiple_choice_question(question, time_limit)`
- `screen_manager.draw_message(text)`
- `sound_manager.play_sound("fortify")`

---

## AI Decision Making

The implementation leverages StrategicAI's intelligent decision-making:

### Attack Target Selection (`choose_attack_target`):
1. **Region Value** - Higher value regions prioritized
2. **Capital Bonus** - +5.0 score for attacking capitals
3. **Fortification** - Unfortified regions easier to attack (+1.0)
4. **Territory Connection** - Regions connecting to player's territory (+2.0 each)
5. **Opponent Strength** - Bonus (+2.0) if opponent is much stronger
6. **Random Factor** - 0.9-1.1 multiplier for unpredictability
7. **Difficulty Modifier**:
   - HARD: Always chooses highest score
   - MEDIUM: 70% best choice, 30% second best
   - EASY: Randomly chosen from top 3

### Fortification Selection (`choose_region_to_fortify`):
1. **Region Value** - Higher value regions prioritized
2. **Capital Protection** - +3.0 for defending capitals
3. **Border Strength** - +2.0 per enemy neighbor
4. **Strategic Connections** - +1.0 per connected friendly region
5. **Random Factor** - 0.9-1.1 multiplier
6. **Difficulty Modifier** - Same as attack selection

---

## Game Flow Summary

```
turn_phase()
├─ Get turn order
├─ Loop: while current_turn < total_turns
│  ├─ Determine current player
│  ├─ Get available_actions
│  ├─ if player.type == HUMAN
│  │  └─ _execute_human_turn()
│  │     ├─ Highlight regions
│  │     ├─ Wait for selection
│  │     └─ _execute_turn_action()
│  └─ else (AI)
│     └─ _execute_ai_turn()
│        ├─ Use StrategicAI to decide action
│        └─ _execute_turn_action()
│           ├─ if attack:
│           │  └─ _start_turn_battle()
│           │     └─ start_battle_question_flow()
│           │        ├─ Get both answers
│           │        ├─ resolve_battle()
│           │        └─ _apply_battle_result()
│           └─ if fortify:
│              └─ logic.fortify_region()
├─ Check for early termination
└─ end_turn_phase()
```

---

## Key Features

✅ **Full Human-AI Support** - Both player types handled correctly
✅ **Strategic AI** - Uses StrategicAI methods for intelligent decisions
✅ **UI Integration** - Region highlighting, selection, and messages
✅ **Battle System** - Trivia questions determine battle outcomes
✅ **Sound Effects** - Play feedback for fortification
✅ **Error Handling** - Validation and fallbacks throughout
✅ **Logging** - Detailed console output for debugging
✅ **Timeout Management** - Prevents infinite waits
✅ **Early Termination** - Ends turn phase if only 1 player remains
✅ **State Management** - Proper tracking of game state throughout

---

## Testing Recommendations

1. **Human Player**:
   - Test region selection UI
   - Test attack and fortify actions
   - Test timeout handling (60s)
   - Test with multiple regions available

2. **AI Players**:
   - Verify strategic choices using StrategicAI methods
   - Test all difficulty levels (EASY, MEDIUM, HARD)
   - Verify fortification occurs when no attacks available
   - Test with different game states (many/few options)

3. **Battle System**:
   - Human vs Human battles
   - Human vs AI battles
   - AI vs AI battles
   - Verify battle outcomes match game rules

4. **Edge Cases**:
   - No available actions (both lists empty)
   - Only 1 player alive
   - Dead players in turn order
   - Region ownership changes during battles
