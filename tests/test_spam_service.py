# tests\test_spam_service.py

from backend.services.chat.spam_service import SpamService

def test_kick_emote_removal(spam_storage, i18n):
    service = SpamService(storage=spam_storage, i18n=i18n)
    raw_msg = "Hello [emote:5748018:collectiblesWideGooseJAM] world!"
    clean_msg = service._KICK_EMOTE_REGEX.sub('', raw_msg)
    assert "[emote:" not in clean_msg
    assert "Hello  world!" == clean_msg

def test_symbol_protection_ignores_emotes(spam_storage, i18n):
    service = SpamService(storage=spam_storage, i18n=i18n)
    service.save_filter("symbol_protection", {
        "is_active": True,
        "max_amount": 5,
        "penalty": "timeout",
        "duration": 30,
        "exclude_group": "none"
    })
    emote_msg = "[emote:1:test1] [emote:2:test2] [emote:3:test3]"
    blocked = service.is_spam(user="user1", message=emote_msg, badges=[], msg_id="1", sender_id=100)
    assert not blocked

def test_symbol_protection_triggers_on_excess_symbols(spam_storage, i18n):
    service = SpamService(storage=spam_storage, i18n=i18n)
    service.save_filter("symbol_protection", {
        "is_active": True,
        "max_amount": 3,
        "penalty": "timeout",
        "duration": 60,
        "exclude_group": "none"
    })
    spam_msg = "Wat????!!!! $$$$ ░░░░"
    blocked = service.is_spam(user="spammer", message=spam_msg, badges=[], msg_id="2", sender_id=101)
    assert blocked

def test_paragraph_protection_length_limit(spam_storage, i18n):
    service = SpamService(storage=spam_storage, i18n=i18n)
    service.save_filter("paragraph_protection", {
        "is_active": True,
        "max_amount": 50,
        "penalty": "delete",
        "duration": 0,
        "exclude_group": "none"
    })
    long_msg = "A" * 60
    blocked = service.is_spam(user="long_user", message=long_msg, badges=[], msg_id="3", sender_id=102)
    assert blocked

def test_platform_specific_spam_filtering(spam_storage, i18n):
    service = SpamService(storage=spam_storage, i18n=i18n)
    service.save_filter("caps_protection", {
        "is_active": True,
        "max_amount": 3,
        "penalty": "timeout",
        "duration": 5,
        "exclude_group": "none",
        "apply_kick": True,
        "apply_twitch": False
    })

    caps_msg = "HELLO WORLD THIS IS CAPS"
    assert service.is_spam(user="user_kick", message=caps_msg, badges=[], msg_id="k1", sender_id=1, platform="kick")
    assert not service.is_spam(user="user_twitch", message=caps_msg, badges=[], msg_id="t1", sender_id=2, platform="twitch")
    service.save_filter("caps_protection", {
        "is_active": True,
        "max_amount": 3,
        "penalty": "timeout",
        "duration": 5,
        "exclude_group": "none",
        "apply_kick": False,
        "apply_twitch": True
    })
    assert not service.is_spam(user="user_kick", message=caps_msg, badges=[], msg_id="k2", sender_id=3, platform="kick")
    assert service.is_spam(user="user_twitch", message=caps_msg, badges=[], msg_id="t2", sender_id=4, platform="twitch")

def test_caps_protection_ignores_emotes(spam_storage, i18n):
    service = SpamService(storage=spam_storage, i18n=i18n)
    service.save_filter("caps_protection", {
        "is_active": True,
        "max_amount": 2,
        "penalty": "timeout",
        "duration": 5,
        "exclude_group": "none",
        "apply_kick": True,
        "apply_twitch": True
    })

    emote_msg = "[emote:1:WideGooseJAM] [emote:2:WideGooseJAM] [emote:3:WideGooseJAM] [emote:4:WideGooseJAM] [emote:5:WideGooseJAM]"
    assert not service.is_spam(user="user1", message=emote_msg, badges=[], msg_id="e1", sender_id=10, platform="kick")
