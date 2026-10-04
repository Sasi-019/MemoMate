import { useEffect, useRef, useState } from "react";

const API_URL = "https://memomate-af77.onrender.com";

const INITIAL_MESSAGE = {
    role: "assistant",
    content:
        "Hi! I'm MemoMate. Tell me what you want to remember, schedule, or organize.",
};

const QUICK_PROMPTS = [
    "Remind me to call mom tomorrow at 6 PM",
    "What do I have tomorrow?",
    "Add milk and bread to my shopping list",
];

function Assistant() {

    const [messages, setMessages] = useState([
        INITIAL_MESSAGE,
    ]);

    const [input, setInput] = useState("");

    const [loading, setLoading] = useState(false);

    // -----------------------------------------------------
    // Voice state
    // -----------------------------------------------------

    const [isRecording, setIsRecording] = useState(false);

    const [voiceSupported, setVoiceSupported] =
        useState(false);

    const [voiceError, setVoiceError] =
        useState("");

    const [transcribing, setTranscribing] =
        useState(false);

    const mediaRecorderRef = useRef(null);

    const audioChunksRef = useRef([]);

    // -----------------------------------------------------
    // Check browser recording support
    // -----------------------------------------------------

    useEffect(() => {

        const supported =
            !!navigator.mediaDevices &&
            !!navigator.mediaDevices.getUserMedia &&
            !!window.MediaRecorder;

        setVoiceSupported(supported);

    }, []);

    // -----------------------------------------------------
    // Send text to Qwen
    // -----------------------------------------------------

    const sendMessage = async (
        messageOverride = null
    ) => {

        const trimmed = (
            messageOverride ?? input
        ).trim();

        if (!trimmed || loading) {
            return;
        }

        const previousConversation =
            messages.map((message) => ({
                role: message.role,
                content: message.content,
            }));

        setMessages((previous) => [
            ...previous,
            {
                role: "user",
                content: trimmed,
            },
        ]);

        setInput("");

        setLoading(true);

        setVoiceError("");

        try {

            const response = await fetch(
                `${API_URL}/assistant/chat`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json",
                    },

                    body: JSON.stringify({
                        message: trimmed,

                        conversation:
                            previousConversation,
                    }),
                }
            );

            const result =
                await response.json();

            if (!response.ok) {

                throw new Error(
                    result.detail ||
                        "Assistant request failed."
                );
            }

            setMessages((previous) => [
                ...previous,
                {
                    role: "assistant",

                    content:
                        result.response ||
                        "I understood your request.",

                    action: result.action,

                    data: result.data,
                },
            ]);

        } catch (error) {

            console.error(
                "Assistant error:",
                error
            );

            setMessages((previous) => [
                ...previous,
                {
                    role: "assistant",

                    content:
                        "Sorry, I couldn't connect to MemoMate AI right now.",

                    error: true,
                },
            ]);

        } finally {

            setLoading(false);
        }
    };

    // -----------------------------------------------------
    // Start recording
    // -----------------------------------------------------

    const startRecording = async () => {

        setVoiceError("");

        if (!voiceSupported) {

            setVoiceError(
                "Voice recording is not supported in this browser."
            );

            return;
        }

        try {

            const stream =
                await navigator.mediaDevices.getUserMedia(
                    {
                        audio: true,
                    }
                );

            const mediaRecorder =
                new MediaRecorder(stream);

            audioChunksRef.current = [];

            mediaRecorder.ondataavailable = (
                event
            ) => {

                if (event.data.size > 0) {

                    audioChunksRef.current.push(
                        event.data
                    );
                }
            };

            mediaRecorder.onstop = async () => {

                stream
                    .getTracks()
                    .forEach((track) =>
                        track.stop()
                    );

                const audioBlob =
                    new Blob(
                        audioChunksRef.current,
                        {
                            type:
                                mediaRecorder.mimeType ||
                                "audio/webm",
                        }
                    );

                await transcribeAudio(
                    audioBlob
                );
            };

            mediaRecorderRef.current =
                mediaRecorder;

            mediaRecorder.start();

            setIsRecording(true);

        } catch (error) {

            console.error(
                "Microphone error:",
                error
            );

            setVoiceError(
                "Microphone access was denied or unavailable. Please allow microphone access in Chrome."
            );
        }
    };

    // -----------------------------------------------------
    // Stop recording
    // -----------------------------------------------------

    const stopRecording = () => {

        const recorder =
            mediaRecorderRef.current;

        if (
            !recorder ||
            recorder.state === "inactive"
        ) {
            return;
        }

        recorder.stop();

        setIsRecording(false);
    };

    // -----------------------------------------------------
    // Send audio to FastAPI
    // -----------------------------------------------------

    const transcribeAudio = async (
        audioBlob
    ) => {

        setTranscribing(true);

        setVoiceError("");

        try {

            const formData =
                new FormData();

            formData.append(
                "file",
                audioBlob,
                "memomate-voice.webm"
            );

            const response =
                await fetch(
                    `${API_URL}/voice/transcribe`,
                    {
                        method: "POST",
                        body: formData,
                    }
                );

            const result =
                await response.json();

            if (!response.ok) {

                throw new Error(
                    result.detail ||
                        "Voice transcription failed."
                );
            }

            const transcript =
                result.text?.trim();

            if (!transcript) {

                throw new Error(
                    "No speech was detected."
                );
            }

            // Put transcript into input
            setInput(transcript);

            // Automatically send transcript
            await sendMessage(
                transcript
            );

        } catch (error) {

            console.error(
                "Transcription error:",
                error
            );

            setVoiceError(
                error.message ||
                    "Could not transcribe your voice."
            );

        } finally {

            setTranscribing(false);
        }
    };

    // -----------------------------------------------------
    // Toggle microphone
    // -----------------------------------------------------

    const toggleVoice = () => {

        if (isRecording) {

            stopRecording();

        } else {

            startRecording();
        }
    };

    // -----------------------------------------------------
    // Keyboard
    // -----------------------------------------------------

    const handleKeyDown = (event) => {

        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {

            event.preventDefault();

            sendMessage();
        }
    };

    // -----------------------------------------------------
    // Clear conversation
    // -----------------------------------------------------

    const clearConversation = () => {

        setMessages([
            INITIAL_MESSAGE,
        ]);

        setInput("");

        setVoiceError("");
    };

    // -----------------------------------------------------
    // Action label
    // -----------------------------------------------------

    const getActionLabel = (
        action
    ) => {

        if (
            !action ||
            action === "NONE"
        ) {
            return null;
        }

        return action
            .replaceAll("_", " ")
            .toLowerCase()
            .replace(
                /\b\w/g,
                (letter) =>
                    letter.toUpperCase()
            );
    };

    return (

        <div className="min-h-[calc(100vh-72px)] bg-slate-50">

            <div className="mx-auto flex h-[calc(100vh-72px)] max-w-6xl flex-col px-4 py-4 sm:px-6 lg:px-8">

                {/* HEADER */}

                <div className="mb-4 flex items-center justify-between">

                    <div className="flex items-center gap-3">

                        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-600 text-2xl text-white shadow-lg shadow-indigo-200">
                            ✨
                        </div>

                        <div>

                            <h1 className="text-xl font-bold text-slate-900 sm:text-2xl">
                                MemoMate AI
                            </h1>

                            <div className="flex items-center gap-2 text-xs text-slate-500">

                                <span className="h-2 w-2 rounded-full bg-emerald-500" />

                                AI assistant ready

                            </div>

                        </div>

                    </div>

                    <button
                        onClick={
                            clearConversation
                        }
                        className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100"
                    >
                        Clear
                    </button>

                </div>

                {/* CHAT */}

                <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-xl">

                    {/* MESSAGES */}

                    <div className="min-h-0 flex-1 overflow-y-auto p-4 sm:p-6">

                        <div className="mx-auto max-w-4xl space-y-5">

                            {messages.map(
                                (
                                    message,
                                    index
                                ) => {

                                    const isUser =
                                        message.role ===
                                        "user";

                                    const actionLabel =
                                        getActionLabel(
                                            message.action
                                        );

                                    return (

                                        <div
                                            key={index}
                                            className={`flex ${
                                                isUser
                                                    ? "justify-end"
                                                    : "justify-start"
                                            }`}
                                        >

                                            <div
                                                className={`flex max-w-[85%] gap-3 ${
                                                    isUser
                                                        ? "flex-row-reverse"
                                                        : ""
                                                }`}
                                            >

                                                <div
                                                    className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-xs font-bold ${
                                                        isUser
                                                            ? "bg-slate-900 text-white"
                                                            : "bg-indigo-100 text-indigo-700"
                                                    }`}
                                                >
                                                    {isUser
                                                        ? "YOU"
                                                        : "✦"}
                                                </div>

                                                <div>

                                                    <div
                                                        className={`rounded-2xl px-4 py-3 text-sm leading-6 ${
                                                            isUser
                                                                ? "rounded-tr-md bg-slate-900 text-white"
                                                                : message.error
                                                                  ? "bg-red-50 text-red-700"
                                                                  : "rounded-tl-md bg-slate-100 text-slate-800"
                                                        }`}
                                                    >
                                                        {
                                                            message.content
                                                        }
                                                    </div>

                                                    {actionLabel && (

                                                        <div className="mt-2 inline-flex rounded-full bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700">

                                                            ✓{" "}
                                                            {
                                                                actionLabel
                                                            }

                                                        </div>

                                                    )}

                                                </div>

                                            </div>

                                        </div>
                                    );
                                }
                            )}

                            {loading && (

                                <div className="flex items-center gap-3">

                                    <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-100 text-indigo-700">
                                        ✦
                                    </div>

                                    <div className="rounded-2xl bg-slate-100 px-4 py-3">

                                        <div className="flex gap-1">

                                            <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400" />

                                            <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:120ms]" />

                                            <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:240ms]" />

                                        </div>

                                    </div>

                                </div>
                            )}

                        </div>

                    </div>

                    {/* QUICK PROMPTS */}

                    <div className="border-t border-slate-100 px-4 pt-3 sm:px-6">

                        <div className="mx-auto max-w-4xl">

                            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
                                Try asking
                            </p>

                            <div className="flex gap-2 overflow-x-auto pb-3">

                                {QUICK_PROMPTS.map(
                                    (prompt) => (

                                        <button
                                            key={prompt}
                                            onClick={() =>
                                                sendMessage(
                                                    prompt
                                                )
                                            }
                                            disabled={
                                                loading ||
                                                transcribing
                                            }
                                            className="shrink-0 rounded-full border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-600 hover:border-indigo-200 hover:bg-indigo-50 hover:text-indigo-700"
                                        >
                                            {prompt}
                                        </button>

                                    )
                                )}

                            </div>

                        </div>

                    </div>

                    {/* VOICE */}

                    <div className="px-4 pb-3 sm:px-6">

                        <div
                            className={`mx-auto flex max-w-4xl items-center justify-between rounded-2xl border px-4 py-3 ${
                                isRecording
                                    ? "border-red-200 bg-red-50"
                                    : transcribing
                                      ? "border-amber-200 bg-amber-50"
                                      : "border-indigo-100 bg-indigo-50"
                            }`}
                        >

                            <div className="flex items-center gap-3">

                                <div
                                    className={`flex h-11 w-11 items-center justify-center rounded-xl text-xl ${
                                        isRecording
                                            ? "bg-red-500 text-white"
                                            : transcribing
                                              ? "bg-amber-500 text-white"
                                              : "bg-indigo-600 text-white"
                                    }`}
                                >
                                    {transcribing
                                        ? "..."
                                        : "🎤"}
                                </div>

                                <div>

                                    <p className="text-sm font-semibold text-slate-800">

                                        {isRecording
                                            ? "Listening..."
                                            : transcribing
                                              ? "Transcribing..."
                                              : "Voice Assistant"}

                                    </p>

                                    <p className="text-xs text-slate-500">

                                        {isRecording
                                            ? "Speak naturally, then tap stop"
                                            : transcribing
                                              ? "MemoMate is converting your voice to text"
                                              : voiceSupported
                                                ? "Tap the microphone and speak"
                                                : "Audio recording is not supported"}

                                    </p>

                                </div>

                            </div>

                            <button
                                type="button"
                                onClick={
                                    toggleVoice
                                }
                                disabled={
                                    loading ||
                                    transcribing
                                }
                                className={`flex h-12 w-12 items-center justify-center rounded-xl text-lg font-bold shadow-md transition ${
                                    isRecording
                                        ? "bg-red-500 text-white shadow-red-200 hover:bg-red-600"
                                        : "bg-indigo-600 text-white shadow-indigo-200 hover:bg-indigo-700"
                                } disabled:opacity-50`}
                            >
                                {isRecording
                                    ? "■"
                                    : "🎤"}
                            </button>

                        </div>

                    </div>

                    {/* VOICE ERROR */}

                    {voiceError && (

                        <div className="px-4 pb-3 sm:px-6">

                            <div className="mx-auto max-w-4xl rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">

                                ⚠️{" "}
                                {voiceError}

                            </div>

                        </div>
                    )}

                    {/* INPUT */}

                    <div className="border-t border-slate-200 bg-slate-50 p-3 sm:p-4">

                        <div className="mx-auto max-w-4xl">

                            <div className="flex items-end gap-2 rounded-2xl border border-slate-200 bg-white p-2 shadow-sm focus-within:border-indigo-300">

                                <textarea
                                    value={input}
                                    onChange={(event) =>
                                        setInput(
                                            event.target.value
                                        )
                                    }
                                    onKeyDown={
                                        handleKeyDown
                                    }
                                    disabled={
                                        loading ||
                                        transcribing
                                    }
                                    rows={1}
                                    placeholder="Type your request..."
                                    className="min-h-[44px] flex-1 resize-none border-0 bg-transparent px-2 py-2.5 text-sm outline-none placeholder:text-slate-400"
                                />

                                <button
                                    type="button"
                                    onClick={() =>
                                        sendMessage()
                                    }
                                    disabled={
                                        !input.trim() ||
                                        loading ||
                                        transcribing
                                    }
                                    className="flex h-11 w-11 items-center justify-center rounded-xl bg-indigo-600 text-lg text-white shadow-md hover:bg-indigo-700 disabled:bg-slate-200 disabled:text-slate-400"
                                >
                                    ↑
                                </button>

                            </div>

                            <div className="mt-2 flex justify-between px-1 text-[11px] text-slate-400">

                                <span>
                                    Enter to send
                                </span>

                                <span>
                                    🎤 Backend Whisper voice
                                </span>

                            </div>

                        </div>

                    </div>

                </div>

            </div>

        </div>
    );
}

export default Assistant;