// =============================================
// VEIL 53
// =============================================


// =============================================
// HTML
// =============================================

const roomScreen =
    document.getElementById(
        "room-screen"
    );

const gameScreen =
    document.getElementById(
        "game-screen"
    );

const playerNameInput =
    document.getElementById(
        "player-name"
    );

const createRoomButton =
    document.getElementById(
        "create-room-button"
    );

const quickMatchButton =
    document.getElementById(
        "quick-match-button"
    );

const quickMatchTimer =
    document.getElementById(
        "quick-match-timer"
    );

const joinRoomButton =
    document.getElementById(
        "join-room-button"
    );

const cpuGameButton =
    document.getElementById(
        "cpu-game-button"
    );

const cpuLevelSelect =
    document.getElementById(
        "cpu-level"
    );

const roomIdInput =
    document.getElementById(
        "room-id"
    );

const message =
    document.getElementById(
        "message"
    );

const roomInfo =
    document.getElementById(
        "room-info"
    );

const playerInfo =
    document.getElementById(
        "player-info"
    );

const handContainer =
    document.getElementById(
        "hand-container"
    );

const gameStatus =
    document.getElementById(
        "game-status"
    );

const cpuActionSection =
    document.getElementById(
        "cpu-action-section"
    );

const cpuActionText =
    document.getElementById(
        "cpu-action-text"
    );


// =============================================
// QUESTION
// =============================================

const questionSection =
    document.getElementById(
        "question-section"
    );

const rankQuestionValue =
    document.getElementById(
        "rank-question-value"
    );

const moreThanValue =
    document.getElementById(
        "more-than-value"
    );

const lessThanValue =
    document.getElementById(
        "less-than-value"
    );

const questionEvenButton =
    document.getElementById(
        "question-even"
    );

const questionOddButton =
    document.getElementById(
        "question-odd"
    );

const questionFaceButton =
    document.getElementById(
        "question-face"
    );

const questionRankButton =
    document.getElementById(
        "question-rank"
    );

const questionMoreThanButton =
    document.getElementById(
        "question-more-than"
    );

const questionLessThanButton =
    document.getElementById(
        "question-less-than"
    );

const questionSpadeButton =
    document.getElementById(
        "question-spade"
    );

const questionHeartButton =
    document.getElementById(
        "question-heart"
    );

const questionDiamondButton =
    document.getElementById(
        "question-diamond"
    );

const questionClubButton =
    document.getElementById(
        "question-club"
    );

const questionJokerButton =
    document.getElementById(
        "question-joker"
    );

const questionButtons = [
    questionEvenButton,
    questionOddButton,
    questionFaceButton,
    questionRankButton,
    questionMoreThanButton,
    questionLessThanButton,
    questionSpadeButton,
    questionHeartButton,
    questionDiamondButton,
    questionClubButton,
    questionJokerButton
];


// =============================================
// GUESS
// =============================================

const guessSection =
    document.getElementById(
        "guess-section"
    );

const guessSuit =
    document.getElementById(
        "guess-suit"
    );

const guessRank =
    document.getElementById(
        "guess-rank"
    );

const guessCardButton =
    document.getElementById(
        "guess-card-button"
    );

const foundCount =
    document.getElementById(
        "found-count"
    );


// =============================================
// RESULT
// =============================================

const guessResultSection =
    document.getElementById(
        "guess-result-section"
    );

const guessResultText =
    document.getElementById(
        "guess-result-text"
    );

const guessResultCount =
    document.getElementById(
        "guess-result-count"
    );

const nextTurnButton =
    document.getElementById(
        "next-turn-button"
    );


// =============================================
// GAME OVER
// =============================================

const gameOverSection =
    document.getElementById(
        "game-over-section"
    );

const gameOverTitle =
    document.getElementById(
        "game-over-title"
    );

const gameOverMessage =
    document.getElementById(
        "game-over-message"
    );

const player1RevealedHand =
    document.getElementById(
        "player1-revealed-hand"
    );

const player2RevealedHand =
    document.getElementById(
        "player2-revealed-hand"
    );

const player1Title =
    document.getElementById(
        "player1-title"
    );

const player2Title =
    document.getElementById(
        "player2-title"
    );

const rematchButton =
    document.getElementById(
        "rematch-button"
    );

const leaveGameButton =
    document.getElementById(
        "leave-game-button"
    );


// =============================================
// STATE
// =============================================

let socket = null;

let currentRoomId = null;

let playerNumber = null;

let myTurn = false;

let currentPhase =
    "waiting";

let waitingForServer =
    false;

let currentFoundCount =
    0;

let gameMode =
    "pvp";

let roomConnectionState =
    "idle";

let currentCpuLevel =
    1;

let currentPlayerName =
    "";

let player1Name =
    "PLAYER 1";

let player2Name =
    "PLAYER 2";


// =============================================
// QUICK MATCH
// =============================================

let isQuickMatchWaiting =
    false;

let quickMatchStartTime =
    null;

let quickMatchTimerId =
    null;


// =============================================
// CPU
// =============================================

let lastCpuQuestion =
    "";

let lastCpuAnswer =
    "";

let lastCpuCandidateCount =
    null;

let lastCpuBeforeCandidateCount =
    null;

let lastCpuYesPredictionCount =
    null;

let lastCpuNoPredictionCount =
    null;

let lastCpuSplitScore =
    null;


// =============================================
// ROOM ID
// =============================================

const roomIdPattern =
    /^[A-HJ-NP-Z2-9]{4}$/;


// =============================================
// CPU NAME
// =============================================

function getCpuName() {

    return (
        `CPU Lv.${currentCpuLevel}`
    );
}


function getCpuLevelName() {

    if (
        currentCpuLevel === 1
    ) {

        return "RANDOM";
    }

    if (
        currentCpuLevel === 2
    ) {

        return "THINKER";
    }

    if (
        currentCpuLevel === 3
    ) {

        return "ANALYST";
    }

    return "CPU";
}


function getSelectedCpuLevel() {

    const level =
        Number(
            cpuLevelSelect.value
        );


    if (
        level === 3
    ) {

        return 3;
    }


    if (
        level === 2
    ) {

        return 2;
    }


    return 1;
}


// =============================================
// NAME
// =============================================

function getValidatedPlayerName() {

    const name =
        playerNameInput
        .value
        .trim();


    if (
        name.length === 0
    ) {

        message.textContent =
            "プレイヤー名を入力してください。";

        playerNameInput.focus();

        return null;
    }


    if (
        name.length > 12
    ) {

        message.textContent =
            "プレイヤー名は12文字以内で入力してください。";

        playerNameInput.focus();

        return null;
    }


    return name;
}


// =============================================
// FORMAT
// =============================================

function formatNumber(
    value
) {

    if (
        value === null
        ||
        value === undefined
    ) {

        return "-";
    }


    return Number(
        value
    ).toLocaleString(
        "ja-JP"
    );
}


// =============================================
// QUICK MATCH TIMER
// =============================================

function startQuickMatchTimer() {

    stopQuickMatchTimer();


    quickMatchStartTime =
        Date.now();


    quickMatchTimer.classList.remove(
        "hidden"
    );


    updateQuickMatchTimer();


    quickMatchTimerId =
        setInterval(
            updateQuickMatchTimer,
            1000
        );
}


function updateQuickMatchTimer() {

    if (
        quickMatchStartTime === null
    ) {

        return;
    }


    const elapsedSeconds =
        Math.floor(
            (
                Date.now()
                -
                quickMatchStartTime
            )
            /
            1000
        );


    const minutes =
        Math.floor(
            elapsedSeconds
            /
            60
        );


    const seconds =
        elapsedSeconds
        %
        60;


    const minuteText =
        String(
            minutes
        ).padStart(
            2,
            "0"
        );


    const secondText =
        String(
            seconds
        ).padStart(
            2,
            "0"
        );


    quickMatchTimer.textContent =
        `WAITING ${minuteText}:${secondText}`;
}


function stopQuickMatchTimer() {

    if (
        quickMatchTimerId !== null
    ) {

        clearInterval(
            quickMatchTimerId
        );


        quickMatchTimerId =
            null;
    }


    quickMatchStartTime =
        null;


    quickMatchTimer.classList.add(
        "hidden"
    );


    quickMatchTimer.textContent =
        "WAITING 00:00";
}


// =============================================
// ROOM CONTROLS
// =============================================

function updateRoomControls() {

    const busy =
        roomConnectionState !==
        "idle";


    createRoomButton.disabled =
        busy;

    joinRoomButton.disabled =
        busy;

    cpuGameButton.disabled =
        busy;

    roomIdInput.disabled =
        busy;

    cpuLevelSelect.disabled =
        busy;

    playerNameInput.disabled =
        busy;


    quickMatchButton.disabled =
        busy
        &&
        !isQuickMatchWaiting;


    createRoomButton.textContent =
        "ルームを作る";

    quickMatchButton.textContent =
        "QUICK MATCH";

    joinRoomButton.textContent =
        "ルームに参加";

    cpuGameButton.textContent =
        `CPU Lv.${getSelectedCpuLevel()}と対戦する`;


    if (
        isQuickMatchWaiting
    ) {

        quickMatchButton.disabled =
            false;

        quickMatchButton.textContent =
            "マッチングをキャンセル";

        return;
    }


    if (
        roomConnectionState ===
        "creating"
    ) {

        createRoomButton.textContent =
            "ルーム作成中...";

        return;
    }


    if (
        roomConnectionState ===
        "matchmaking"
    ) {

        quickMatchButton.textContent =
            "対戦相手を検索中...";

        return;
    }


    if (
        roomConnectionState ===
        "cpu-creating"
    ) {

        cpuGameButton.textContent =
            "CPU準備中...";

        return;
    }


    if (
        roomConnectionState ===
        "connecting"
    ) {

        createRoomButton.textContent =
            "接続中...";

        quickMatchButton.textContent =
            "接続中...";

        joinRoomButton.textContent =
            "接続中...";

        cpuGameButton.textContent =
            "接続中...";

        return;
    }


    if (
        roomConnectionState ===
        "joined"
    ) {

        createRoomButton.textContent =
            "参加済み";

        quickMatchButton.textContent =
            "対戦中";

        joinRoomButton.textContent =
            "参加済み";

        cpuGameButton.textContent =
            "対戦中";
    }
}


// =============================================
// CREATE ROOM
// =============================================

createRoomButton.addEventListener(
    "click",
    async () => {

        if (
            roomConnectionState !==
            "idle"
        ) {

            return;
        }


        const name =
            getValidatedPlayerName();


        if (
            name === null
        ) {

            return;
        }


        currentPlayerName =
            name;

        gameMode =
            "pvp";

        isQuickMatchWaiting =
            false;

        stopQuickMatchTimer();

        roomConnectionState =
            "creating";

        updateRoomControls();

        message.textContent =
            "ルームを作成しています...";


        try {

            const response =
                await fetch(
                    "/rooms",
                    {
                        method:
                            "POST"
                    }
                );


            if (
                !response.ok
            ) {

                throw new Error(
                    "ルーム作成失敗"
                );
            }


            const data =
                await response.json();


            currentRoomId =
                data.room_id;


            roomConnectionState =
                "connecting";


            updateRoomControls();


            message.textContent =
                `ルームID：${currentRoomId}\n`
                +
                "接続しています...";


            connectWebSocket(
                currentRoomId
            );

        }

        catch (error) {

            console.error(
                error
            );


            roomConnectionState =
                "idle";

            currentRoomId =
                null;

            updateRoomControls();


            message.textContent =
                "ルームを作成できませんでした。";
        }
    }
);


// =============================================
// QUICK MATCH
// =============================================

quickMatchButton.addEventListener(
    "click",
    async () => {

        if (
            isQuickMatchWaiting
        ) {

            await cancelQuickMatch();

            return;
        }


        if (
            roomConnectionState !==
            "idle"
        ) {

            return;
        }


        const name =
            getValidatedPlayerName();


        if (
            name === null
        ) {

            return;
        }


        currentPlayerName =
            name;

        gameMode =
            "pvp";

        roomConnectionState =
            "matchmaking";

        updateRoomControls();


        message.textContent =
            "対戦相手を探しています...";


        try {

            const response =
                await fetch(
                    "/matchmaking",
                    {
                        method:
                            "POST"
                    }
                );


            if (
                !response.ok
            ) {

                throw new Error(
                    "マッチング失敗"
                );
            }


            const data =
                await response.json();


            currentRoomId =
                data.room_id;


            if (
                !data.matched
            ) {

                isQuickMatchWaiting =
                    true;


                startQuickMatchTimer();


                message.textContent =
                    "対戦相手を探しています...\n\n"
                    +
                    "キャンセルする場合は"
                    +
                    "ボタンを押してください。";
            }


            else {

                isQuickMatchWaiting =
                    false;


                stopQuickMatchTimer();


                message.textContent =
                    "対戦相手が見つかりました！\n"
                    +
                    "接続しています...";
            }


            roomConnectionState =
                "connecting";


            updateRoomControls();


            connectWebSocket(
                currentRoomId
            );

        }

        catch (error) {

            console.error(
                error
            );


            isQuickMatchWaiting =
                false;


            stopQuickMatchTimer();


            roomConnectionState =
                "idle";


            currentRoomId =
                null;


            updateRoomControls();


            message.textContent =
                "マッチングを開始できませんでした。";
        }
    }
);


// =============================================
// QUICK MATCH CANCEL
// =============================================

async function cancelQuickMatch() {

    if (
        !isQuickMatchWaiting
        ||
        currentRoomId === null
    ) {

        return;
    }


    const cancellingRoomId =
        currentRoomId;


    quickMatchButton.disabled =
        true;


    quickMatchButton.textContent =
        "キャンセル中...";


    try {

        const response =
            await fetch(
                `/matchmaking/cancel/${encodeURIComponent(
                    cancellingRoomId
                )}`,
                {
                    method:
                        "POST"
                }
            );


        if (
            !response.ok
        ) {

            throw new Error(
                "キャンセル失敗"
            );
        }


        const data =
            await response.json();


        if (
            !data.cancelled
        ) {

            isQuickMatchWaiting =
                false;


            stopQuickMatchTimer();


            updateRoomControls();


            message.textContent =
                "対戦相手が見つかったため、"
                +
                "キャンセルできませんでした。";


            return;
        }


        isQuickMatchWaiting =
            false;


        stopQuickMatchTimer();


        closeSocketWithoutLeave();


        currentRoomId =
            null;

        playerNumber =
            null;

        roomConnectionState =
            "idle";

        waitingForServer =
            false;

        myTurn =
            false;

        currentPhase =
            "waiting";


        updateRoomControls();

        updateControls();


        message.textContent =
            "QUICK MATCHをキャンセルしました。";

    }

    catch (error) {

        console.error(
            error
        );


        isQuickMatchWaiting =
            true;


        updateRoomControls();


        message.textContent =
            "キャンセルできませんでした。\n"
            +
            "もう一度試してください。";
    }
}


// =============================================
// CPU
// =============================================

cpuGameButton.addEventListener(
    "click",
    async () => {

        if (
            roomConnectionState !==
            "idle"
        ) {

            return;
        }


        const name =
            getValidatedPlayerName();


        if (
            name === null
        ) {

            return;
        }


        currentPlayerName =
            name;


        currentCpuLevel =
            getSelectedCpuLevel();


        gameMode =
            "cpu";


        isQuickMatchWaiting =
            false;


        stopQuickMatchTimer();


        roomConnectionState =
            "cpu-creating";


        updateRoomControls();


        message.textContent =
            `${getCpuName()}を準備しています...`;


        try {

            const response =
                await fetch(
                    `/cpu-rooms?level=${currentCpuLevel}`,
                    {
                        method:
                            "POST"
                    }
                );


            if (
                !response.ok
            ) {

                throw new Error(
                    "CPUルーム作成失敗"
                );
            }


            const data =
                await response.json();


            currentRoomId =
                data.room_id;


            if (
                data.cpu_level
            ) {

                currentCpuLevel =
                    Number(
                        data.cpu_level
                    );
            }


            roomConnectionState =
                "connecting";


            updateRoomControls();


            message.textContent =
                `${getCpuName()}に接続しています...`;


            connectWebSocket(
                currentRoomId
            );

        }

        catch (error) {

            console.error(
                error
            );


            roomConnectionState =
                "idle";

            currentRoomId =
                null;

            gameMode =
                "pvp";


            updateRoomControls();


            message.textContent =
                "CPU対戦を開始できませんでした。";
        }
    }
);


// =============================================
// JOIN
// =============================================

joinRoomButton.addEventListener(
    "click",
    () => {

        if (
            roomConnectionState !==
            "idle"
        ) {

            return;
        }


        const name =
            getValidatedPlayerName();


        if (
            name === null
        ) {

            return;
        }


        currentPlayerName =
            name;


        const roomId =
            roomIdInput
            .value
            .trim()
            .toUpperCase();


        if (
            roomId === ""
        ) {

            message.textContent =
                "ルームIDを入力してください。";

            roomIdInput.focus();

            return;
        }


        if (
            roomId.length !== 4
        ) {

            message.textContent =
                "ルームIDは4文字です。";

            roomIdInput.focus();

            return;
        }


        if (
            !roomIdPattern.test(
                roomId
            )
        ) {

            message.textContent =
                "ルームIDの形式が正しくありません。";

            roomIdInput.focus();

            return;
        }


        gameMode =
            "pvp";


        isQuickMatchWaiting =
            false;


        stopQuickMatchTimer();


        currentRoomId =
            roomId;


        roomConnectionState =
            "connecting";


        updateRoomControls();


        message.textContent =
            `ルーム ${roomId} に接続しています...`;


        connectWebSocket(
            currentRoomId
        );
    }
);


roomIdInput.addEventListener(
    "keydown",
    (event) => {

        if (
            event.key ===
            "Enter"
        ) {

            joinRoomButton.click();
        }
    }
);


cpuLevelSelect.addEventListener(
    "change",
    () => {

        if (
            roomConnectionState !==
            "idle"
        ) {

            return;
        }


        currentCpuLevel =
            getSelectedCpuLevel();


        updateRoomControls();
    }
);


// =============================================
// WEBSOCKET
// =============================================

function connectWebSocket(
    roomId
) {

    closeSocketWithoutLeave();


    const protocol =
        location.protocol ===
        "https:"
            ? "wss"
            : "ws";


    const encodedName =
        encodeURIComponent(
            currentPlayerName
        );


    const socketUrl =
        `${protocol}://${location.host}`
        +
        `/ws/${roomId}`
        +
        `?name=${encodedName}`;


    const newSocket =
        new WebSocket(
            socketUrl
        );


    socket =
        newSocket;


    newSocket.addEventListener(
        "open",
        () => {

            if (
                socket !== newSocket
            ) {

                return;
            }


            if (
                isQuickMatchWaiting
            ) {

                message.textContent =
                    "対戦相手を探しています...\n\n"
                    +
                    "キャンセルする場合は"
                    +
                    "ボタンを押してください。";

                return;
            }


            message.textContent =
                gameMode ===
                "cpu"
                    ?
                    `${getCpuName()}に接続しました。`
                    :
                    `ルームID：${roomId}\n`
                    +
                    "サーバーに接続しました。";
        }
    );


    newSocket.addEventListener(
        "message",
        (event) => {

            if (
                socket !== newSocket
            ) {

                return;
            }


            try {

                const data =
                    JSON.parse(
                        event.data
                    );


                handleServerMessage(
                    data
                );

            }

            catch (error) {

                console.error(
                    error
                );


                waitingForServer =
                    false;


                updateControls();


                message.textContent =
                    "受信データを解析できませんでした。";
            }
        }
    );


    newSocket.addEventListener(
        "close",
        () => {

            if (
                socket !== newSocket
            ) {

                return;
            }


            socket =
                null;


            if (
                roomConnectionState ===
                "connecting"
            ) {

                isQuickMatchWaiting =
                    false;


                stopQuickMatchTimer();


                roomConnectionState =
                    "idle";

                currentRoomId =
                    null;

                playerNumber =
                    null;

                waitingForServer =
                    false;

                myTurn =
                    false;

                currentPhase =
                    "waiting";


                updateRoomControls();

                updateControls();


                message.textContent =
                    "ルームに接続できませんでした。";


                return;
            }


            if (
                currentPhase !==
                "finished"
                &&
                roomConnectionState ===
                "joined"
            ) {

                returnToRoomScreen(
                    "サーバーとの接続が切れました。\n\n"
                    +
                    "もう一度対戦を開始してください。"
                );
            }
        }
    );


    newSocket.addEventListener(
        "error",
        (error) => {

            console.error(
                error
            );
        }
    );
}


// =============================================
// SERVER MESSAGE
// =============================================

function handleServerMessage(
    data
) {

    if (
        data.type ===
        "error"
        &&
        [
            "ROOM_NOT_FOUND",
            "ROOM_FULL",
            "INVALID_ROOM_ID",
            "INVALID_PLAYER_NAME"
        ].includes(
            data.code
        )
    ) {

        const oldSocket =
            socket;


        socket =
            null;


        if (
            oldSocket !== null
        ) {

            oldSocket.close();
        }


        isQuickMatchWaiting =
            false;


        stopQuickMatchTimer();


        roomConnectionState =
            "idle";

        currentRoomId =
            null;

        playerNumber =
            null;


        updateRoomControls();


        message.textContent =
            data.message
            ||
            "ルームに接続できませんでした。";


        return;
    }


    // =========================================
    // PLAYER NUMBER
    // =========================================

    if (
        data.type ===
        "player_number"
    ) {

        playerNumber =
            data.player;


        if (
            data.player_name
        ) {

            currentPlayerName =
                data.player_name;
        }


        if (
            data.room_id
        ) {

            currentRoomId =
                data.room_id;
        }


        if (
            data.mode
        ) {

            gameMode =
                data.mode;
        }


        if (
            data.cpu_level
        ) {

            currentCpuLevel =
                Number(
                    data.cpu_level
                );
        }


        roomConnectionState =
            "joined";


        updateRoomControls();


        roomInfo.textContent =
            gameMode ===
            "cpu"
                ?
                `${getCpuName()} ${getCpuLevelName()}`
                :
                `Room ${currentRoomId}`;


        playerInfo.textContent =
            gameMode ===
            "cpu"
                ?
                `${currentPlayerName} vs ${getCpuName()}`
                :
                `${currentPlayerName} / Player ${playerNumber}`;


        myTurn =
            false;

        currentPhase =
            "waiting";

        waitingForServer =
            false;


        updateControls();


        if (
            isQuickMatchWaiting
        ) {

            message.textContent =
                "対戦相手を探しています...\n\n"
                +
                "マッチングをやめる場合は"
                +
                "「マッチングをキャンセル」を"
                +
                "押してください。";
        }

        else {

            message.textContent =
                gameMode ===
                "cpu"
                    ?
                    `${currentPlayerName} vs ${getCpuName()}\n`
                    +
                    "対戦を開始します..."
                    :
                    `ルームID：${currentRoomId}\n`
                    +
                    `${currentPlayerName} / Player ${playerNumber}\n\n`
                    +
                    "相手を待っています...";
        }


        return;
    }


    // =========================================
    // GAME START
    // =========================================

    if (
        data.type ===
        "game_start"
    ) {

        isQuickMatchWaiting =
            false;


        stopQuickMatchTimer();


        roomConnectionState =
            "joined";


        updateRoomControls();


        showGameScreen();


        playerNumber =
            data.player;


        if (
            data.mode
        ) {

            gameMode =
                data.mode;
        }


        if (
            data.cpu_level
        ) {

            currentCpuLevel =
                Number(
                    data.cpu_level
                );
        }


        player1Name =
            data.player1_name
            ||
            "PLAYER 1";


        player2Name =
            data.player2_name
            ||
            "PLAYER 2";


        currentPlayerName =
            playerNumber === 1
                ?
                player1Name
                :
                player2Name;


        myTurn =
            Boolean(
                data.your_turn
            );


        currentPhase =
            data.phase;


        waitingForServer =
            false;


        currentFoundCount =
            0;


        lastCpuQuestion =
            "";

        lastCpuAnswer =
            "";

        lastCpuCandidateCount =
            data.candidate_count
            ??
            null;

        lastCpuBeforeCandidateCount =
            null;

        lastCpuYesPredictionCount =
            null;

        lastCpuNoPredictionCount =
            null;

        lastCpuSplitScore =
            null;


        cpuActionSection.classList.add(
            "hidden"
        );


        cpuActionText.textContent =
            "";


        roomInfo.textContent =
            gameMode ===
            "cpu"
                ?
                `${getCpuName()} ${getCpuLevelName()}`
                :
                `Room ${currentRoomId}`;


        playerInfo.textContent =
            `${player1Name} vs ${player2Name}`;


        player1Title.textContent =
            player1Name;


        player2Title.textContent =
            player2Name;


        displayHand(
            data.hand,
            handContainer
        );


        resetGuessInput();


        guessResultText.textContent =
            "";


        guessResultSection.classList.add(
            "hidden"
        );


        gameOverSection.classList.add(
            "hidden"
        );


        rematchButton.disabled =
            false;


        updateFoundCount();

        updateGameStatus();

        updateControls();


        message.textContent =
            myTurn
                ?
                `${currentPlayerName}のターンです。\n`
                +
                "質問を1つ選んでください。"
                :
                `${
                    playerNumber === 1
                        ?
                        player2Name
                        :
                        player1Name
                }のターンです。`;


        return;
    }


    // =========================================
    // QUESTION RESULT
    // =========================================

    if (
        data.type ===
        "question_result"
    ) {

        waitingForServer =
            false;


        currentPhase =
            "guess";


        const answerText =
            data.answer
                ?
                "YES"
                :
                "NO";


        message.textContent =
            `${data.question}\n\n`
            +
            `答え：${answerText}`;


        updateGameStatus();

        updateControls();


        return;
    }


    // =========================================
    // GUESS RESULT
    // =========================================

    if (
        data.type ===
        "guess_result"
    ) {

        waitingForServer =
            false;


        currentPhase =
            "result";


        currentFoundCount =
            data.found_count;


        updateFoundCount();


        guessResultText.textContent =
            data.correct
                ?
                `${data.guess}\n\n🎉 当たり！`
                :
                `${data.guess}\n\nはずれ！`;


        guessResultCount.textContent =
            `現在 ${currentFoundCount} / 3 枚正解`;


        gameStatus.textContent =
            "予想結果を確認してください";


        message.textContent =
            "結果を確認したら"
            +
            "「NEXT」を押してください。";


        updateControls();


        return;
    }


    // =========================================
    // CPU QUESTION
    // =========================================

    if (
        data.type ===
        "cpu_question"
    ) {

        if (
            data.cpu_level
        ) {

            currentCpuLevel =
                Number(
                    data.cpu_level
                );
        }


        lastCpuQuestion =
            data.question;


        lastCpuAnswer =
            data.answer
                ?
                "YES"
                :
                "NO";


        lastCpuCandidateCount =
            data.candidate_count
            ??
            null;


        lastCpuBeforeCandidateCount =
            data.before_candidate_count
            ??
            null;


        lastCpuYesPredictionCount =
            data.yes_prediction_count
            ??
            null;


        lastCpuNoPredictionCount =
            data.no_prediction_count
            ??
            null;


        lastCpuSplitScore =
            data.split_score
            ??
            null;


        cpuActionSection.classList.remove(
            "hidden"
        );


        if (
            currentCpuLevel ===
            1
        ) {

            cpuActionText.textContent =
                `CPU Lv.1の質問\n\n`
                +
                `${lastCpuQuestion}\n\n`
                +
                `答え：${lastCpuAnswer}`;


            gameStatus.textContent =
                "CPU Lv.1が考えています...";


            message.textContent =
                "CPU Lv.1がランダムに"
                +
                "カードを予想します...";


            return;
        }


        if (
            currentCpuLevel ===
            2
        ) {

            let candidateText =
                "";


            if (
                lastCpuCandidateCount !==
                null
            ) {

                candidateText =
                    "\n\n推理候補："
                    +
                    `${formatNumber(
                        lastCpuCandidateCount
                    )} 通り`;
            }


            cpuActionText.textContent =
                `CPU Lv.2の質問\n\n`
                +
                `${lastCpuQuestion}\n\n`
                +
                `答え：${lastCpuAnswer}`
                +
                candidateText;


            gameStatus.textContent =
                "CPU Lv.2が推理しています...";


            message.textContent =
                "質問結果から候補手札を"
                +
                "絞り込んでいます...";


            return;
        }


        if (
            currentCpuLevel ===
            3
        ) {

            let analysisText =
                "";


            if (
                lastCpuBeforeCandidateCount !==
                null
            ) {

                analysisText +=
                    "\n\n質問前候補："
                    +
                    `${formatNumber(
                        lastCpuBeforeCandidateCount
                    )} 通り`;
            }


            if (
                lastCpuYesPredictionCount !==
                null
                &&
                lastCpuNoPredictionCount !==
                null
            ) {

                analysisText +=
                    "\nYES予測："
                    +
                    `${formatNumber(
                        lastCpuYesPredictionCount
                    )} 通り`
                    +
                    "\nNO予測："
                    +
                    `${formatNumber(
                        lastCpuNoPredictionCount
                    )} 通り`;
            }


            if (
                lastCpuSplitScore !==
                null
            ) {

                analysisText +=
                    "\n分割差："
                    +
                    `${formatNumber(
                        lastCpuSplitScore
                    )}`;
            }


            let afterText =
                "\n\n答え："
                +
                `${lastCpuAnswer}`;


            if (
                lastCpuCandidateCount !==
                null
            ) {

                afterText +=
                    "\n\n残り候補："
                    +
                    `${formatNumber(
                        lastCpuCandidateCount
                    )} 通り`;
            }


            cpuActionText.textContent =
                "CPU Lv.3 ANALYST\n\n"
                +
                "最も情報量の高い質問を選択\n\n"
                +
                `${lastCpuQuestion}`
                +
                analysisText
                +
                afterText;


            gameStatus.textContent =
                "CPU Lv.3が分析しています...";


            message.textContent =
                "候補を最も半分に近づける質問を"
                +
                "計算して推理しています...";


            return;
        }
    }


    // =========================================
    // CPU GUESS RESULT
    // =========================================

    if (
        data.type ===
        "cpu_guess_result"
    ) {

        if (
            data.cpu_level
        ) {

            currentCpuLevel =
                Number(
                    data.cpu_level
                );
        }


        const resultText =
            data.correct
                ?
                "🎯 当たり！"
                :
                "はずれ！";


        lastCpuCandidateCount =
            data.candidate_count
            ??
            lastCpuCandidateCount;


        cpuActionSection.classList.remove(
            "hidden"
        );


        let candidateText =
            "";


        if (
            (
                currentCpuLevel === 2
                ||
                currentCpuLevel === 3
            )
            &&
            lastCpuCandidateCount !==
            null
        ) {

            candidateText =
                "\n\n残り候補："
                +
                `${formatNumber(
                    lastCpuCandidateCount
                )} 通り`;
        }


        let level3AnalysisText =
            "";


        if (
            currentCpuLevel ===
            3
        ) {

            if (
                lastCpuBeforeCandidateCount !==
                null
            ) {

                level3AnalysisText +=
                    "\n\n質問時の分析"
                    +
                    "\n質問前："
                    +
                    `${formatNumber(
                        lastCpuBeforeCandidateCount
                    )} 通り`;
            }


            if (
                lastCpuYesPredictionCount !==
                null
                &&
                lastCpuNoPredictionCount !==
                null
            ) {

                level3AnalysisText +=
                    "\nYES予測："
                    +
                    `${formatNumber(
                        lastCpuYesPredictionCount
                    )}`
                    +
                    "\nNO予測："
                    +
                    `${formatNumber(
                        lastCpuNoPredictionCount
                    )}`;
            }
        }


        cpuActionText.textContent =
            `${getCpuName()}の質問\n\n`
            +
            `${lastCpuQuestion}\n`
            +
            `答え：${lastCpuAnswer}`
            +
            level3AnalysisText
            +
            "\n\n"
            +
            `${getCpuName()}の予想\n\n`
            +
            `${data.guess}\n\n`
            +
            resultText
            +
            "\n\n"
            +
            `CPU：${data.found_count} / 3 枚正解`
            +
            candidateText;


        gameStatus.textContent =
            `${getCpuName()}の予想結果`;


        message.textContent =
            data.correct
                ?
                `${getCpuName()}がカードを1枚当てました。`
                :
                `${getCpuName()}の予想は外れました。`;


        return;
    }


    // =========================================
    // TURN CHANGED
    // =========================================

    if (
        data.type ===
        "turn_changed"
    ) {

        if (
            data.cpu_level
        ) {

            currentCpuLevel =
                Number(
                    data.cpu_level
                );
        }


        myTurn =
            Boolean(
                data.your_turn
            );


        currentPhase =
            data.phase;


        waitingForServer =
            false;


        resetGuessInput();

        updateGameStatus();

        updateControls();


        if (
            myTurn
        ) {

            message.textContent =
                `${currentPlayerName}のターンです。\n`
                +
                "質問を1つ選んでください。";
        }

        else {

            const opponentName =
                playerNumber === 1
                    ?
                    player2Name
                    :
                    player1Name;


            message.textContent =
                `${opponentName}のターンです...`;
        }


        return;
    }


    // =========================================
    // GAME OVER
    // =========================================

    if (
        data.type ===
        "game_over"
    ) {

        isQuickMatchWaiting =
            false;


        stopQuickMatchTimer();


        myTurn =
            false;

        currentPhase =
            "finished";

        waitingForServer =
            false;


        questionSection.classList.add(
            "hidden"
        );

        guessSection.classList.add(
            "hidden"
        );

        guessResultSection.classList.add(
            "hidden"
        );

        cpuActionSection.classList.add(
            "hidden"
        );


        gameOverSection.classList.remove(
            "hidden"
        );


        player1Name =
            data.player1_name
            ||
            player1Name;


        player2Name =
            data.player2_name
            ||
            player2Name;


        player1Title.textContent =
            player1Name;

        player2Title.textContent =
            player2Name;


        displayHand(
            data.player1_hand,
            player1RevealedHand
        );


        displayHand(
            data.player2_hand,
            player2RevealedHand
        );


        if (
            data.winner ===
            playerNumber
        ) {

            gameOverTitle.textContent =
                "YOU WIN";


            gameOverMessage.textContent =
                `${currentPlayerName}の勝利！\n`
                +
                "相手の3枚すべてを見破りました。";


            gameStatus.textContent =
                `${currentPlayerName}の勝ち！`;


            message.textContent =
                `🎉 ${currentPlayerName}の勝ちです！`;
        }

        else {

            const winnerName =
                data.winner === 1
                    ?
                    player1Name
                    :
                    player2Name;


            gameOverTitle.textContent =
                gameMode ===
                "cpu"
                    ?
                    "CPU WINS"
                    :
                    "YOU LOSE";


            gameOverMessage.textContent =
                `${winnerName}が3枚すべてを見破りました。`;


            gameStatus.textContent =
                `${winnerName}の勝利`;


            message.textContent =
                `${winnerName}の勝ちです。`;
        }


        updateControls();


        return;
    }


    if (
        data.type ===
        "rematch_waiting"
    ) {

        message.textContent =
            "相手の再戦希望を待っています...";

        return;
    }


    if (
        data.type ===
        "opponent_disconnected"
    ) {

        closeSocketWithoutLeave();


        returnToRoomScreen(
            "相手との接続が切れました。\n"
            +
            "対戦を終了しました。"
        );


        return;
    }


    if (
        data.type ===
        "opponent_left"
    ) {

        closeSocketWithoutLeave();


        returnToRoomScreen(
            "相手がゲームを終了しました。"
        );


        return;
    }


    if (
        data.type ===
        "error"
    ) {

        waitingForServer =
            false;


        updateControls();


        message.textContent =
            data.message
            ||
            "エラーが発生しました。";


        return;
    }
}


// =============================================
// CONTROLS
// =============================================

function updateControls() {

    updateQuestionControls();

    updateGuessControls();

    updateResultControls();
}


function updateQuestionControls() {

    const canAsk =
        myTurn
        &&
        currentPhase ===
        "question"
        &&
        !waitingForServer;


    if (
        canAsk
    ) {

        questionSection.classList.remove(
            "hidden"
        );
    }

    else {

        questionSection.classList.add(
            "hidden"
        );
    }


    questionButtons.forEach(
        (button) => {

            if (
                button !== null
            ) {

                button.disabled =
                    !canAsk;
            }
        }
    );


    rankQuestionValue.disabled =
        !canAsk;

    moreThanValue.disabled =
        !canAsk;

    lessThanValue.disabled =
        !canAsk;
}


function updateGuessControls() {

    const canGuess =
        myTurn
        &&
        currentPhase ===
        "guess"
        &&
        !waitingForServer;


    if (
        canGuess
    ) {

        guessSection.classList.remove(
            "hidden"
        );
    }

    else {

        guessSection.classList.add(
            "hidden"
        );
    }


    guessSuit.disabled =
        !canGuess;


    if (
        !canGuess
    ) {

        guessRank.disabled =
            true;
    }

    else {

        updateGuessRankState();
    }


    guessCardButton.disabled =
        !canGuess;
}


function updateResultControls() {

    const showResult =
        myTurn
        &&
        currentPhase ===
        "result";


    if (
        showResult
    ) {

        guessResultSection.classList.remove(
            "hidden"
        );
    }

    else {

        guessResultSection.classList.add(
            "hidden"
        );
    }


    nextTurnButton.disabled =
        !showResult
        ||
        waitingForServer;
}


// =============================================
// SCREEN
// =============================================

function showGameScreen() {

    roomScreen.classList.add(
        "hidden"
    );


    gameScreen.classList.remove(
        "hidden"
    );
}


function showRoomScreen() {

    gameScreen.classList.add(
        "hidden"
    );


    roomScreen.classList.remove(
        "hidden"
    );
}


// =============================================
// STATUS
// =============================================

function updateGameStatus() {

    if (
        currentPhase ===
        "finished"
    ) {

        return;
    }


    if (
        !myTurn
    ) {

        const opponentName =
            gameMode ===
            "cpu"
                ?
                getCpuName()
                :
                (
                    playerNumber === 1
                        ?
                        player2Name
                        :
                        player1Name
                );


        gameStatus.textContent =
            `${opponentName}のターンです`;


        return;
    }


    if (
        currentPhase ===
        "question"
    ) {

        gameStatus.textContent =
            `${currentPlayerName}のターン：質問を選んでください`;

        return;
    }


    if (
        currentPhase ===
        "guess"
    ) {

        gameStatus.textContent =
            "相手のカードを1枚予想してください";

        return;
    }


    if (
        currentPhase ===
        "result"
    ) {

        gameStatus.textContent =
            "予想結果を確認してください";

        return;
    }


    gameStatus.textContent =
        "ゲーム進行中";
}


// =============================================
// FOUND
// =============================================

function updateFoundCount() {

    foundCount.textContent =
        `現在 ${currentFoundCount} / 3 枚正解`;


    guessResultCount.textContent =
        `現在 ${currentFoundCount} / 3 枚正解`;
}


// =============================================
// JOKER
// =============================================

guessSuit.addEventListener(
    "change",
    () => {

        updateGuessRankState();
    }
);


function updateGuessRankState() {

    if (
        guessSuit.value ===
        "JOKER"
    ) {

        guessRank.disabled =
            true;


        guessRank.value =
            "";


        return;
    }


    guessRank.disabled =
        !(
            myTurn
            &&
            currentPhase ===
            "guess"
            &&
            !waitingForServer
        );
}


function resetGuessInput() {

    guessSuit.value =
        "";


    guessRank.value =
        "";


    guessRank.disabled =
        true;
}


// =============================================
// QUESTION SEND
// =============================================

function canSendQuestion() {

    if (
        socket === null
        ||
        socket.readyState !==
        WebSocket.OPEN
    ) {

        message.textContent =
            "サーバーに接続されていません。";


        return false;
    }


    if (
        waitingForServer
        ||
        !myTurn
        ||
        currentPhase !==
        "question"
    ) {

        return false;
    }


    return true;
}


function sendQuestion(
    questionId,
    extraData = {}
) {

    if (
        !canSendQuestion()
    ) {

        return;
    }


    waitingForServer =
        true;


    updateControls();


    message.textContent =
        "質問しています...";


    socket.send(
        JSON.stringify({
            type:
                "question",

            question_id:
                questionId,

            ...extraData
        })
    );
}


// =============================================
// VALIDATION
// =============================================

function validateRankQuestion() {

    const rank =
        rankQuestionValue
        .value
        .trim()
        .toUpperCase();


    if (
        rank === ""
        ||
        !isValidRank(
            rank
        )
    ) {

        message.textContent =
            "ランクを選択してください。";


        return null;
    }


    return rank;
}


function validateNumberQuestion(
    inputElement
) {

    const rawValue =
        inputElement
        .value
        .trim();


    const number =
        Number(
            rawValue
        );


    if (
        rawValue === ""
        ||
        !Number.isInteger(
            number
        )
        ||
        number < 1
        ||
        number > 13
    ) {

        message.textContent =
            "1〜13の整数を入力してください。";


        return null;
    }


    return number;
}


// =============================================
// QUESTION EVENTS
// =============================================

questionEvenButton.addEventListener(
    "click",
    () => sendQuestion(1)
);


questionOddButton.addEventListener(
    "click",
    () => sendQuestion(2)
);


questionFaceButton.addEventListener(
    "click",
    () => sendQuestion(3)
);


questionRankButton.addEventListener(
    "click",
    () => {

        const rank =
            validateRankQuestion();


        if (
            rank === null
        ) {

            return;
        }


        sendQuestion(
            4,
            {
                rank:
                    rank
            }
        );
    }
);


questionMoreThanButton.addEventListener(
    "click",
    () => {

        const number =
            validateNumberQuestion(
                moreThanValue
            );


        if (
            number === null
        ) {

            return;
        }


        sendQuestion(
            5,
            {
                number:
                    number
            }
        );
    }
);


questionLessThanButton.addEventListener(
    "click",
    () => {

        const number =
            validateNumberQuestion(
                lessThanValue
            );


        if (
            number === null
        ) {

            return;
        }


        sendQuestion(
            6,
            {
                number:
                    number
            }
        );
    }
);


questionSpadeButton.addEventListener(
    "click",
    () => sendQuestion(7)
);


questionHeartButton.addEventListener(
    "click",
    () => sendQuestion(8)
);


questionDiamondButton.addEventListener(
    "click",
    () => sendQuestion(9)
);


questionClubButton.addEventListener(
    "click",
    () => sendQuestion(10)
);


questionJokerButton.addEventListener(
    "click",
    () => sendQuestion(11)
);


// =============================================
// GUESS
// =============================================

guessCardButton.addEventListener(
    "click",
    sendGuess
);


function sendGuess() {

    if (
        socket === null
        ||
        socket.readyState !==
        WebSocket.OPEN
        ||
        waitingForServer
        ||
        !myTurn
        ||
        currentPhase !==
        "guess"
    ) {

        return;
    }


    const suit =
        guessSuit.value;


    if (
        suit === ""
    ) {

        message.textContent =
            "スートを選択してください。";


        return;
    }


    let data;


    if (
        suit ===
        "JOKER"
    ) {

        data = {
            type:
                "guess_card",

            suit:
                "JOKER"
        };
    }

    else {

        const rank =
            guessRank
            .value
            .trim()
            .toUpperCase();


        if (
            !isValidRank(
                rank
            )
        ) {

            message.textContent =
                "ランクを選択してください。";


            return;
        }


        data = {
            type:
                "guess_card",

            suit:
                suit,

            rank:
                rank
        };
    }


    waitingForServer =
        true;


    updateControls();


    message.textContent =
        "予想しています...";


    socket.send(
        JSON.stringify(
            data
        )
    );
}


// =============================================
// NEXT
// =============================================

nextTurnButton.addEventListener(
    "click",
    continueAfterGuess
);


function continueAfterGuess() {

    if (
        socket === null
        ||
        socket.readyState !==
        WebSocket.OPEN
        ||
        currentPhase !==
        "result"
        ||
        !myTurn
        ||
        waitingForServer
    ) {

        return;
    }


    waitingForServer =
        true;


    updateControls();


    message.textContent =
        gameMode ===
        "cpu"
            ?
            `${getCpuName()}のターンへ進みます...`
            :
            "次のターンへ進みます...";


    socket.send(
        JSON.stringify({
            type:
                "continue_after_guess"
        })
    );
}


// =============================================
// REMATCH
// =============================================

rematchButton.addEventListener(
    "click",
    () => {

        if (
            socket === null
            ||
            socket.readyState !==
            WebSocket.OPEN
        ) {

            return;
        }


        rematchButton.disabled =
            true;


        message.textContent =
            gameMode ===
            "cpu"
                ?
                `${getCpuName()}と再戦します...`
                :
                "再戦をリクエストしました。";


        socket.send(
            JSON.stringify({
                type:
                    "rematch_request"
            })
        );
    }
);


// =============================================
// LEAVE
// =============================================

leaveGameButton.addEventListener(
    "click",
    () => {

        if (
            socket !== null
            &&
            socket.readyState ===
            WebSocket.OPEN
        ) {

            try {

                socket.send(
                    JSON.stringify({
                        type:
                            "leave_game"
                    })
                );

            }

            catch (error) {

                console.error(
                    error
                );
            }
        }


        closeSocketWithoutLeave();


        returnToRoomScreen(
            "ゲームを終了しました。"
        );
    }
);


// =============================================
// SOCKET
// =============================================

function closeSocketWithoutLeave() {

    if (
        socket === null
    ) {

        return;
    }


    const oldSocket =
        socket;


    socket =
        null;


    try {

        oldSocket.close();

    }

    catch (error) {

        console.error(
            error
        );
    }
}


// =============================================
// RETURN
// =============================================

function returnToRoomScreen(
    text
) {

    closeSocketWithoutLeave();


    resetBattleState();


    showRoomScreen();


    message.textContent =
        text;
}


// =============================================
// RESET
// =============================================

function resetBattleState() {

    socket =
        null;

    currentRoomId =
        null;

    playerNumber =
        null;

    myTurn =
        false;

    currentPhase =
        "waiting";

    waitingForServer =
        false;

    currentFoundCount =
        0;

    gameMode =
        "pvp";

    roomConnectionState =
        "idle";

    currentCpuLevel =
        getSelectedCpuLevel();

    isQuickMatchWaiting =
        false;


    stopQuickMatchTimer();


    currentPlayerName =
        playerNameInput
        .value
        .trim();


    player1Name =
        "PLAYER 1";

    player2Name =
        "PLAYER 2";


    lastCpuQuestion =
        "";

    lastCpuAnswer =
        "";

    lastCpuCandidateCount =
        null;

    lastCpuBeforeCandidateCount =
        null;

    lastCpuYesPredictionCount =
        null;

    lastCpuNoPredictionCount =
        null;

    lastCpuSplitScore =
        null;


    roomIdInput.value =
        "";


    roomInfo.textContent =
        "Room ----";


    playerInfo.textContent =
        "Player -";


    handContainer.innerHTML =
        "";


    player1RevealedHand.innerHTML =
        "";


    player2RevealedHand.innerHTML =
        "";


    cpuActionText.textContent =
        "";


    cpuActionSection.classList.add(
        "hidden"
    );


    gameOverTitle.textContent =
        "GAME OVER";


    gameOverMessage.textContent =
        "";


    gameOverSection.classList.add(
        "hidden"
    );


    player1Title.textContent =
        "PLAYER 1";


    player2Title.textContent =
        "PLAYER 2";


    rematchButton.disabled =
        false;


    resetGuessInput();


    updateFoundCount();

    updateGameStatus();

    updateControls();

    updateRoomControls();
}


// =============================================
// HAND
// =============================================

function displayHand(
    hand,
    container
) {

    container.innerHTML =
        "";


    if (
        !Array.isArray(
            hand
        )
    ) {

        return;
    }


    hand.forEach(
        (cardData) => {

            container.appendChild(
                createCardElement(
                    cardData
                )
            );
        }
    );
}


// =============================================
// CARD
// =============================================

function createCardElement(
    cardData
) {

    const cardText =
        String(
            cardData
        ).trim();


    if (
        cardText.toUpperCase()
        ===
        "JOKER"
    ) {

        return createJokerCard();
    }


    const parts =
        cardText.split(
            /\s+/
        );


    if (
        parts.length < 2
    ) {

        return createUnknownCard(
            cardText
        );
    }


    const rawSuit =
        parts[0];


    const rank =
        String(
            parts[1]
        )
        .trim()
        .toUpperCase();


    const suit =
        normalizeSuit(
            rawSuit
        );


    if (
        suit === null
        ||
        !isValidRank(
            rank
        )
    ) {

        return createUnknownCard(
            cardText
        );
    }


    const suitSymbol =
        getSuitSymbol(
            suit
        );


    const card =
        document.createElement(
            "div"
        );


    card.classList.add(
        "playing-card"
    );


    if (
        suit ===
        "HEART"
        ||
        suit ===
        "DIAMOND"
    ) {

        card.classList.add(
            "card-red"
        );
    }

    else {

        card.classList.add(
            "card-black"
        );
    }


    const topCorner =
        document.createElement(
            "div"
        );


    topCorner.classList.add(
        "card-corner"
    );


    topCorner.innerHTML =
        `<span>${rank}</span>`
        +
        `<span>${suitSymbol}</span>`;


    const center =
        document.createElement(
            "div"
        );


    center.classList.add(
        "card-center"
    );


    center.textContent =
        suitSymbol;


    const bottomCorner =
        document.createElement(
            "div"
        );


    bottomCorner.classList.add(
        "card-corner",
        "card-bottom"
    );


    bottomCorner.innerHTML =
        `<span>${rank}</span>`
        +
        `<span>${suitSymbol}</span>`;


    card.appendChild(
        topCorner
    );


    card.appendChild(
        center
    );


    card.appendChild(
        bottomCorner
    );


    return card;
}


function createJokerCard() {

    const card =
        document.createElement(
            "div"
        );


    card.classList.add(
        "playing-card",
        "joker-card"
    );


    card.textContent =
        "JOKER";


    return card;
}


function createUnknownCard(
    text
) {

    const card =
        document.createElement(
            "div"
        );


    card.classList.add(
        "playing-card"
    );


    card.style.display =
        "flex";

    card.style.alignItems =
        "center";

    card.style.justifyContent =
        "center";

    card.style.padding =
        "12px";

    card.style.textAlign =
        "center";

    card.style.color =
        "#222";


    card.textContent =
        text;


    return card;
}


// =============================================
// RANK
// =============================================

function isValidRank(
    rank
) {

    return [
        "A",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "10",
        "J",
        "Q",
        "K"
    ].includes(
        rank
    );
}


// =============================================
// SUIT
// =============================================

function normalizeSuit(
    rawSuit
) {

    const suit =
        String(
            rawSuit
        )
        .trim()
        .toUpperCase();


    const aliases = {

        "SPADE":
            "SPADE",

        "SPADES":
            "SPADE",

        "S":
            "SPADE",

        "♠":
            "SPADE",

        "♤":
            "SPADE",

        "スペード":
            "SPADE",


        "HEART":
            "HEART",

        "HEARTS":
            "HEART",

        "H":
            "HEART",

        "♥":
            "HEART",

        "♡":
            "HEART",

        "ハート":
            "HEART",


        "DIAMOND":
            "DIAMOND",

        "DIAMONDS":
            "DIAMOND",

        "D":
            "DIAMOND",

        "♦":
            "DIAMOND",

        "♢":
            "DIAMOND",

        "ダイヤ":
            "DIAMOND",

        "ダイヤモンド":
            "DIAMOND",


        "CLUB":
            "CLUB",

        "CLUBS":
            "CLUB",

        "C":
            "CLUB",

        "♣":
            "CLUB",

        "♧":
            "CLUB",

        "クラブ":
            "CLUB",

        "クローバー":
            "CLUB"
    };


    return (
        aliases[suit]
        ||
        null
    );
}


function getSuitSymbol(
    suit
) {

    if (
        suit ===
        "SPADE"
    ) {

        return "♠";
    }


    if (
        suit ===
        "HEART"
    ) {

        return "♥";
    }


    if (
        suit ===
        "DIAMOND"
    ) {

        return "♦";
    }


    if (
        suit ===
        "CLUB"
    ) {

        return "♣";
    }


    return "?";
}


// =============================================
// INITIALIZE
// =============================================

resetBattleState();