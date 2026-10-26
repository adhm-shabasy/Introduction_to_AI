//  Game Setup
let currentMode = 'play';
let initialBoard = [1, 2, 5, 3, 4, 0, 6, 7, 8];
let currentBoard = [...initialBoard];

let userMoves = 0;
let gameActive = true;
let startTime = null;
let timerInterval = null;
let userScore = null; 

let results = {};
let selectedAlgo = null;
let states = [];
let moves = [];
let step = 0;
let playbackTimer = null;
let playbackDelay = 350;

const boardEl = document.getElementById("board");
const tiles = {};
const TILE_SIZE = 88;
const GAP = 8;

for (let i = 0; i < 9; i++) {
    const slot = document.createElement("div");
    slot.className = "slot";
    slot.style.transform = `translate(${(i % 3) * (TILE_SIZE + GAP)}px, ${Math.floor(i / 3) * (TILE_SIZE + GAP)}px)`;
    boardEl.appendChild(slot);
}
for (let t = 1; t < 9; t++) {
    const tile = document.createElement("div");
    tile.className = "tile";
    tile.textContent = t;
    tile.onclick = () => handleTileClick(t);
    boardEl.appendChild(tile);
    tiles[t] = tile;
}


// Game Logic
function drawBoard(state) {
    state.forEach((tileNum, index) => {
        if (tileNum === 0) return;
        const x = (index % 3) * (TILE_SIZE + GAP);
        const y = Math.floor(index / 3) * (TILE_SIZE + GAP);
        tiles[tileNum].style.transform = `translate(${x}px, ${y}px)`;
        tiles[tileNum].classList.toggle("home", tileNum === index);
    });
}

function handleTileClick(tileNum) {
    if (currentMode !== 'play' || !gameActive) return;

    let tileIdx = currentBoard.indexOf(tileNum);
    let blankIdx = currentBoard.indexOf(0);

    let tileRow = Math.floor(tileIdx / 3), tileCol = tileIdx % 3;
    let blankRow = Math.floor(blankIdx / 3), blankCol = blankIdx % 3;
    let isAdjacent = Math.abs(tileRow - blankRow) + Math.abs(tileCol - blankCol) === 1;

    if (isAdjacent) {
        if (userMoves === 0) startTimer();
        currentBoard[blankIdx] = tileNum;
        currentBoard[tileIdx] = 0;
        userMoves++;
        document.getElementById("moveCount").textContent = userMoves;
        drawBoard(currentBoard);

        if (currentBoard.join(",") === "0,1,2,3,4,5,6,7,8") {
            handleGameEnd('won');
        }
    }
}

// UI & Timers
function startTimer() {
    startTime = Date.now();
    timerInterval = setInterval(() => {
        let elapsed = Date.now() - startTime;
        let sec = Math.floor(elapsed / 1000);
        let ms = Math.floor((elapsed % 1000) / 100);
        let m = Math.floor(sec / 60);
        let s = sec % 60;
        document.getElementById("timerDisplay").textContent = 
            `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}.${ms}`;
    }, 100);
}

function handleGameEnd(status) {
    gameActive = false;
    clearInterval(timerInterval);
    
    let timeInSec = ((Date.now() - startTime) / 1000).toFixed(3);
    userScore = { cost: userMoves, time: parseFloat(timeInSec), status: status };

    let banner = document.getElementById("bannerContainer");
    if (status === 'won') {
        banner.innerHTML = `<div class="banner win">🎉 Solved! Moves: ${userMoves} · Time: ${timeInSec}s</div>`;
    } else {
        banner.innerHTML = `<div class="banner giveup">Gave Up after ${userMoves} moves</div>`;
    }
    triggerAiSolve();
}

function resetGame() {
    clearInterval(timerInterval);
    userMoves = 0;
    gameActive = true;
    userScore = null;
    currentBoard = [...initialBoard];
    
    document.getElementById("moveCount").textContent = "0";
    document.getElementById("timerDisplay").textContent = "00:00.0";
    document.getElementById("bannerContainer").innerHTML = "";
    document.getElementById("replayerSection").style.display = "none";
    document.getElementById("pathBox").hidden = true;
    
    results = {};
    selectedAlgo = null;
    drawBoard(currentBoard);
    renderTable();
}

// API Calls
async function postData(url, body) {
    let response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    return response.json();
}

async function triggerAiSolve() {
    stopPlayback();
    results = {};
    renderTable();

    ALGOS.forEach(async algo => {
        let data = await postData("/solve/" + algo.key, { state: initialBoard });
        results[algo.key] = data;
        
        if (!selectedAlgo) selectAlgorithm(algo.key);
        else renderTable();
    });
}


// Table Render & Playback
function renderTable() {
    let rows = document.getElementById("rows");
    rows.innerHTML = "";

    if (userScore && currentMode === 'play') {
        let isWon = userScore.status === 'won';
        let rowClass = isWon ? "user-row" : "user-row gave-up";
        rows.innerHTML += `
            <tr class="${rowClass}">
                <td><b>You (${isWon ? 'Solved' : 'Gave Up'})</b></td>
                <td>${userScore.cost}</td>
                <td>—</td><td>—</td>
                <td>${userScore.time.toFixed(3)}</td>
            </tr>`;
    }

    ALGOS.forEach(algo => {
        let r = results[algo.key];
        if (!r) {
            rows.innerHTML += `<tr><td>${algo.name}</td><td>...</td><td>...</td><td>...</td><td>running</td></tr>`;
        } else {
            let activeClass = algo.key === selectedAlgo ? "active row done" : "row done";
            rows.innerHTML += `
                <tr class="${activeClass}" onclick="selectAlgorithm('${algo.key}')">
                    <td>${algo.name}</td>
                    <td>${r.cost}</td>
                    <td>${r.nodes_expanded}</td>
                    <td>${r.depth}</td>
                    <td>${r.time.toFixed(4)}</td>
                </tr>`;
        }
    });
}

function selectAlgorithm(key) {
    stopPlayback();
    selectedAlgo = key;
    states = results[key].states;
    moves = results[key].moves;
    
    document.getElementById("slider").max = states.length - 1;
    document.getElementById("replayerSection").style.display = "block";
    
    showPlaybackStep(0);
    renderTable();

    let pathText = moves.join(" → ");
    if (pathText.length > 150) pathText = pathText.slice(0, 147) + "...";
    let pathBox = document.getElementById("pathBox");
    pathBox.innerHTML = `<b>Path:</b> ${pathText || "already solved"}`;
    pathBox.hidden = false;
}

function showPlaybackStep(n) {
    step = Math.max(0, Math.min(n, states.length - 1));
    drawBoard(states[step]);
    document.getElementById("slider").value = step;
    document.getElementById("status").textContent = `Step ${step} of ${states.length - 1}`;
}

function tickPlayback() {
    playbackTimer = setTimeout(() => {
        showPlaybackStep(step + 1);
        if (step >= states.length - 1) stopPlayback();
        else tickPlayback();
    }, playbackDelay);
}

function playPlayback() {
    if (step >= states.length - 1) showPlaybackStep(0);
    tickPlayback();
}

function stopPlayback() {
    clearTimeout(playbackTimer);
    playbackTimer = null;
}

// Event Listeners and modes
function setMode(mode) {
    currentMode = mode;
    document.getElementById("modePlayBtn").classList.toggle("active", mode === 'play');
    document.getElementById("modeBenchBtn").classList.toggle("active", mode === 'benchmark');

    if (mode === 'play') {
        document.getElementById("subTitle").textContent = "Try solving the puzzle yourself, or give up to compare against AI algorithms.";
        document.getElementById("gameStats").style.display = "flex";
        document.getElementById("gameControls").style.display = "flex";
        document.getElementById("setBoardBtn").style.display = "inline-block";
        document.getElementById("directSolveBtn").style.display = "none";
        resetGame();
    } else {
        document.getElementById("subTitle").textContent = "Directly compare search algorithms side-by-side.";
        document.getElementById("gameStats").style.display = "none";
        document.getElementById("gameControls").style.display = "none";
        document.getElementById("setBoardBtn").style.display = "none";
        document.getElementById("directSolveBtn").style.display = "inline-block";
        userScore = null;
        document.getElementById("bannerContainer").innerHTML = "";
        triggerAiSolve();
    }
}

async function setBoardFromInput() {
    let val = document.getElementById("stateInput").value;
    let nums = val.replace(/,/g, " ").trim().split(/\s+/).map(Number);
    
    if (nums.length !== 9 || nums.some(n => !Number.isInteger(n))) {
        return alert("Enter exactly 9 numbers.");
    }
    
    let check = await postData("/check", { state: nums });
    if (!check.ok) return alert(check.error);

    initialBoard = [...nums];
    resetGame();
    if (currentMode === 'benchmark') triggerAiSolve();
}

// Attach listeners
document.getElementById("giveUpBtn").onclick = () => handleGameEnd('gave_up');
document.getElementById("resetBtn").onclick = resetGame;
document.getElementById("playBtn").onclick = () => playbackTimer ? stopPlayback() : playPlayback();
document.getElementById("slider").oninput = (e) => { stopPlayback(); showPlaybackStep(Number(e.target.value)); };
document.getElementById("nextBtn").onclick = () => { stopPlayback(); showPlaybackStep(step + 1); };
document.getElementById("prevBtn").onclick = () => { stopPlayback(); showPlaybackStep(step - 1); };
document.getElementById("firstBtn").onclick = () => { stopPlayback(); showPlaybackStep(0); };
document.getElementById("lastBtn").onclick = () => { stopPlayback(); showPlaybackStep(states.length - 1); };

// Top Menu Controls
document.getElementById("modePlayBtn").onclick = () => setMode('play');
document.getElementById("modeBenchBtn").onclick = () => setMode('benchmark');
document.getElementById("setBoardBtn").onclick = setBoardFromInput;
document.getElementById("directSolveBtn").onclick = setBoardFromInput;
document.getElementById("randomBtn").onclick = async () => {
    let res = await fetch("/random");
    let data = await res.json();
    document.getElementById("stateInput").value = data.state.join(" ");
    setBoardFromInput();
};

// Speed Adjuster
document.getElementById("speed").querySelectorAll("button").forEach(btn => {
    btn.onclick = () => {
        playbackDelay = Number(btn.dataset.ms);
        document.getElementById("speed").querySelectorAll("button").forEach(b => b.classList.toggle("on", b === btn));
    };
});

// Init
drawBoard(currentBoard);
renderTable();