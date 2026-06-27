# backend\config\default_en_locale.py

DEFAULT_DICTIONARY = {
    "settings": {
        "header": {
            "title": "General Settings",
            "subtitle": "Global system settings, account management, and updates."
        },
        "system": {
            "tray_title": "Run in Background",
            "tray_desc": "Minimize to the system tray instead of fully closing the application.",
            "lang_title": "Application Language",
            "lang_desc": "Select the interface language (requires restart).",
            "update_title": "Software Updates",
            "update_desc": "Check for and install new MiniKick versions.",
            "btn_update": "Check for updates"
        },
        "backup": {
            "title": "Configuration Backup",
            "desc": "Export or import your rewards, voices, and general settings.",
            "btn_export": "Export",
            "btn_import": "Import"
        },
        "account": {
            "title": "Unlink Account",
            "desc": "Close the current session. You will need to re-authorize MiniKick next time.",
            "btn_unlink": "Unlink"
        },
        "dialogs": {
            "export_title": "Export Configuration",
            "import_title": "Import Configuration"
        },
        "status": {
            "tray_enabled": "Background Execution On",
            "tray_enabled_msg": "MiniKick will minimize to the tray when closed.",
            "tray_disabled": "Background Execution Off",
            "tray_disabled_msg": "The application will exit completely when closed.",
            "exported": "Backup Exported",
            "exported_msg": "Your settings have been saved successfully.",
            "imported": "Backup Restored",
            "imported_msg": "Settings have been loaded successfully.",
            "lang_changed": "Language Changed",
            "lang_changed_msg": "Please restart the application to apply the new language.",
            "unlinked": "Account Unlinked",
            "unlinked_msg": "Your local Kick session has been closed.",
            "error_title": "Operation Failed",
            "export_error": "Could not save the backup file.",
            "import_error": "The backup file is corrupted or incompatible."
        }
    },
    "spam": {
        "header": {
            "title": "Anti-Spam Filters (Auto-Mod)",
            "subtitle": "Use these filters to keep your chat friendly, fun, and toxicity-free."
        },
        "card": {
            "config_title": "Penalty Configuration",
            "action": "Action",
            "action_timeout": "Timeout user",
            "action_delete": "Delete message",
            "duration": "Duration (seconds)",
            "exclude": "Exclude rank (Immune)",
            "exclude_none": "None",
            "exclude_mod": "Moderators & Broadcaster",
            "exclude_sub": "Subscribers & VIPs",
            "max_amount": "Maximum allowed amount"
        },
        "filters": {
            "caps": {
                "title": "Caps Protection",
                "desc": "Removes messages with an excessive amount of uppercase letters."
            },
            "link": {
                "title": "Link Protection",
                "desc": "Removes messages containing unauthorized links."
            },
            "emote": {
                "title": "Emote Protection",
                "desc": "Removes messages that abuse the amount of emotes."
            },
            "paragraph": {
                "title": "Walls of Text",
                "desc": "Blocks excessively long messages (Many characters)."
            },
            "symbol": {
                "title": "Symbol Protection",
                "desc": "Removes messages with excessive use of symbols (Ex: @#!%)."
            }
        }
    },
    "command": {
        "header": {
            "title": "Triggers and Command Responses",
            "subtitle": "Link chat commands or regular expressions to automated bot responses."
        },
        "table": {
            "title": "Linked Commands",
            "search_placeholder": "Search linked command...",
            "btn_new": "New Command",
            "col_command": "Command",
            "col_aliases": "Aliases / Regex",
            "col_permission": "Access Level",
            "col_actions": "Actions",
            "regex_prefix": "Regex",
            "tooltip_edit": "Modify command configuration",
            "tooltip_delete": "Delete command permanently"
        },
        "dialog": {
            "title": "Configure Command",
            "subtitle": "Create or edit custom commands for your chat.",
            "trigger_label": "Command Name (Ex: !discord):",
            "response_label": "Bot Response (you can use {user}):",
            "cooldown_label": "Cooldown (sec):",
            "permission_label": "Minimum Permission:",
            "perm_everyone": "Everyone",
            "perm_subscriber": "Subscriber",
            "perm_vip": "VIP",
            "perm_moderator": "Moderator",
            "perm_broadcaster": "Broadcaster",
            "active_checkbox": "Active Command",
            "aliases_label": "Standard Aliases (comma separated):",
            "aliases_placeholder": "!dc, !discord server",
            "regex_checkbox": "Use RegEx (Ignores Prefixes and Aliases)",
            "regex_label": "Regular Expression Syntax:",
            "regex_placeholder": "Ex: \\b(hello|hi)\\b",
            "regex_help": "If you enable RegEx, the bot will search for this pattern anywhere in the message.",
            "tab_basic": "Basic",
            "tab_advanced": "Advanced",
            "btn_save": "Save Command",
            "btn_cancel": "Cancel"
        },
        "status": {
            "created": "Command Created",
            "updated": "Command Updated",
            "deleted": "Command Deleted",
            "enabled": "Command Enabled",
            "disabled": "Command Disabled",
            "created_msg": "Available in chat: {trigger}",
            "updated_msg": "Changes saved for: {trigger}",
            "deleted_msg": "Deleted: {trigger}",
            "toggled_msg": "Trigger word: {trigger}"
        }
    },
    "rewards": {
        "header": {
            "title": "Triggers & Rewards",
            "subtitle": "Link your channel rewards with on-screen multimedia elements."
        },
        "obs": {
            "title": "OBS Browser Source",
            "desc": "Copy this link and paste it into your broadcasting software (Recommended resolution: 1920x1080).",
            "copied": "Link Copied!"
        },
        "table": {
            "title": "Linked Rewards",
            "btn_new": "New Rewards",
            "col_reward": "Kick Reward",
            "col_file": "File",
            "col_actions": "Actions",
            "unknown_file": "Unknown",
            "tooltip_play": "Test in OBS",
            "tooltip_edit": "Modify settings",
            "tooltip_delete": "Delete Rewards"
        },
        "dialogs": {
            "visual": {
                "title": "Visual Positioner (1920x1080)",
                "desc": "Drag your rewards. When you release it, a preview will be shown in OBS.",
                "btn_save": "Save and Close"
            },
            "wizard": {
                "title_edit": "Edit Rewards",
                "title_new": "New Rewards",
                "btn_cancel": "Cancel",
                "btn_next": "Next",
                "btn_back": "Back",
                "btn_save": "Save Rewards",
                "file_dialog_title": "Multimedia",
                "file_dialog_filter": "Media (*.mp4 *.webm *.mp3 *.wav *.ogg *.gif *.png *.jpg);;All (*.*)",
                "step1": {
                    "title": "Reward and File",
                    "desc": "Configure which channel point will trigger this rewards.",
                    "reward_selection": "Reward Selection",
                    "loading": "Loading rewards...",
                    "tooltip_refresh": "Refresh Kick Rewards",
                    "file_label": "Multimedia File",
                    "file_placeholder": "Ex. your_rewards.mp4 or sound.mp3",
                    "btn_browse": "Browse",
                    "no_rewards": "No rewards",
                    "no_available": "No available rewards"
                },
                "step2": {
                    "title": "Display Settings",
                    "desc": "Define how and where your rewards will be displayed on the canvas.",
                    "volume": "Rewards volume",
                    "random_pos": "Random Position",
                    "btn_visual": "Position in OBS",
                    "coord_x": "X:",
                    "coord_y": "Y:",
                    "scale": "Scale:"
                }
            }
        },
        "status": {
            "created": "Rewards Created",
            "updated": "Rewards Updated",
            "deleted": "Rewards Deleted",
            "created_msg": "Linked to reward: {reward}",
            "updated_msg": "Configuration saved for: {reward}",
            "deleted_msg": "Unlinked reward: {reward}"
        }
    },
    "log": {
        "header": {
            "title": "Developer Logs",
            "subtitle": "Monitor system events, debug errors, and load historical data using the file explorer."
        },
        "controls": {
            "search_placeholder": "Search logs...",
            "filter_all": "ALL",
            "btn_folder": "Folder",
            "tooltip_folder": "Open location in Windows",
            "btn_load": "Load History",
            "btn_live": "Live View",
            "btn_clear": "Clear",
            "btn_report": "Report Bug",
            "btn_show_logs": "View Logs",
            "btn_hide_logs": "Hide Logs"
        },
        "empty": {
            "title": "Console paused",
            "desc": "Events are still being recorded in the background. Press the button to view real-time diagnostics.",
            "btn_show": "View live logs"
        },
        "table": {
            "col_level": "Log Level",
            "col_time": "Timestamp",
            "col_message": "Log Message"
        },
        "dialogs": {
            "select_history": "Select Log History",
            "file_filter": "Log Files (*.log*);;All files (*.*)"
        },
        "misc": {
            "historical": "HISTORICAL"
        },
        "status": {
            "historical_title": "Log File Loaded",
            "historical_msg": "Inspecting: {file}",
            "live_title": "Live Console",
            "live_msg": "Showing real-time event diagnostics.",
            "paused_title": "Live mode",
            "paused_msg": "You returned to live mode. Use 'View Logs' whenever you want to monitor events.",
            "cleared_title": "Logs Cleared",
            "cleared_msg": "The log view has been cleared successfully."
        }
    },
    "chat": {
        "header": {
            "title": "Live Chat",
            "subtitle": "Manage moderation, interactive Text-to-Speech (TTS), and real-time channel events."
        },
        "settings": {
            "tts_title": "Voice Service (TTS)",
            "tts_desc": "Enable automated message reading.",
            "name_title": "Read Names",
            "name_desc": "Pronounce the sender's name before the message.",
            "provider_title": "Premium Voice Engine",
            "provider_desc": "Toggle between Edge web voices or local voices.",
            "cmd_title": "Require Command",
            "cmd_desc": "Only read messages starting with a prefix.",
            "vol_title": "General Volume",
            "vol_desc": "Adjust the intensity of the speech synthesizer.",
            "prefix_title": "Command Prefix",
            "prefix_desc": "Define the exact text that will trigger the bot's reading.",
            "prefix_placeholder": "Ex. !tts"
        },
        "bots": {
            "title": "Muted Users",
            "input_placeholder": "ex. botrix",
            "btn_add": "Add"
        },
        "display": {
            "title": "Room History"
        },
        "status": {
            "loading_voices": "Fetching cloud voices...",
            "provider_title": "Speech Engine",
            "tts_title": "Chat Text-to-Speech"
        }
    },
    "music": {
        "header": {
            "title": "Music Player",
            "subtitle": "Let your viewers control the music stream using chat commands."
        },
        "provider": {
            "name": "Spotify Audio Provider"
        },
        "btn": {
            "connect": "Connect Spotify",
            "disconnect": "Disconnect"
        },
        "status": {
            "disconnected": "Disconnected",
            "connecting": "Authorize in your browser...",
            "active": "Connected as",
            "session_remembered": "Broadcaster (Session remembered)",
            "connected_user": "Broadcaster (Connected)"
        },
        "player": {
            "not_playing": "No song currently playing",
            "paused_title": "Player paused...",
            "paused_desc": "Open Spotify and press Play",
            "unknown_song": "Unknown"
        },
        "cmds": {
            "title": "Viewer Commands",
            "sr_label": "Request Song (Default: !sr)",
            "sr_desc": "Allows viewers to add music to the queue. You can customize the '!sr' trigger in the Commands view.",
            "skip_label": "Skip Track (Default: !skip)",
            "skip_desc": "Forces playback to the next song. You can customize the '!skip' trigger in the Commands view.",
            "song_label": "Current Song (Default: !song)",
            "song_desc": "Displays the currently playing track in chat. You can customize the '!song' trigger in the Commands view.",
            "default_tag_name": "Music Plugin"
        },
        "toast": {
            "title_spotify": "Spotify",
            "connected": "Link with Spotify successfully established.",
            "disconnected": "Spotify account disconnected."
        },
        "chat": {
            "sr_usage": "@{user} please provide a song name. (Ex: {trigger} Torero Chayanne)",
            "not_linked": "❌ The broadcaster has not linked their Spotify account.",
            "skip_success": "⏩ Song skipped successfully.",
            "skip_failed": "❌ Could not skip song (Player paused or queue empty).",
            "song_now_playing": "🎵 Now playing: {title} - {artist}",
            "song_paused": "🔇 Spotify is paused or closed."
        },
        "queue": {
            "not_found": "❌ Could not find any song named '{query}'.",
            "success": "🎵 Added to queue: {track}",
            "no_device": "❌ Error: Please open Spotify on your PC and play any track first.",
            "rejected": "❌ Spotify rejected the request: {status}",
            "error": "❌ Internal Spotify error: {error}"
        },
        "errors": {
            "no_session": "No active Spotify session.",
            "refresh_failed": "Could not refresh Spotify token."
        }
    },
    "spotify": {
        "error": {
            "timeout": "Login timed out or was canceled by user.",
            "generic": "Spotify connection error:"
        }
    },
    "dashboard": {
        "header": {
            "title": "Dashboard",
            "subtitle": "Authentication management, automatic connection, and general system status."
        },
        "banner": {
            "text": "<b>Update required:</b> Your account does not have permissions for the new Anti-Spam features.",
            "btn_update": "Update Permissions"
        },
        "connection": {
            "autostart_title": "Automatic Connection",
            "autostart_desc": "Start the bot automatically.",
            "status_waiting": "Status: Waiting for connection...",
            "status_auth": "Status: Authenticating...",
            "status_connected": "Status: Connected and Listening",
            "status_error": "Error",
            "btn_connect": "Connect to Kick",
            "btn_active": "System Active",
            "btn_retry": "Retry"
        },
        "stats": {
            "followers": "Followers",
            "room_id": "ChatRoom ID",
            "category": "Last Category",
            "affiliate": "Affiliate Status",
            "vods": "VODs"
        },
        "status": {
            "connected": "Connected",
            "connected_toast_msg": "Channel linked: {username}"
        }
    },
    "dialogs": {
        "confirm": {
            "btn_continue": "Continue",
            "btn_cancel": "Cancel"
        }
    },
    "main": {
        "dialogs": {
            "unlink_title": "Unlink Account",
            "unlink_desc": "Are you sure you want to log out? You will need to re-authorize MiniKick next time.",
            "close_title": "Close MiniKick",
            "close_desc": "Are you sure you want to exit the application? The bot will stop listening to the chat.",
            "update": {
                "top_searching": "Searching...",
                "title_default": "System Update",
                "subtitle_connecting": "Connecting to the server...",
                "lbl_progress": "Progress",
                "btn_restart": "Restart now",
                "btn_close": "Close",
                "top_available": "Version {version} available",
                "subtitle_restart_req": "A restart is required to complete the installation.",
                "btn_download": "Download now",
                "subtitle_downloading": "Downloading the new version...",
                "btn_downloading": "Downloading...",
                "title_completed": "Update completed",
                "subtitle_installed": "Version {version} installed.",
                "title_up_to_date": "System Up to Date",
                "subtitle_up_to_date": "Your system version is already the latest available.",
                "top_error": "Update Error",
                "title_error": "Download failed",
                "msg_unexpected_error": "Unexpected failure downloading the file."
            },
            "already_running": {
                "title": "MiniKick is Already Running",
                "desc": "The broadcasting controller is already operating in the background. Please check the Windows system tray (next to the clock) to access the dashboard.",
                "btn_exit": "Exit",
                "btn_understood": "Understood"
            }
        },
        "sidebar": {
            "new_version": "New Version",
            "version": "Version {version}",
            "tabs": {
                "dashboard": "Dashboard",
                "chat": "Chat",
                "music": "Music",
                "triggers": "Triggers",
                "comandos": "Commands",
                "spam_filters": "Spam Filters",
                "settings": "Settings",
                "developer": "Developer"
            }
        },
        "tray": {
            "open_panel": "Open Panel",
            "read_chat": "Read chat aloud",
            "close_app": "Close MiniKick",
            "tts_on": "Enabled",
            "tts_off": "Muted",
            "tts_msg": "Chat reading: {estado}",
            "bg_title": "MiniKick in background",
            "bg_desc": "I will keep reading the chat for you. Double click to return."
        },
        "controllers": {
            "dashboard": {
                "unknown_user": "Unknown",
                "no_bio": "No description",
                "none": "None",
                "affiliate": "Affiliate",
                "not_affiliate": "Not Affiliate",
                "yes": "Yes",
                "no": "No"
            },
            "log": {
                "error_title": "Error",
                "read_error": "Could not read the file: {error}",
                "folder_error": "Could not open the folder: {error}"
            },
            "settings": {
                "export_success_title": "Export successful",
                "export_success_desc": "Your settings have been saved.",
                "error_title": "Error",
                "export_error_desc": "Failed to export the file.",
                "import_success_title": "Import successful",
                "import_success_desc": "Your settings have been restored.",
                "import_error_desc": "The file is corrupt or invalid.",
                "restart_title": "Restart Required",
                "restart_desc": "Please close and reopen MiniKick to apply the new language."
            },
            "chat": {
                "voice_updated": "Voice updated."
            }
        },
        "workers": {
            "auth": {
                "error_failed": "Authorization canceled or failed."
            },
            "chat": {
                "error_room_id": "Could not get the room ID from the API."
            },
            "reward": {
                "unknown_reward": "Unknown Reward",
                "someone": "Someone",
                "batch_success": "Successfully marked {count} redemptions as completed on Kick.",
                "batch_error": "Could not confirm the batch on Kick: {error}",
                "poll_error": "Error querying rewards: {error}"
            }
        },
        "window": {
            "title": "MiniKick - Version {version}"
        },
        "chat": {
            "reward_redeemed": "redeemed {reward_name}",
            "points_tag": "POINTS"
        },
        "logs": {
            "reward_no_rewards": "Reward '{reward_name}' does not have an rewards configured.",
            "automod_sanction": "Message sanctioned by Auto-Mod: {user}: {msg}",
            "api_offline": "Attempted to update rewards without being connected to Kick.",
            "api_fetching": "Rewards are already being fetched. Please wait.",
            "api_error_setup": "Error setting up rewards query: {error}",
            "api_error": "Kick Rewards API failed: {error}",
            "worker_stopping": "Requesting {worker} to stop...",
            "worker_stuck": "{worker} stuck (possible network lock). Forcing termination...",
            "worker_stopped": "{worker} closed cleanly.",
            "shutdown_init": "Initiating shutdown sequence...",
            "shutdown_tts_overlay": "Shutting down TTS and Overlay...",
            "shutdown_complete": "Thread shutdown sequence completed."
        },
        "toasts": {
            "reward_title": "Reward Redeemed",
            "reward_msg": "{user} redeemed: {reward_name}"
        }
    }
}