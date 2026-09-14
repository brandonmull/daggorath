-- Scripted machine save-load plugin.
--
-- Plays a scripted situation in the game and freezes it with machine:save, or
-- reports what a frozen machine came back with. Everything happens here: the
-- phrases are posted straight to natkeyboard and the game's RAM is read
-- directly, so no part of the environment is involved.
--
-- The addresses come from docs/references/game/ram.md. The 0x026E meaning —
-- the light the player sees — was confirmed by the torch-light sandbox.
--
-- Environment:
--   SANDBOX_MODE            "setup" to play and save, "verify" to report a load
--   SANDBOX_STATE_NAME      the state to write, or the one that was loaded
--   SANDBOX_STATE_DIRECTORY where states live, for the report
--   SANDBOX_REPORT_FILE     where the report is written

local exports = {}
exports.name = "scripted"
exports.version = "0.0.1"
exports.license = "MIT"
exports.author = { name = "Daggorath Gym" }

-- Game facts, from docs/references/game/ram.md.
local DISPLAY_FUNCTION_HI = 0x02B2
local DISPLAY_FUNCTION_LO = 0x02B3
local DISPLAY_LOOK = 0xCE66
local PLAYER_X = 0x0214
local PLAYER_Y = 0x0213
local PLAYER_DIRECTION = 0x0223
local EFFECTIVE_LIGHT_PHYSICAL = 0x026E
local LEFT_HAND_HI = 0x021D
local LEFT_HAND_LO = 0x021E
local RIGHT_HAND_HI = 0x021F
local RIGHT_HAND_LO = 0x0220
local TORCH_POINTER_HI = 0x0224
local TORCH_POINTER_LO = 0x0225
local OBJECT_MINUTES_OFFSET = 6
local OBJECT_PHYSICAL_LIGHT_OFFSET = 7

-- What each step of the scripted situation must change. The phrases are
-- posted in order; after each one settles, its expectation is judged against
-- the facts taken just before it was posted.
local EXPECTATIONS = {
    {
        "PULL LEFT TORCH", "a hand holds the torch",
        function(before, after)
            return before.leftHand == 0 and before.rightHand == 0
                and (after.leftHand ~= 0 or after.rightHand ~= 0)
        end,
    },
    {
        "USE LEFT", "the torch is lit and the dungeon is lit",
        function(_, after)
            return after.torchPointer ~= 0 and after.torchPhysicalLight > 0
                and after.effectiveLightPhysical > 0
        end,
    },
    {
        "MOVE", "the player moved",
        function(before, after)
            return after.playerX ~= before.playerX or after.playerY ~= before.playerY
        end,
    },
}

-- The situation: take the torch, light it, then walk forward three cells.
local SEQUENCE = { 1, 2, 3, 3, 3 }

-- Room for the phrase to be typed and its effect to land: the command-latency
-- measurement put typing at about ten frames per character, and the longest
-- phrase here is fifteen characters.
local COMMAND_SETTLE_FRAMES = 260

-- The game sits in a demo loop until a key arrives; a Return leaves it, and
-- the environment's plugin primes the same way at the same frame.
local PRIME_FRAME = 300

-- Margin after the game reaches its play screen before the first post.
local READY_SETTLE_FRAMES = 60

-- The game's play screen arrives around frame 725; give it room before giving
-- up on it.
local READY_LIMIT_FRAMES = 3000

-- Frames to wait before reporting a loaded machine.
local VERIFY_FRAME = 30

local DONE_SENTINEL = "scripted: done"

local _mode = os.getenv("SANDBOX_MODE") or "setup"
local _stateName = os.getenv("SANDBOX_STATE_NAME") or ""
local _stateDirectory = os.getenv("SANDBOX_STATE_DIRECTORY") or ""
local _reportFile = io.open(os.getenv("SANDBOX_REPORT_FILE") or "/dev/null", "w")
local _frameSubscription = nil
local _frame = 0
local _primed = false
local _started = false
local _nextActionFrame = 0
local _step = 0
local _lastFacts = nil
local _startFacts = nil
local _failures = 0
local _finished = false


local function _report(line)
    print(line)
    _reportFile:write(line .. "\n")
    _reportFile:flush()
end


local function _readU8(address)
    return manager.machine.devices[":maincpu"].spaces["program"]:read_u8(address)
end


local function _readU16(highAddress, lowAddress)
    return _readU8(highAddress) * 256 + _readU8(lowAddress)
end


local function _displayFunction()
    return _readU16(DISPLAY_FUNCTION_HI, DISPLAY_FUNCTION_LO)
end


local function _facts()
    local torchPointer = _readU16(TORCH_POINTER_HI, TORCH_POINTER_LO)
    local torchMinutes = 0
    local torchLight = 0
    if torchPointer ~= 0 then
        torchMinutes = _readU8(torchPointer + OBJECT_MINUTES_OFFSET)
        torchLight = _readU8(torchPointer + OBJECT_PHYSICAL_LIGHT_OFFSET)
    end
    return {
        leftHand = _readU16(LEFT_HAND_HI, LEFT_HAND_LO),
        rightHand = _readU16(RIGHT_HAND_HI, RIGHT_HAND_LO),
        torchPointer = torchPointer,
        torchMinutes = torchMinutes,
        torchPhysicalLight = torchLight,
        effectiveLightPhysical = _readU8(EFFECTIVE_LIGHT_PHYSICAL),
        playerX = _readU8(PLAYER_X),
        playerY = _readU8(PLAYER_Y),
        playerDirection = _readU8(PLAYER_DIRECTION),
    }
end


local function _reportFacts(label, facts)
    _report(
        label
        .. " hands=" .. facts.leftHand .. "," .. facts.rightHand
        .. " torch=" .. facts.torchPointer
        .. " minutes=" .. facts.torchMinutes
        .. " torchLight=" .. facts.torchPhysicalLight
        .. " seenLight=" .. facts.effectiveLightPhysical
        .. " cell=" .. facts.playerX .. "," .. facts.playerY
        .. " facing=" .. facts.playerDirection
    )
end


local function _finish(succeeded)
    if _finished then
        return
    end
    _finished = true
    if succeeded then
        _report(DONE_SENTINEL .. " ok")
    else
        _report(DONE_SENTINEL .. " failed")
    end
end


local function _phraseFor(step)
    return EXPECTATIONS[SEQUENCE[step]][1]
end


local function _evaluateStep(step, before, after)
    local expectation = EXPECTATIONS[SEQUENCE[step]]
    _reportFacts("after " .. expectation[1], after)
    if expectation[3](before, after) then
        _report("PASS  " .. expectation[2])
    else
        _report("FAIL  " .. expectation[2])
        _failures = _failures + 1
    end
end


local function _finishSetup()
    _reportFacts("start", _startFacts)
    _reportFacts("end", _facts())
    if _failures > 0 then
        _report("not saving: " .. _failures .. " step(s) did not play out as expected")
        _finish(false)
        return
    end
    manager.machine:save(_stateName)
    _report("saved " .. _stateName .. " under " .. _stateDirectory)
    _finish(true)
end


local function _onFrame()
    _frame = _frame + 1
    if _finished then
        return
    end

    if _mode == "verify" then
        if _frame == VERIFY_FRAME then
            _report("machine time: " .. string.format("%.3f", manager.machine.time.seconds) .. "s")
            _reportFacts("loaded", _facts())
            _report("state: " .. _stateName .. " under " .. _stateDirectory)
            _finish(true)
        end
        return
    end

    if not _primed then
        if _frame >= PRIME_FRAME then
            _primed = true
            manager.machine.natkeyboard:post("\r")
            _report("left the demo loop at frame " .. _frame)
        end
        return
    end

    if not _started then
        if _displayFunction() == DISPLAY_LOOK then
            _started = true
            _startFacts = _facts()
            _nextActionFrame = _frame + READY_SETTLE_FRAMES
            _report("live play at frame " .. _frame)
        elseif _frame > READY_LIMIT_FRAMES then
            _report("the game never reached its play screen")
            _finish(false)
        end
        return
    end

    if _frame < _nextActionFrame then
        return
    end

    -- The wait after the last post has just elapsed; judge that step.
    if _step > 0 then
        _evaluateStep(_step, _lastFacts, _facts())
    end

    if _step >= #SEQUENCE then
        _finishSetup()
        return
    end

    _step = _step + 1
    _lastFacts = _facts()
    local phrase = _phraseFor(_step)
    manager.machine.natkeyboard:post(phrase .. "\r")
    _report("posted " .. phrase .. " at frame " .. _frame)
    _nextActionFrame = _frame + COMMAND_SETTLE_FRAMES
end


function exports.startplugin()
    -- Held in a module-local: a discarded subscription is collected, and the
    -- callback stops firing.
    _frameSubscription = emu.add_machine_frame_notifier(_onFrame)
end


return exports
