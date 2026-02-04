# Turn Phase Implementation - Clarifications

## 1. How the Human Player Sees the Multiple Choice Question

### Current Flow:

When `start_battle_question_flow()` calls `_get_human_battle_answer()`:

```
_get_human_battle_answer()
    ↓
screen_manager.show_question(question, time_limit=30)
    ↓
question_screen.set_question(question, time_limit)
    ↓
current_screen = ScreenType.QUESTION
    ↓
(In game loop) screen_manager.draw(game_state) draws the question screen
    ↓
QuestionScreen draws:
    - Question text
    - Multiple choice buttons (one for each option)
    - Timer/countdown
    - Battle info (attacker vs defender)
    ↓
Human clicks answer button
    ↓
question_screen.selected_answer is set
    ↓
Back in _get_human_battle_answer(), we return selected_answer
```

### Visual Display Details:

The question screen displays:
1. **Question Text Box** - Shows the battle question clearly
2. **Answer Buttons** - One interactive button per multiple choice option
3. **Timer** - Countdown showing time remaining
4. **Battle Info** - Shows who is attacking and who is defending
5. **Auto-submit** - If timer reaches 0, the answer is submitted (or default behavior)

The entire screen is managed by the `ScreenManager` and `QuestionScreen` classes from `src/ui/question_screen.py`.

---

## 2. Handling Ties with Open Answer Questions

### Current Status: 
The tie handling is **NOT YET IMPLEMENTED**. We need to add this logic.

### Required Changes:

When both players answer the MC question correctly, we need to:

1. **Detect the Tie** - Check if both answers are correct
2. **Ask Open Answer Question** - Get a numeric question
3. **Get Both Players' Answers** - Only the 2 battle participants answer
4. **Resolve by Proximity** - Winner is closest to correct answer
5. **Tiebreaker by Time** - If same distance, fastest wins

### Implementation Details:

Add to `start_battle_question_flow()` after `logic.resolve_battle()`:

```python
# After resolve_battle()
result = self.logic.resolve_battle(
    attacker_id=attacker_id,
    defender_id=defender_id,
    region_id=self.state.current_battle.region_id,
    question=question,
    attacker_answer=attacker_answer,
    defender_answer=defender_answer
)

# NEW: Check if tie (both correct → no winner yet)
if result.winner_id is None:  # Tie in MC
    print("  Tie in multiple choice! Going to open answer question...")
    
    # Ask open answer question
    open_question = self.trivia_db.get_open_question(categories)
    
    # Get answers from both players (only these 2)
    answers = {}
    answer_times = {}
    
    # Attacker's answer
    if attacker.player_type == PlayerType.HUMAN:
        answer = self._get_human_battle_open_answer(open_question)
    else:
        ai = self.ai_players[attacker_id]
        think_time = self.config.get_ai_think_time() / 1000.0
        answer = ai.answer_open_question(open_question, think_time)
    
    answers[attacker_id] = answer
    answer_times[attacker_id] = time.time()
    
    # Defender's answer
    if defender.player_type == PlayerType.HUMAN:
        answer = self._get_human_battle_open_answer(open_question)
    else:
        ai = self.ai_players[defender_id]
        think_time = self.config.get_ai_think_time() / 1000.0
        answer = ai.answer_open_question(open_question, think_time)
    
    answers[defender_id] = answer
    answer_times[defender_id] = time.time()
    
    # Resolve tie with open answer
    result = self.logic.resolve_open_answer_battle(
        attacker_id=attacker_id,
        defender_id=defender_id,
        region_id=self.state.current_battle.region_id,
        question=open_question,
        answers=answers,
        answer_times=answer_times
    )

# Apply result (this is the same as before)
self._apply_battle_result(result)
```

### New Helper Method Needed:

```python
def _get_human_battle_open_answer(self, question: Question) -> Optional[float]:
    """
    Get human player's open answer for a tie-breaking question.
    
    Args:
        question: The open answer question
        
    Returns:
        Player's numeric answer, or None if timeout
    """
    print("  Waiting for human player open answer (tie-breaker)...")
    
    # Show open answer question
    if self.screen_manager and question:
        self.screen_manager.show_open_question(
            question=question,
            time_limit=30  # 30 second timeout
        )
    
    # Wait for answer
    start_time = time.time()
    self.waiting_for_human_answer = True
    self.human_answer_value = None
    
    while self.waiting_for_human_answer:
        elapsed = time.time() - start_time
        if elapsed > 30:
            print("  Time's up for open answer question!")
            self.waiting_for_human_answer = False
            return None
        
        self.handle_events()
        self.update()
        self.draw()
        pygame.time.delay(10)
    
    return self.human_answer_value
```

### Using Existing Logic Method:

The `GameLogic.resolve_open_answer_battle()` method already exists and does exactly what we need:
- Takes answers from both players
- Calculates closeness to correct answer
- Uses time as tiebreaker
- Returns winner

This method is already used in the occupation phase, so the logic is proven!

---

## 3. Removing Unnecessary Context Variable

### Current Usage of `current_turn_context`:

Looking at the code, `current_turn_context` is set but **never actually used** because we use blocking game loops instead of callbacks.

### Simplification:

We can **remove** `current_turn_context` and **simplify** the code since we're already tracking everything we need:

**Instead of:**
```python
self.current_turn_context = {
    'player_id': player_id,
    'available_actions': available_actions
}
```

**Just use:**
```python
self.current_selection_player = player_id  # Already exists!
self.selectable_region_ids = available_actions['attack'] + available_actions['fortify']  # Already exists!
```

These instance variables are already defined in `__init__()` and serve the same purpose!

### Variables Already Available:

In `_execute_human_turn()`, we can access:
- `self.current_selection_player` - Who's turn it is
- `self.selectable_region_ids` - What regions they can select
- `self.waiting_for_region_selection` - Whether we're waiting
- `self.selected_region_id` - What they selected
- `self.selected_action` - What action they chose

No need for `current_turn_context` dictionary!

---

## Summary of Changes Needed

### 1. **Add Open Answer Tie-Breaking** (Required)
   - Add check for `result.winner_id is None` after MC battle
   - Ask open answer question
   - Get both players' answers (human UI + AI)
   - Call `logic.resolve_open_answer_battle()`
   - Apply the final result
   - New helper: `_get_human_battle_open_answer()`

### 2. **Remove Unnecessary Context** (Cleanup)
   - Remove `self.current_turn_context = {...}` from `_execute_human_turn()`
   - Remove context check from `handle_turn_region_click()` (it's not needed)
   - Use existing `self.current_selection_player` and `self.selectable_region_ids`

### 3. **Documentation** (Clarification)
   - The human sees MC questions through the `QuestionScreen` UI
   - Questions are rendered with buttons, timer, and battle info
   - Player clicks to select answer
   - Screen manager handles all the drawing

---

## Next Steps

Would you like me to implement these changes?

1. Add the tie-handling logic with open answer questions
2. Clean up by removing `current_turn_context` 
3. Test that everything works correctly
