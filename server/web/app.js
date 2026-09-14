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

const handSection =
    document.getElementById(
        "hand-section"
    );

const handContainer =
    document.getElementById(
        "hand-container"
    );

const statusSection =
    document.getElementById(
        "status-section"
    );

const gameStatus =
    document.getElementById(
        "game-status"
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
// ゲーム終了画面
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

const rematchButton =
    document.getElementById(
        "rematch-button"
    );

const leaveGameButton =
    document.getElementById(
        "leave-game-button"
    );


// =============================================
// ゲーム状態
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


// =============================================
// ルーム接続状態
// =============================================

let roomConnectionState =
    "idle";

/*
    idle
        操作可能

    creating
        ルーム作成中

    connecting
        WebSocket接続中

    joined
        ルーム参加済み
*/


// =============================================
// 初期化
// =============================================

updateFoundCount();

updateControls();

updateRoomControls();


// =============================================
// ルーム画面操作状態
// =============================================

function updateRoomControls() {

    const locked =
        roomConnectionState
        !== "idle";


    createRoomButton.disabled =
        locked;

    joinRoomButton.disabled =
        locked;

    roomIdInput.disabled =
        locked;


    if (
        roomConnectionState
        === "creating"
    ) {

        createRoomButton.textContent =
            "ルーム作成中...";

        joinRoomButton.textContent =
            "ルームに参加";

        return;
    }


    if (
        roomConnectionState
        === "connecting"
    ) {

        createRoomButton.textContent =
            "ルームを作る";

        joinRoomButton.textContent =
            "接続中...";

        return;
    }


    if (
        roomConnectionState
        === "joined"
    ) {

        createRoomButton.textContent =
            "ルームを作る";

        joinRoomButton.textContent =
            "参加済み";

        return;
    }


    createRoomButton.textContent =
        "ルームを作る";

    joinRoomButton.textContent =
        "ルームに参加";
}


// =============================================
// ルーム作成
// =============================================

createRoomButton.addEventListener(
    "click",
    async () => {

        if (
            roomConnectionState
            !== "idle"
        ) {

            return;
        }


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


            roomConnectionState =
                "connecting";


            updateRoomControls();


            message.textContent =
                `ルームID：${currentRoomId}\n`
                + "サーバーに接続しています...";


            connectWebSocket(
                currentRoomId
            );

        } catch (error) {

            console.error(
                error
            );


            currentRoomId =
                null;


            roomConnectionState =
                "idle";


            updateRoomControls();


            message.textContent =
                "ルームを作成できませんでした。\n\n"
                + "少し待ってから"
                + "もう一度試してください。";
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
            roomConnectionState
            !== "idle"
        ) {

            return;
        }


        const roomId =
            roomIdInput
                .value
                .trim()
                .toUpperCase();


        // =====================================
        // 空欄
        // =====================================

        if (
            roomId === ""
        ) {

            message.textContent =
                "ルームIDを入力してください。";

            roomIdInput.focus();

            return;
        }


        // =====================================
        // 4文字
        // =====================================

        if (
            roomId.length
            !== 4
        ) {

            message.textContent =
                "ルームIDは"
                + "4文字で入力してください。";

            roomIdInput.focus();

            return;
        }


        // =====================================
        // 使用可能文字
        // I / O / 0 / 1 は除外
        // =====================================

        const roomIdPattern =
            /^[A-HJ-NP-Z2-9]{4}$/;


        if (
            !roomIdPattern.test(
                roomId
            )
        ) {

            message.textContent =
                "ルームIDの形式が"
                + "正しくありません。";

            roomIdInput.focus();

            return;
        }


        currentRoomId =
            roomId;


        roomConnectionState =
            "connecting";


        updateRoomControls();


        message.textContent =
            `ルーム ${roomId} に`
            + "接続しています...";


        connectWebSocket(
            roomId
        );
    }
);


// =============================================
// Enterで参加
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
// WebSocket接続
// =============================================

function connectWebSocket(
    roomId
) {

    // =========================================
    // 古いWebSocketがある場合
    // =========================================

    if (
        socket !== null
    ) {

        const oldSocket =
            socket;


        socket =
            null;


        try {

            oldSocket.close();

        } catch (error) {

            console.log(
                "古いWebSocket終了:",
                error
            );
        }
    }


    const protocol =
        location.protocol === "https:"
            ? "wss"
            : "ws";


    const socketUrl =
        `${protocol}://${location.host}/ws/${roomId}`;


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
    // 接続成功
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
                `ルームID：${roomId}\n`
                + "接続しました。\n"
                + "参加処理を確認しています...";
        }
    );


    // =========================================
    // メッセージ
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
                    "JSON解析エラー:",
                    error
                );


                waitingForServer =
                    false;


                updateControls();


                message.textContent =
                    "サーバーからのデータを"
                    + "解析できませんでした。";
            }
        }
    );


    // =========================================
    // 接続終了
    // =========================================

    newSocket.addEventListener(
        "close",
        () => {

            /*
                エラー処理やゲーム終了処理などで
                すでにsocketが変更されている場合は
                何もしない。
            */

            if (
                socket !==
                newSocket
            ) {

                return;
            }


            socket =
                null;


            // =================================
            // 接続途中で終了
            // =================================

            if (
                roomConnectionState
                === "connecting"
            ) {

                roomConnectionState =
                    "idle";


                currentRoomId =
                    null;

                playerNumber =
                    null;


                updateRoomControls();


                message.textContent =
                    "ルームに接続できませんでした。\n\n"
                    + "ルームIDや"
                    + "サーバーの状態を"
                    + "確認してください。";


                return;
            }


            // =================================
            // 対戦中・待機中
            // =================================

            returnToRoomScreen(
                "サーバーとの接続が切れました。\n"
                + "対戦を終了しました。\n\n"
                + "もう一度ルームを作成するか、"
                + "ルームに参加してください。"
            );
        }
    );


    // =========================================
    // WebSocketエラー
    // =========================================

    newSocket.addEventListener(
        "error",
        (error) => {

            if (
                socket !==
                newSocket
            ) {

                return;
            }


            console.error(
                "WebSocketエラー:",
                error
            );


            /*
                errorのあと通常closeも発生するので、
                画面処理はclose側へ任せる。
            */
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
    // ルーム接続エラー
    // =========================================

    if (
        data.type === "error"
        &&
        (
            data.code
            === "ROOM_NOT_FOUND"

            ||

            data.code
            === "ROOM_FULL"

            ||

            data.code
            === "INVALID_ROOM_ID"
        )
    ) {

        const errorCode =
            data.code;


        // =====================================
        // closeイベントによる上書き防止
        // =====================================

        if (
            socket !== null
        ) {

            const failedSocket =
                socket;


            socket =
                null;


            try {

                failedSocket.close();

            } catch (error) {

                console.log(
                    error
                );
            }
        }


        currentRoomId =
            null;

        playerNumber =
            null;


        roomConnectionState =
            "idle";


        updateRoomControls();


        // =====================================
        // 存在しない
        // =====================================

        if (
            errorCode
            === "ROOM_NOT_FOUND"
        ) {

            message.textContent =
                "そのルームは存在しません。\n\n"
                + "ルームIDを確認してください。";


            roomIdInput.focus();


            return;
        }


        // =====================================
        // 満員
        // =====================================

        if (
            errorCode
            === "ROOM_FULL"
        ) {

            message.textContent =
                "そのルームは満員です。\n\n"
                + "別のルームに参加するか、"
                + "新しいルームを作ってください。";


            return;
        }


        // =====================================
        // ID形式
        // =====================================

        message.textContent =
            "ルームIDの形式が"
            + "正しくありません。\n\n"
            + "4文字のルームIDを"
            + "確認してください。";


        roomIdInput.focus();


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


        roomConnectionState =
            "joined";


        updateRoomControls();


        roomInfo.textContent =
            `Room ${currentRoomId}`;

        playerInfo.textContent =
            `Player ${playerNumber}`;


        myTurn =
            false;

        currentPhase =
            "waiting";

        waitingForServer =
            false;


        updateControls();


        message.textContent =
            `ルームID：${currentRoomId}\n`
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

        roomConnectionState =
            "joined";


        updateRoomControls();


        showGameScreen();

        hideGameOverScreen();


        handSection.classList.remove(
            "hidden"
        );

        statusSection.classList.remove(
            "hidden"
        );


        playerNumber =
            data.player;


        myTurn =
            Boolean(
                data.your_turn
            );


        currentPhase =
            data.phase
            || "waiting";


        waitingForServer =
            false;


        currentFoundCount =
            0;


        roomInfo.textContent =
            `Room ${currentRoomId}`;

        playerInfo.textContent =
            `Player ${playerNumber}`;


        displayHand(
            data.hand
        );


        resetGuessInput();

        resetQuestionInputs();


        guessResultText.textContent =
            "";


        updateFoundCount();

        updateGameStatus();

        updateControls();


        if (
            myTurn
        ) {

            message.textContent =
                "ゲーム開始！\n"
                + "質問を1つ選んでください。";

        } else {

            message.textContent =
                "ゲーム開始！\n"
                + "相手のターンです。";
        }


        return;
    }


    // =========================================
    // 質問結果
    // =========================================

    if (
        data.type ===
        "question_result"
    ) {

        waitingForServer =
            false;


        currentPhase =
            "guess";


        const answer =
            data.answer
                ? "YES"
                : "NO";


        message.textContent =
            `${data.question}\n\n`
            + `答え：${answer}`;


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
    // 予想結果
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


        message.textContent =
            "結果を確認したら"
            + "「次へ」を押してください。";


        updateGameStatus();

        updateControls();


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

        resetQuestionInputs();


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
                "相手のターンです。";
        }


        return;
    }


    // =========================================
    // ゲーム終了
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


        showGameOverScreen(
            data
        );


        return;
    }


    // =========================================
    // 再戦待ち
    // =========================================

    if (
        data.type ===
        "rematch_waiting"
    ) {

        rematchButton.disabled =
            true;


        rematchButton.textContent =
            "相手を待っています...";


        message.textContent =
            "相手の再戦希望を"
            + "待っています...";


        return;
    }


    // =========================================
    // 相手の予期しない切断
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
    // 相手がゲーム終了
    // =========================================

    if (
        data.type ===
        "opponent_left"
    ) {

        closeSocketWithoutLeave();


        returnToRoomScreen(
            "相手がゲームを終了しました。\n"
            + "対戦を終了しました。\n\n"
            + "新しいルームを作るか、"
            + "別のルームに参加してください。"
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
// UI全体
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
// ゲーム終了画面
// =============================================

function showGameOverScreen(
    data
) {

    questionSection.classList.add(
        "hidden"
    );

    guessSection.classList.add(
        "hidden"
    );

    guessResultSection.classList.add(
        "hidden"
    );

    handSection.classList.add(
        "hidden"
    );


    gameOverSection.classList.remove(
        "hidden"
    );


    if (
        data.winner ===
        playerNumber
    ) {

        gameOverTitle.textContent =
            "🎉 WIN";


        gameOverMessage.textContent =
            "あなたの勝ちです！";


        gameStatus.textContent =
            "あなたの勝ち！";

    } else {

        gameOverTitle.textContent =
            "LOSE";


        gameOverMessage.textContent =
            `Player ${data.winner} の勝ちです`;


        gameStatus.textContent =
            "あなたの負け";
    }


    displayRevealedHand(
        player1RevealedHand,
        data.player1_hand
    );


    displayRevealedHand(
        player2RevealedHand,
        data.player2_hand
    );


    rematchButton.disabled =
        false;


    rematchButton.textContent =
        "もう一度遊ぶ";


    message.textContent =
        "両プレイヤーの手札を公開しました。";
}


// =============================================
// ゲーム終了画面を隠す
// =============================================

function hideGameOverScreen() {

    gameOverSection.classList.add(
        "hidden"
    );


    player1RevealedHand.innerHTML =
        "";

    player2RevealedHand.innerHTML =
        "";


    gameOverTitle.textContent =
        "ゲーム終了";


    gameOverMessage.textContent =
        "";


    rematchButton.disabled =
        false;


    rematchButton.textContent =
        "もう一度遊ぶ";
}


// =============================================
// ゲーム状態
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
            "相手のターンです";

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


    questionSection.classList.toggle(
        "hidden",
        !canAsk
    );


    questionButtons.forEach(
        (button) => {

            button.disabled =
                !canAsk;
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


    guessSection.classList.toggle(
        "hidden",
        !canGuess
    );


    guessSuit.disabled =
        !canGuess;


    guessCardButton.disabled =
        !canGuess;


    if (
        canGuess
    ) {

        updateGuessRankState();

    } else {

        guessRank.disabled =
            true;
    }
}


// =============================================
// 予想結果UI
// =============================================

function updateResultControls() {

    const showResult =
        myTurn
        &&
        currentPhase === "result";


    guessResultSection.classList.toggle(
        "hidden",
        !showResult
    );


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
// 質問入力リセット
// =============================================

function resetQuestionInputs() {

    rankQuestionValue.value =
        "";

    moreThanValue.value =
        "";

    lessThanValue.value =
        "";
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

        guessRank.value =
            "";

        guessRank.disabled =
            true;

        return;
    }


    guessRank.disabled =
        !(
            myTurn
            &&
            currentPhase === "guess"
            &&
            !waitingForServer
        );
}


// =============================================
// 質問送信可能確認
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
            "今は相手のターンです。";

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


    waitingForServer =
        true;


    updateControls();


    message.textContent =
        "質問しています...";


    socket.send(
        JSON.stringify({
            type: "question",
            question_id: questionId,
            ...extraData
        })
    );
}


// =============================================
// 偶数
// =============================================

questionEvenButton.addEventListener(
    "click",
    () => {

        sendQuestion(1);
    }
);


// =============================================
// 奇数
// =============================================

questionOddButton.addEventListener(
    "click",
    () => {

        sendQuestion(2);
    }
);


// =============================================
// 絵札
// =============================================

questionFaceButton.addEventListener(
    "click",
    () => {

        sendQuestion(3);
    }
);


// =============================================
// ランク
// =============================================

questionRankButton.addEventListener(
    "click",
    () => {

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


        sendQuestion(
            4,
            {
                rank: rank
            }
        );
    }
);


// =============================================
// 以上
// =============================================

questionMoreThanButton.addEventListener(
    "click",
    () => {

        const rawValue =
            moreThanValue
                .value
                .trim();


        if (
            rawValue === ""
        ) {

            message.textContent =
                "数字を入力してください。";

            return;
        }


        const number =
            Number(
                rawValue
            );


        if (
            !Number.isInteger(number)
            ||
            number < 1
            ||
            number > 13
        ) {

            message.textContent =
                "1〜13の整数を入力してください。";

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


// =============================================
// 以下
// =============================================

questionLessThanButton.addEventListener(
    "click",
    () => {

        const rawValue =
            lessThanValue
                .value
                .trim();


        if (
            rawValue === ""
        ) {

            message.textContent =
                "数字を入力してください。";

            return;
        }


        const number =
            Number(
                rawValue
            );


        if (
            !Number.isInteger(number)
            ||
            number < 1
            ||
            number > 13
        ) {

            message.textContent =
                "1〜13の整数を入力してください。";

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


// =============================================
// スペード
// =============================================

questionSpadeButton.addEventListener(
    "click",
    () => {

        sendQuestion(7);
    }
);


// =============================================
// ハート
// =============================================

questionHeartButton.addEventListener(
    "click",
    () => {

        sendQuestion(8);
    }
);


// =============================================
// ダイヤ
// =============================================

questionDiamondButton.addEventListener(
    "click",
    () => {

        sendQuestion(9);
    }
);


// =============================================
// クラブ
// =============================================

questionClubButton.addEventListener(
    "click",
    () => {

        sendQuestion(10);
    }
);


// =============================================
// JOKER
// =============================================

questionJokerButton.addEventListener(
    "click",
    () => {

        sendQuestion(11);
    }
);


// =============================================
// カード予想
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

        message.textContent =
            "今は相手のターンです。";

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


    // =========================================
    // JOKER
    // =========================================

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

        // =====================================
        // 通常カード
        // =====================================

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

        message.textContent =
            "サーバーに接続されていません。";

        return;
    }


    if (
        currentPhase !==
        "result"
    ) {

        return;
    }


    if (
        !myTurn
    ) {

        return;
    }


    if (
        waitingForServer
    ) {

        return;
    }


    waitingForServer =
        true;


    updateControls();


    message.textContent =
        "次のターンへ進みます...";


    socket.send(
        JSON.stringify({
            type:
                "continue_after_guess"
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

            message.textContent =
                "サーバーに接続されていません。";

            return;
        }


        if (
            currentPhase !==
            "finished"
        ) {

            return;
        }


        rematchButton.disabled =
            true;


        rematchButton.textContent =
            "再戦申請中...";


        message.textContent =
            "再戦を希望しました。";


        socket.send(
            JSON.stringify({
                type:
                    "rematch_request"
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

            const leavingSocket =
                socket;


            /*
                closeイベントに
                通信切断扱いさせない。
            */

            socket =
                null;


            try {

                leavingSocket.send(
                    JSON.stringify({
                        type:
                            "leave_game"
                    })
                );


                leavingSocket.close(
                    1000,
                    "leave_game"
                );

            } catch (error) {

                console.error(
                    "終了処理エラー:",
                    error
                );
            }

        } else {

            socket =
                null;
        }


        returnToRoomScreen(
            "ゲームを終了しました。\n\n"
            + "新しいルームを作るか、"
            + "別のルームに参加してください。"
        );
    }
);


// =============================================
// WebSocketだけ閉じる
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

        if (
            oldSocket.readyState ===
            WebSocket.OPEN
        ) {

            oldSocket.close(
                1000,
                "room_closed"
            );

        } else if (
            oldSocket.readyState ===
            WebSocket.CONNECTING
        ) {

            oldSocket.close();
        }

    } catch (error) {

        console.log(
            "WebSocket close:",
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

    resetBattleState();


    gameScreen.classList.add(
        "hidden"
    );


    roomScreen.classList.remove(
        "hidden"
    );


    message.textContent =
        text;
}


// =============================================
// 対戦状態完全リセット
// =============================================

function resetBattleState() {

    // =========================================
    // 接続状態
    // =========================================

    roomConnectionState =
        "idle";


    // =========================================
    // JavaScript状態
    // =========================================

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


    // =========================================
    // ルーム入力
    // =========================================

    roomIdInput.value =
        "";


    // =========================================
    // 表示
    // =========================================

    roomInfo.textContent =
        "Room ----";

    playerInfo.textContent =
        "Player -";


    // =========================================
    // 手札
    // =========================================

    handContainer.innerHTML =
        "";


    // =========================================
    // 質問
    // =========================================

    resetQuestionInputs();


    // =========================================
    // 予想
    // =========================================

    resetGuessInput();


    // =========================================
    // 正解枚数
    // =========================================

    updateFoundCount();


    // =========================================
    // 予想結果
    // =========================================

    guessResultText.textContent =
        "";


    // =========================================
    // 公開カード
    // =========================================

    player1RevealedHand.innerHTML =
        "";

    player2RevealedHand.innerHTML =
        "";


    // =========================================
    // ゲーム終了画面
    // =========================================

    gameOverTitle.textContent =
        "ゲーム終了";

    gameOverMessage.textContent =
        "";

    gameOverSection.classList.add(
        "hidden"
    );


    // =========================================
    // 再戦
    // =========================================

    rematchButton.disabled =
        false;

    rematchButton.textContent =
        "もう一度遊ぶ";


    // =========================================
    // 通常画面
    // =========================================

    handSection.classList.remove(
        "hidden"
    );

    statusSection.classList.remove(
        "hidden"
    );


    questionSection.classList.add(
        "hidden"
    );

    guessSection.classList.add(
        "hidden"
    );

    guessResultSection.classList.add(
        "hidden"
    );


    gameStatus.textContent =
        "相手を待っています...";


    updateControls();

    updateRoomControls();
}


// =============================================
// 公開手札
// =============================================

function displayRevealedHand(
    container,
    hand
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
// 自分の手札
// =============================================

function displayHand(
    hand
) {

    handContainer.innerHTML =
        "";


    if (
        !Array.isArray(
            hand
        )
    ) {

        message.textContent =
            "手札データが正しくありません。";

        return;
    }


    hand.forEach(
        (cardData) => {

            handContainer.appendChild(
                createCardElement(
                    cardData
                )
            );
        }
    );
}


// =============================================
// カード生成
// =============================================

function createCardElement(
    cardData
) {

    const cardText =
        String(
            cardData
        ).trim();


    // =========================================
    // Joker
    // =========================================

    if (
        cardText.toUpperCase()
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
        !isValidRank(rank)
    ) {

        return createUnknownCard(
            cardText
        );
    }


    const symbol =
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


    // =========================================
    // 左上
    // =========================================

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
        symbol;


    topCorner.appendChild(
        topRank
    );

    topCorner.appendChild(
        topSuit
    );


    // =========================================
    // 中央
    // =========================================

    const center =
        document.createElement(
            "div"
        );


    center.classList.add(
        "card-center"
    );


    center.textContent =
        symbol;


    // =========================================
    // 右下
    // =========================================

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
        symbol;


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
// Jokerカード
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

    card.style.justifyContent =
        "center";

    card.style.alignItems =
        "center";

    card.style.padding =
        "12px";


    card.textContent =
        text;


    return card;
}


// =============================================
// ランク判定
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
// スート標準化
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


    return aliases[suit]
        || null;
}


// =============================================
// スート記号
// =============================================

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