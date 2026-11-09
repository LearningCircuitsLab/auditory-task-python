# Task logic: a walkthrough for newcomers

This repository holds the behavioural tasks that run on the **Training Village**
(the `village` package) for the two-alternative forced choice (2AFC) task with
visual and auditory stimuli. A mouse pokes the center port, gets a stimulus, and
must poke the left or right port that the stimulus points to.

The two files that matter most are:

| File | What it does |
|---|---|
| `twoAFC.py` | The task itself: builds each trial, runs it on the Bpod, saves what happened. |
| `training_protocol.py` | The settings of every subject, and the rules that move it through the training stages after each session. |

Other files you will meet:

| File | What it does |
|---|---|
| `habituation.py` | The first task every mouse runs: any side poke is rewarded. |
| `softcode_functions.py` | Functions the Bpod calls during a trial (stop, load and play sounds, punishment noise). |
| `sound_functions.py` | Sound generation (cloud of tones, white noise) and `speaker_dict`, which says which speakers each rig has. |
| `online_plot.py`, `session_plot.py`, `subject_plot.py`, `trial_plotter.py` | Plots shown in the village GUI. |
| `auto2AFC.py`, `virtual_mouse.py`, `task_runner.py`, `test.py`, `playground.py` | Helpers for testing without a real mouse. |

---

## 1. How the village runs a task

The village calls the methods of the task in this order:

```
start()                     once, at the beginning of the session
loop until the session ends:
    create_trial()          build the Bpod state machine of the next trial
    (the Bpod runs the trial)
    after_trial()           read what happened and save it
close()                     once, at the end
then, outside the task:
    TrainingProtocol.update_training_settings()   decide the settings of the next session
```

- `self.settings` holds the subject's settings. They are defined in
  `TrainingProtocol.default_training_settings()` and edited in the GUI.
- `self.trial_data` holds the timestamps of every state and event of the trial
  (for example `STATE_stimulus_state_START`, `Port1In`). States that were not
  visited appear as `[nan]`.
- `self.register_value(name, value)` saves a column in the subject's data.

Ports: **1 = left, 2 = center, 3 = right**.

---

## 2. Modalities, training sequence and stages

### Modalities
A modality is the kind of cue that tells the mouse where the reward is. They are
defined once, at the top of `training_protocol.py`, and imported by `twoAFC.py`:

| Modality | Cue |
|---|---|
| `visual` | Both side ports light up; the brighter one is correct. |
| `auditory-cot` | A cloud of tones; the dominant frequency (high or low) says the side (`frequency_associated_with_left_choice`). |
| `auditory-local-wn` | White noise played only from the speaker on the correct side. Needs a rig with two speakers (see `speaker_dict`). |
| `multisensory` | Not a cue by itself: blocks of trials that alternate the single modalities of the training sequence. |

Modality names use **hyphens, never underscores**, because underscores separate
the parts of a stage name.

### Training sequence
Each subject has a training sequence, chosen in the GUI "Protocol" tab:

- `first_stimulus_modality`: a single modality (required).
- `second_stimulus_modality`: a different single modality, or `none`.
- `third_stimulus_modality`: `multisensory`, or `none`. Multisensory needs two
  single modalities before it.

`get_training_sequence(settings)` builds the list (for example
`["visual", "auditory-cot", "multisensory"]`) and raises a clear error if the
combination is not valid. Nothing else is stored: the sequence is always rebuilt
from these three settings.

### Stages
`current_training_stage` says where the subject is. It is one of:

- `Habituation`
- `TwoAFC_<modality>_<difficulty>`, for example `TwoAFC_auditory-cot_easy`.
  `parse_stage()` splits it into `("auditory-cot", "easy")`.
- `Manual_training`: the protocol does not move the subject. The modality comes
  from `manual_training_modality` (GUI tab "Manual training only"), the only
  place where that setting is used.

**The stage is the single source of truth.** The modality of a session and the
position in the training sequence are both derived from it, never stored apart.

---

## 3. Settings in the GUI

| Tab | Contents |
|---|---|
| Protocol | The training sequence (first, second, third modality). |
| Difficulty | Which difficulties are on (easy / medium / hard), and the trials needed in each modality's hard stage to move on. |
| Habituation | Initial large reward, time to automatic reward. |
| Visual | Brightness range of the dimmer port, brightness ratio per difficulty, light distractor. |
| Manual training only | `manual_training_modality`. |
| Sound COT | Everything about the cloud of tones (frequencies, durations, loudness, proportion of dominant tones per difficulty, unilateral sound, tone distractor). |
| Sound loc | White noise duration and loudness range per difficulty. |

Settings that are in no tab appear in the general panel on the right of the GUI
(for example `punishment`, `iti`, `reward_amount_ul`, `anti_bias_on`).

`reward_amount_ul` is in **µl**, the unit of the water calibration.

---

## 4. One trial, step by step

### `start()` (once per session)
1. Valve opening times from the water calibration.
2. Punishment choices: with `punishment` off, a wrong poke sends the mouse back to
   `stimulus_state` to choose again. With `early_poke_punishment` off, leaving the
   center port too early sends it back to `ready_to_initiate`.
3. Holding time (how long the mouse must stay in the center port). It is checked
   and kept between `holding_response_time_min` and `holding_response_time_max`
   (a NaN or out-of-range value is replaced, with a warning).
4. Session modality, from the stage (or `manual_training_modality`).
5. For multisensory: the block modalities and a random first block.
6. Contingency of the cloud of tones (which frequency means left).
7. Anti-bias history, sound settings, speakers of this rig, and the parameters of
   each active difficulty.
8. Checks that stop the session with a clear message: no difficulty is on, or the
   brighter port could go above maximum brightness.

### `create_trial()`
1. `set_stimulus_modality()`: the modality of this trial (in multisensory, it
   changes when the block runs out).
2. `generate_trial_type()`: the correct side (50/50, or biased by the anti-bias)
   and a random difficulty among the active ones.
3. `set_stimulus_state_conditions()`: ports, valve and stimuli (section 5).
4. `assemble_state_machine()`: the Bpod states below.

### The state machine

```
start_of_trial          1 ms, TTL on BNC2
    ↓
ready_to_initiate       center light on; stop any sound (SoftCode1); load the trial sound (SoftCode2)
    ↓ center poke
hold_center_port        holding_response_time_min
    ↓                   (leaving early → punish_state or ready_to_initiate)
hold_while_stimulus     the rest of the holding time; stimulus starts here (lights, sound play SoftCode3)
    ↓                   (leaving early → punish_state or ready_to_initiate)
stimulus_state          stimulus on, waits up to timer_for_response for a side poke
    ├─ correct poke → reward_state (valve) → iti → end
    ├─ wrong poke   → punish_state (white noise, SoftCode4) → iti → end
    │                 (or back to stimulus_state if punishment is off)
    └─ no poke      → end (timeout, no iti)
```

### `after_trial()`
Saves the trial (section 6), increases the holding time after a correct trial,
and updates the anti-bias history.

---

## 5. Stimuli: the cue and the distractors

`set_stimulus_state_conditions()` separates two ideas:

- **The cue**: the stimulus of the trial's modality. It always points to the
  correct side.
- **Distractors**: an extra stimulus of another type that carries no information.
  They only appear in trials whose cue is a different type, so they can never
  randomize the cue.

| Trial modality | Cue | Possible distractors |
|---|---|---|
| visual | brighter correct port | random cloud of tones (`random_COT_stimulus`) |
| auditory-cot | cloud of tones | random light (`random_visual_stimulus`) |
| auditory-local-wn | white noise on the correct side | random light (`random_visual_stimulus`). Never a cloud of tones, so two sounds are never mixed. |

The builders:

- `add_visual_stimulus(informative)`: the dimmer port gets a random brightness in
  `side_port_wrong_intensities_extremes`; the brighter one is that value × the
  difficulty's `light_intensity_difference`. If informative, the brighter port is
  the correct one; if not, it is chosen at random.
- `add_cot_stimulus(informative)`: proportion of dominant tones from the
  difficulty (`*_frequency_proportion`). If informative, the dominant frequency
  follows the contingency; if not, it is random. Loudness is clipped to the
  calibrated range (see the comment in the code). With probability
  `unilateral_sound_probability` the tones are played from one speaker only
  (`choose_auditory_output_side()`).
- `add_local_wn_stimulus()`: loudness from the difficulty's
  `*_location_db_range`, played only from the correct side's speaker.

### How a sound gets played
The task stores the trial sound in `self.twoAFC_sound` (`{"left": ..., "right": ...}`)
through `set_trial_sound()`. The Bpod then calls the softcode functions in
`softcode_functions.py`, which read it from `manager.task.twoAFC_sound`:

| Softcode | When | Does |
|---|---|---|
| 1 | `ready_to_initiate` | stop sound |
| 2 | `ready_to_initiate` | load the trial sound |
| 3 | `hold_while_stimulus` | play it |
| 4 | `punish_state` | 1 s of white noise |

Sound gains come from the sound calibration (`one_thousand_hz_calibration`) of
each speaker.

---

## 6. What is saved for each trial

| Column | Meaning |
|---|---|
| `current_training_stage` | Stage of the session. |
| `correct_side` | Reward side of the trial (`left` / `right`). |
| `stimulus_modality` | Modality of this trial (in multisensory, the block's). |
| `difficulty` | `easy`, `medium` or `hard`. |
| `visual_stimulus` | **(left, right)** brightness of the side ports, or empty. See the TODO at the top of `twoAFC.py`: older data saved (correct, incorrect). |
| `auditory_stimulus` | Tone matrices (cloud of tones) or loudness and duration (white noise), or empty. |
| `auditory_output_side` | Speaker(s) that played the sound: `both`, `left` or `right`. |
| `auditory_real_statistics` | Statistics of the cloud of tones actually played. |
| `stimulus_modality_block_number` | Block number in multisensory sessions. |
| `correct` | `True` / `False` from the first side poke. **Early withdrawal** (the trial ended before `stimulus_state`) is `False`. **Timeout** (no side poke) is `None`. |
| `water` | µl delivered in the trial. |
| `holding_time` | Holding time used in the trial. |

The mouse's actual choice is not saved as a column: the analysis code
(`lecilab_behavior_analysis`) computes it from the poke timestamps.

---

## 7. Things that change within a session

- **Anti-bias** (`anti_bias_on`): keeps the last `anti_bias_vector_size` trials
  in which the mouse chose a side (timeouts and early withdrawals are skipped).
  `get_right_bias()` from the analysis library turns them into a bias between -1
  (left) and 1 (right), and the next correct side is drawn against the bias. It
  is off (50/50) until the history is full.
- **Holding time**: grows by `holding_response_time_step` after each correct
  trial, up to `holding_response_time_max`.
- **Multisensory blocks**: block sizes are drawn around
  `stimulus_modality_block_size` (± 30 %); modalities alternate in the order of
  the training sequence, starting with a random one.

---

## 8. Between sessions: the training protocol

After each session the village calls `update_training_settings()`, with
`self.df` holding the subject's whole history. In order:

1. Check the training sequence (a wrong combination raises an error, which the
   village reports as an alarm).
2. Manual runs in `Manual_training` change nothing.
3. Carry the holding time over: the last non-empty `holding_time` of the history
   (rows of other tasks are skipped).
4. Apply the rules of the current stage:

| Stage | Rule |
|---|---|
| Habituation | From the 4th session: no initial large reward, auto-reward time +20 s per session, longer sessions. After 150 trials in total: go to the first modality of the sequence, easy. |
| `_easy` | Uses only the trials of this stage. Last 3 days each over 85 % and over 100 trials: go to `_hard` (all difficulties on). If that modality's `*_hard_trials_to_promote` is 0 and there is a next modality, skip the hard stage and go straight to the next modality. Punishment on if the last 3 days are over 70 %, or the last 5 days under 60 %. |
| `_hard` | Punishment, if it was switched on in the easy stage, stays on. After `<modality>_hard_trials_to_promote` trials in the stage: go to the next modality of the sequence, easy (punishment off, anti-bias on). If there is no next modality, stay. Multisensory hard is always the last stage. |

Every promotion raises an alarm (`promotion_alarm()`).

**Session durations.** In Habituation (from the 4th session) and in easy stages
(from the 3rd day in the stage), `increase_min_time_and_refractory_period()` runs
after **every session**: +1 min to the minimum and maximum session duration and
+5 min to the refractory period, each up to a cap (Habituation: 20 min, 40 min,
3 h; easy: 25 min, 50 min, 4 h). Hard stages keep the values reached.

---

## 9. Common changes

- **Add a training sequence**: nothing to code, choose the modalities in the
  "Protocol" tab.
- **Change how fast a mouse leaves a hard stage**: the `*_hard_trials_to_promote`
  settings in the "Difficulty" tab (0 skips that hard stage).
- **Add a new modality**: add it to `SINGLE_MODALITIES` and
  `HARD_TRIALS_TO_PROMOTE_SETTINGS` in `training_protocol.py` (plus its default
  setting), write an `add_<modality>_stimulus()` builder in `twoAFC.py`, and call
  it from `set_stimulus_state_conditions()`.
- **Test without a mouse**: `auto2AFC.py` is the village "autonomouse" for
  TwoAFC: it pokes the ports during a real session (`run_trial`), or appends mock
  trials with the same columns as the task (`inject_trial`).
  `task_runner.py` runs the task with `virtual_mouse.py` and plots the results
  with `trial_plotter.py` (timeouts, `correct` = None, are not plotted).

---

## 10. Known open items

- The analysis code in `lecilab_behavior_analysis` still reads
  `visual_stimulus` as (correct, incorrect) and uses the old modality names. See
  the TODO at the top of `twoAFC.py`.
- The plots in `online_plot.py`, `session_plot.py` and `subject_plot.py` come
  from `lecilab_behavior_analysis`; they still have to be checked with
  `correct` = None (timeouts) and the new modality names.
- The white noise uses the 1 kHz calibration (`one_thousand_hz_calibration`);
  this is intentional for now.
