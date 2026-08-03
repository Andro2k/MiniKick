# Walkthrough - WT-1.4.7_02: Fix Intermittent TTS Audio Cut-Off & Skipped Messages

Fix intermittent TTS audio playback issues in `MiniKick` where audio streams were being cut off mid-sentence or skipped entirely during active Kick chat streams.

---

## 1. Summary of Changes

### Backend - Text-to-Speech Engine & Message Filtering

#### [backend/providers/voices/tts_online.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/voices/tts_online.py)
- **Isolated `QMediaPlayer` Instances**: Removed the shared `self.player` attribute. Created dedicated per-playback `QMediaPlayer` and `QAudioOutput` instances inside `_play_audio_file()`. This prevents subsequent audio playbacks from interrupting active streams via `setSource()`.
- **`QMediaPlayer.MediaStatus.EndOfMedia` Integration**: Enhanced event loop termination criteria to listen for `EndOfMedia`, `InvalidMedia`, `NoMedia`, and `StoppedState` to ensure clean exit of `QEventLoop.exec()`.
- **Emoji and Unicode Symbol Support**: Updated `_is_speakable_text()` to accept any non-empty whitespace-trimmed string (`bool(text and text.strip())`), allowing Microsoft Edge TTS to natively pronounce emojis (e.g. `👍`, `❤️`) and symbols instead of discarding the message.
- **Resilient Retry Mechanism**: Implemented up to 3 download attempts with exponential backoff in `_async_prepare()` and `_async_speak()` to tolerate transient network latencies and connection drops with Microsoft Edge TTS servers.

#### [backend/handlers/chat_filter_handler.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/handlers/chat_filter_handler.py)
- **Kick Emote Name Preservation**: Updated `_EMOTE_REGEX` from `r"\[emote:[^\]]+\]"` to `r"\[emote:(?:\d+:)?([^\]]+)\]"` and updated `clean_message_for_tts()` to replace emote tags with their human-readable name (`\1`). Emote-only messages (e.g., `[emote:12345:kekw]`) now speak the emote name (`"kekw"`) instead of being reduced to empty strings and skipped.

---

## 2. Big-O & Architecture Compliance

- **Separation of Responsibilities**: TTS playback isolation remains encapsulated within `WebTTSProvider`, and chat filter string processing remains within `ChatFilterHandler`.
- **Big-O Efficiency**: Emote cleaning uses single-pass regular expression matching ($O(N)$ where $N$ is text length).
- **Resource Management**: All `QMediaPlayer` and `QAudioOutput` instances are explicitly stopped and scheduled for deletion (`deleteLater()`) upon playback completion.

---

## 3. Verification & Results

- **Emote Messages**: Messages consisting exclusively of Kick emotes are converted to text names and spoken seamlessly.
- **Emoji Messages**: Emojis are retained and spoken natively by Microsoft Edge TTS.
- **Concurrent Audio Playback**: Successive chat messages play completely without cutting off preceding audio streams.
