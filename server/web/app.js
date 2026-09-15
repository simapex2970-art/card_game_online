// =============================================
// VEIL 53
// Browser Client
//
// PvP
// CPU Lv.1
// =============================================


// =============================================
// HTML要素
// =============================================

const roomScreen =
    document.getElementById(
        "room-screen"
    );

const gameScreen =
    document.getElementById(
        "game-screen"
    );

const createRoomButton =
    document.getElementById(
        "create-room-button"
    );

const joinRoomButton =
    document.getElementById(
        "join-room-button"
    );

const cpuGameButton =
    document.getElementById(
        "cpu-game-button"
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


// =============================================
// CPU表示
// =============================================

const cpuActionSection =
    document.getElementById(
        "cpu-action-section"
    );

const cpuActionText =
    document.getElementById(
        "cpu-action-text"
    );


// =============================================
// 質問
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
// 予想
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
// 予想結果
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
// 状態
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

let lastCpuQuestion =
    "";

let lastCpuAnswer =
    "";


// =============================================
// ルームID
// =============================================

const roomIdPattern =
    /^[A-HJ-NP-Z2-9]{4}$/;


// =============================================
// 初期状態
// =============================================

resetBattleState();


// =============================================
// ルーム操作UI
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


    if (
        roomConnectionState ===
        "creating"
    ) {

        createRoomButton.textContent =
            "ルーム作成中...";

        cpuGameButton.textContent =
            "CPUと対戦する";

        return;
    }


    if (
        roomConnectionState ===
        "cpu-creating"
    ) {

        createRoomButton.textContent =
            "ルームを作る";

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

        joinRoomButton.textContent =
            "参加済み";

        cpuGameButton.textContent =
            "対戦中";

        return;
    }


    createRoomButton.textContent =
        "ルームを作る";

    joinRoomButton.textContent =
        "ルームに参加";

    cpuGameButton.textContent =
        "CPUと対戦する";
}


// =============================================
// 対人ルーム作成
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


        gameMode =
            "pvp";

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
                        method: "POST"
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


            message.textContent =
                `ルームID：${currentRoomId}\n`
                + "接続しています...";


            roomConnectionState =
                "connecting";

            updateRoomControls();


            connectWebSocket(
                currentRoomId
            );

        } catch (error) {

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
// CPU対戦作成
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


        gameMode =
            "cpu";

        roomConnectionState =
            "cpu-creating";

        updateRoomControls();


        message.textContent =
            "CPU対戦を準備しています...";


        try {

            const response =
                await fetch(
                    "/cpu-rooms",
                    {
                        method: "POST"
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


            roomConnectionState =
                "connecting";

            updateRoomControls();


            message.textContent =
                "CPU対戦に接続しています...";


            connectWebSocket(
                currentRoomId
            );

        } catch (error) {

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
// ルーム参加
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
                "ルームIDの形式が正しくありません。\n"
                + "使用できる文字を確認してください。";

            roomIdInput.focus();

            return;
        }


        gameMode =
            "pvp";

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


// =============================================
// Enter参加
// =============================================

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


// =============================================
// WebSocket
// =============================================

function connectWebSocket(
    roomId
) {

    closeSocketWithoutLeave();


    const protocol =
        location.protocol === "https:"
            ? "wss"
            : "ws";


    const socketUrl =
        `${protocol}://${location.host}`
        + `/ws/${roomId}`;


    console.log(
        "WebSocket:",
        socketUrl
    );


    const newSocket =
        new WebSocket(
            socketUrl
        );


    socket =
        newSocket;


    // =========================================
    // 接続
    // =========================================

    newSocket.addEventListener(
        "open",
        () => {

            if (
                socket !==
                newSocket
            ) {

                return;
            }


            message.textContent =
                gameMode === "cpu"
                    ? "CPU対戦に接続しました。"
                    : `ルームID：${roomId}\n`
                      + "サーバーに接続しました。";
        }
    );


    // =========================================
    // 受信
    // =========================================

    newSocket.addEventListener(
        "message",
        (event) => {

            if (
                socket !==
                newSocket
            ) {

                return;
            }


            try {

                const data =
                    JSON.parse(
                        event.data
                    );


                console.log(
                    "受信:",
                    data
                );


                handleServerMessage(
                    data
                );

            } catch (error) {

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


    // =========================================
    // 切断
    // =========================================

    newSocket.addEventListener(
        "close",
        () => {

            if (
                socket !==
                newSocket
            ) {

                return;
            }


            socket =
                null;


            if (
                roomConnectionState ===
                "connecting"
            ) {

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
                    + "もう一度対戦を開始してください。"
                );
            }
        }
    );


    // =========================================
    // エラー
    // =========================================

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
// サーバーメッセージ
// =============================================

function handleServerMessage(
    data
) {

    // =========================================
    // 特定エラー
    // =========================================

    if (
        data.type === "error"
        &&
        data.code ===
        "ROOM_NOT_FOUND"
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


        roomConnectionState =
            "idle";

        currentRoomId =
            null;

        playerNumber =
            null;

        updateRoomControls();


        message.textContent =
            "そのルームは存在しません。\n\n"
            + "ルームIDを確認してください。";

        return;
    }


    if (
        data.type === "error"
        &&
        data.code ===
        "ROOM_FULL"
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


        roomConnectionState =
            "idle";

        currentRoomId =
            null;

        playerNumber =
            null;

        updateRoomControls();


        message.textContent =
            "そのルームは満員です。\n\n"
            + "別のルームに参加するか、"
            + "新しいルームを作ってください。";

        return;
    }


    if (
        data.type === "error"
        &&
        data.code ===
        "INVALID_ROOM_ID"
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


        roomConnectionState =
            "idle";

        currentRoomId =
            null;

        playerNumber =
            null;

        updateRoomControls();


        message.textContent =
            "ルームIDの形式が正しくありません。";

        return;
    }


    // =========================================
    // Player番号
    // =========================================

    if (
        data.type ===
        "player_number"
    ) {

        playerNumber =
            data.player;


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


        roomConnectionState =
            "joined";

        updateRoomControls();


        roomInfo.textContent =
            gameMode === "cpu"
                ? "CPU BATTLE"
                : `Room ${currentRoomId}`;


        playerInfo.textContent =
            gameMode === "cpu"
                ? "YOU vs CPU"
                : `Player ${playerNumber}`;


        myTurn =
            false;

        currentPhase =
            "waiting";

        waitingForServer =
            false;

        updateControls();


        message.textContent =
            gameMode === "cpu"
                ? "CPU対戦を開始します..."
                : `ルームID：${currentRoomId}\n`
                  + `Player ${playerNumber}\n\n`
                  + "相手を待っています...";


        return;
    }


    // =========================================
    // ゲーム開始
    // =========================================

    if (
        data.type ===
        "game_start"
    ) {

        showGameScreen();


        playerNumber =
            data.player;


        if (
            data.mode
        ) {

            gameMode =
                data.mode;
        }


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


        cpuActionSection.classList.add(
            "hidden"
        );

        cpuActionText.textContent =
            "";


        roomInfo.textContent =
            gameMode === "cpu"
                ? "CPU BATTLE"
                : `Room ${currentRoomId}`;


        playerInfo.textContent =
            gameMode === "cpu"
                ? "YOU vs CPU"
                : `Player ${playerNumber}`;


        player2Title.textContent =
            gameMode === "cpu"
                ? "CPU"
                : "PLAYER 2";


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


        updateFoundCount();

        updateGameStatus();

        updateControls();


        message.textContent =
            gameMode === "cpu"
                ? "CPU対戦開始！\n"
                  + "質問を1つ選んでください。"
                : (
                    myTurn
                        ? "ゲーム開始！\n"
                          + "質問を1つ選んでください。"
                        : "ゲーム開始！\n"
                          + "相手のターンです。"
                );


        return;
    }


    // =========================================
    // 人間の質問結果
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
                ? "YES"
                : "NO";


        message.textContent =
            `${data.question}\n\n`
            + `答え：${answerText}`;


        updateGameStatus();

        updateControls();


        return;
    }


    // =========================================
    // フェーズ変更
    // =========================================

    if (
        data.type ===
        "phase_changed"
    ) {

        currentPhase =
            data.phase;


        waitingForServer =
            false;


        updateGameStatus();

        updateControls();


        return;
    }


    // =========================================
    // 人間の予想結果
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


        if (
            data.correct
        ) {

            guessResultText.textContent =
                `${data.guess}\n\n`
                + "🎉 当たり！";

        } else {

            guessResultText.textContent =
                `${data.guess}\n\n`
                + "はずれ！";
        }


        guessResultCount.textContent =
            `現在 ${currentFoundCount} / 3 枚正解`;


        gameStatus.textContent =
            "予想結果を確認してください";


        message.textContent =
            "結果を確認したら"
            + "「次へ」を押してください。";


        updateControls();


        return;
    }


    // =========================================
    // CPU質問
    // =========================================

    if (
        data.type ===
        "cpu_question"
    ) {

        lastCpuQuestion =
            data.question;


        lastCpuAnswer =
            data.answer
                ? "YES"
                : "NO";


        cpuActionSection.classList.remove(
            "hidden"
        );


        cpuActionText.textContent =
            `CPUの質問\n\n`
            + `${lastCpuQuestion}\n\n`
            + `答え：${lastCpuAnswer}`;


        gameStatus.textContent =
            "CPUが考えています...";


        message.textContent =
            "CPUがあなたのカードを"
            + "推理しています...";


        return;
    }


    // =========================================
    // CPU予想結果
    // =========================================

    if (
        data.type ===
        "cpu_guess_result"
    ) {

        const resultText =
            data.correct
                ? "🎯 当たり！"
                : "はずれ！";


        cpuActionSection.classList.remove(
            "hidden"
        );


        cpuActionText.textContent =
            `CPUの質問\n\n`
            + `${lastCpuQuestion}\n`
            + `答え：${lastCpuAnswer}\n\n`
            + `CPUの予想\n\n`
            + `${data.guess}\n\n`
            + resultText
            + `\n\nCPU：${data.found_count} / 3 枚正解`;


        gameStatus.textContent =
            "CPUの予想結果";


        message.textContent =
            data.correct
                ? "CPUがカードを1枚当てました。"
                : "CPUの予想は外れました。";


        return;
    }


    // =========================================
    // ターン変更
    // =========================================

    if (
        data.type ===
        "turn_changed"
    ) {

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
                "あなたのターンです。\n"
                + "質問を1つ選んでください。";

        } else {

            message.textContent =
                gameMode === "cpu"
                    ? "CPUのターンです..."
                    : "相手のターンです。";
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


        displayHand(
            data.player1_hand,
            player1RevealedHand
        );


        displayHand(
            data.player2_hand,
            player2RevealedHand
        );


        player2Title.textContent =
            gameMode === "cpu"
                ? "CPU"
                : "PLAYER 2";


        if (
            data.winner ===
            playerNumber
        ) {

            gameOverTitle.textContent =
                "YOU WIN";

            gameOverMessage.textContent =
                "相手の3枚すべてを見破りました。";

            gameStatus.textContent =
                "あなたの勝ち！";

            message.textContent =
                "🎉 あなたの勝ちです！";

        } else {

            gameOverTitle.textContent =
                gameMode === "cpu"
                    ? "CPU WINS"
                    : "YOU LOSE";

            gameOverMessage.textContent =
                gameMode === "cpu"
                    ? "CPUがあなたの3枚をすべて見破りました。"
                    : "相手があなたの3枚をすべて見破りました。";

            gameStatus.textContent =
                "あなたの負け";

            message.textContent =
                gameMode === "cpu"
                    ? "CPUが3枚すべて当てました。"
                    : "相手が3枚すべて当てました。";
        }


        updateControls();


        return;
    }


    // =========================================
    // 再戦待ち
    // =========================================

    if (
        data.type ===
        "rematch_waiting"
    ) {

        message.textContent =
            "相手の再戦希望を"
            + "待っています...";

        return;
    }


    // =========================================
    // 相手切断
    // =========================================

    if (
        data.type ===
        "opponent_disconnected"
    ) {

        closeSocketWithoutLeave();


        returnToRoomScreen(
            "相手との接続が切れました。\n"
            + "対戦を終了しました。\n\n"
            + "新しいルームを作るか、"
            + "別のルームに参加してください。"
        );


        return;
    }


    // =========================================
    // 相手終了
    // =========================================

    if (
        data.type ===
        "opponent_left"
    ) {

        closeSocketWithoutLeave();


        returnToRoomScreen(
            "相手がゲームを終了しました。\n\n"
            + "新しい対戦を開始してください。"
        );


        return;
    }


    // =========================================
    // 通常エラー
    // =========================================

    if (
        data.type ===
        "error"
    ) {

        waitingForServer =
            false;

        updateControls();


        message.textContent =
            data.message
            || "エラーが発生しました。";


        return;
    }


    console.log(
        "未処理:",
        data
    );
}


// =============================================
// UI共通
// =============================================

function updateControls() {

    updateQuestionControls();

    updateGuessControls();

    updateResultControls();
}


// =============================================
// ゲーム画面
// =============================================

function showGameScreen() {

    roomScreen.classList.add(
        "hidden"
    );

    gameScreen.classList.remove(
        "hidden"
    );
}


// =============================================
// ルーム画面
// =============================================

function showRoomScreen() {

    gameScreen.classList.add(
        "hidden"
    );

    roomScreen.classList.remove(
        "hidden"
    );
}


// =============================================
// ゲームステータス
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

        gameStatus.textContent =
            gameMode === "cpu"
                ? "CPUのターンです"
                : "相手のターンです";

        return;
    }


    if (
        currentPhase ===
        "question"
    ) {

        gameStatus.textContent =
            "あなたのターン："
            + "質問を選んでください";

        return;
    }


    if (
        currentPhase ===
        "guess"
    ) {

        gameStatus.textContent =
            "相手のカードを"
            + "1枚予想してください";

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
// 質問UI
// =============================================

function updateQuestionControls() {

    const canAsk =
        myTurn
        &&
        currentPhase === "question"
        &&
        !waitingForServer;


    if (
        canAsk
    ) {

        questionSection.classList.remove(
            "hidden"
        );

    } else {

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


// =============================================
// 予想UI
// =============================================

function updateGuessControls() {

    const canGuess =
        myTurn
        &&
        currentPhase === "guess"
        &&
        !waitingForServer;


    if (
        canGuess
    ) {

        guessSection.classList.remove(
            "hidden"
        );

    } else {

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

    } else {

        updateGuessRankState();
    }


    guessCardButton.disabled =
        !canGuess;
}


// =============================================
// 人間の結果
// =============================================

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

    } else {

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
// 正解枚数
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


// =============================================
// 予想入力リセット
// =============================================

function resetGuessInput() {

    guessSuit.value =
        "";

    guessRank.value =
        "";

    guessRank.disabled =
        true;
}


// =============================================
// 質問送信可能
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
    ) {

        return false;
    }


    if (
        !myTurn
    ) {

        message.textContent =
            gameMode === "cpu"
                ? "今はCPUのターンです。"
                : "今は相手のターンです。";

        return false;
    }


    if (
        currentPhase !==
        "question"
    ) {

        return false;
    }


    return true;
}


// =============================================
// 質問送信
// =============================================

function sendQuestion(
    questionId,
    extraData = {}
) {

    if (
        !canSendQuestion()
    ) {

        return;
    }


    const data = {
        type: "question",
        question_id: questionId,
        ...extraData
    };


    waitingForServer =
        true;


    updateControls();


    message.textContent =
        "質問しています...";


    socket.send(
        JSON.stringify(
            data
        )
    );
}


// =============================================
// ランク質問
// =============================================

function validateRankQuestion() {

    const rank =
        rankQuestionValue
        .value
        .trim()
        .toUpperCase();


    if (
        rank === ""
    ) {

        message.textContent =
            "ランクを選択してください。";

        rankQuestionValue.focus();

        return null;
    }


    if (
        !isValidRank(
            rank
        )
    ) {

        message.textContent =
            "ランクが正しくありません。";

        return null;
    }


    return rank;
}


// =============================================
// 数字質問
// =============================================

function validateNumberQuestion(
    inputElement
) {

    const rawValue =
        inputElement
        .value
        .trim();


    if (
        rawValue === ""
    ) {

        message.textContent =
            "数字を入力してください。";

        inputElement.focus();

        return null;
    }


    const number =
        Number(
            rawValue
        );


    if (
        !Number.isInteger(
            number
        )
        ||
        number < 1
        ||
        number > 13
    ) {

        message.textContent =
            "1〜13の整数を"
            + "入力してください。";

        inputElement.focus();

        return null;
    }


    return number;
}


// =============================================
// 質問ボタン
// =============================================

questionEvenButton.addEventListener(
    "click",
    () => {

        sendQuestion(
            1
        );
    }
);


questionOddButton.addEventListener(
    "click",
    () => {

        sendQuestion(
            2
        );
    }
);


questionFaceButton.addEventListener(
    "click",
    () => {

        sendQuestion(
            3
        );
    }
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
                rank: rank
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
                number: number
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
                number: number
            }
        );
    }
);


questionSpadeButton.addEventListener(
    "click",
    () => {

        sendQuestion(
            7
        );
    }
);


questionHeartButton.addEventListener(
    "click",
    () => {

        sendQuestion(
            8
        );
    }
);


questionDiamondButton.addEventListener(
    "click",
    () => {

        sendQuestion(
            9
        );
    }
);


questionClubButton.addEventListener(
    "click",
    () => {

        sendQuestion(
            10
        );
    }
);


questionJokerButton.addEventListener(
    "click",
    () => {

        sendQuestion(
            11
        );
    }
);


// =============================================
// 予想
// =============================================

guessCardButton.addEventListener(
    "click",
    () => {

        sendGuess();
    }
);


function sendGuess() {

    if (
        socket === null
        ||
        socket.readyState !==
        WebSocket.OPEN
    ) {

        message.textContent =
            "サーバーに接続されていません。";

        return;
    }


    if (
        waitingForServer
    ) {

        return;
    }


    if (
        !myTurn
    ) {

        return;
    }


    if (
        currentPhase !==
        "guess"
    ) {

        message.textContent =
            "先に質問してください。";

        return;
    }


    const suit =
        guessSuit.value;


    if (
        suit === ""
    ) {

        message.textContent =
            "スートを選択してください。";

        guessSuit.focus();

        return;
    }


    let data;


    if (
        suit ===
        "JOKER"
    ) {

        data = {
            type: "guess_card",
            suit: "JOKER"
        };


        message.textContent =
            "JOKERで予想しています...";

    } else {

        const rank =
            guessRank
            .value
            .trim()
            .toUpperCase();


        if (
            rank === ""
        ) {

            message.textContent =
                "ランクを選択してください。";

            guessRank.focus();

            return;
        }


        if (
            !isValidRank(
                rank
            )
        ) {

            message.textContent =
                "ランクが正しくありません。";

            return;
        }


        data = {
            type: "guess_card",
            suit: suit,
            rank: rank
        };


        message.textContent =
            `${suit} ${rank} で`
            + "予想しています...";
    }


    waitingForServer =
        true;


    updateControls();


    socket.send(
        JSON.stringify(
            data
        )
    );
}


// =============================================
// 次へ
// =============================================

nextTurnButton.addEventListener(
    "click",
    () => {

        continueAfterGuess();
    }
);


function continueAfterGuess() {

    if (
        socket === null
        ||
        socket.readyState !==
        WebSocket.OPEN
    ) {

        return;
    }


    if (
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
        gameMode === "cpu"
            ? "CPUのターンへ進みます..."
            : "次のターンへ進みます...";


    socket.send(
        JSON.stringify({
            type: "continue_after_guess"
        })
    );
}


// =============================================
// 再戦
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
            gameMode === "cpu"
                ? "CPUと再戦します..."
                : "再戦をリクエストしました。";


        socket.send(
            JSON.stringify({
                type: "rematch_request"
            })
        );
    }
);


// =============================================
// ゲーム終了
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
                        type: "leave_game"
                    })
                );

            } catch (error) {

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
// WebSocketを閉じる
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

    } catch (error) {

        console.error(
            error
        );
    }
}


// =============================================
// ルーム画面へ戻る
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
// 状態リセット
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

    lastCpuQuestion =
        "";

    lastCpuAnswer =
        "";


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
// 手札表示
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

            const card =
                createCardElement(
                    cardData
                );


            container.appendChild(
                card
            );
        }
    );
}


// =============================================
// カード作成
// =============================================

function createCardElement(
    cardData
) {

    const cardText =
        String(
            cardData
        )
        .trim();


    if (
        cardText
        .toUpperCase()
        === "JOKER"
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
        suit === "HEART"
        ||
        suit === "DIAMOND"
    ) {

        card.classList.add(
            "card-red"
        );

    } else {

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


    const topRank =
        document.createElement(
            "span"
        );

    topRank.textContent =
        rank;


    const topSuit =
        document.createElement(
            "span"
        );

    topSuit.textContent =
        suitSymbol;


    topCorner.appendChild(
        topRank
    );

    topCorner.appendChild(
        topSuit
    );


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


    const bottomRank =
        document.createElement(
            "span"
        );

    bottomRank.textContent =
        rank;


    const bottomSuit =
        document.createElement(
            "span"
        );

    bottomSuit.textContent =
        suitSymbol;


    bottomCorner.appendChild(
        bottomRank
    );

    bottomCorner.appendChild(
        bottomSuit
    );


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


// =============================================
// JOKER
// =============================================

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


// =============================================
// 不明カード
// =============================================

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

    card.style.flexDirection =
        "column";

    card.style.justifyContent =
        "center";

    card.style.alignItems =
        "center";

    card.style.padding =
        "12px";

    card.style.textAlign =
        "center";


    card.textContent =
        text;


    return card;
}


// =============================================
// ランク
// =============================================

function isValidRank(
    rank
) {

    const ranks = [
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
    ];


    return ranks.includes(
        rank
    );
}


// =============================================
// スート
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

        "SPADE": "SPADE",
        "SPADES": "SPADE",
        "S": "SPADE",
        "♠": "SPADE",
        "♤": "SPADE",
        "スペード": "SPADE",

        "HEART": "HEART",
        "HEARTS": "HEART",
        "H": "HEART",
        "♥": "HEART",
        "♡": "HEART",
        "ハート": "HEART",

        "DIAMOND": "DIAMOND",
        "DIAMONDS": "DIAMOND",
        "D": "DIAMOND",
        "♦": "DIAMOND",
        "♢": "DIAMOND",
        "ダイヤ": "DIAMOND",
        "ダイヤモンド": "DIAMOND",

        "CLUB": "CLUB",
        "CLUBS": "CLUB",
        "C": "CLUB",
        "♣": "CLUB",
        "♧": "CLUB",
        "クラブ": "CLUB",
        "クローバー": "CLUB"
    };


    return aliases[
        suit
    ] || null;
}


// =============================================
// スート記号
// =============================================

function getSuitSymbol(
    suit
) {

    if (
        suit === "SPADE"
    ) {

        return "♠";
    }


    if (
        suit === "HEART"
    ) {

        return "♥";
    }


    if (
        suit === "DIAMOND"
    ) {

        return "♦";
    }


    if (
        suit === "CLUB"
    ) {

        return "♣";
    }


    return "?";
}