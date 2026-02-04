#!/usr/bin/env python3
"""
Telegram Configuration Helper
Helps you obtain the Bot Token and Chat ID
"""
import requests
import json
import time

print("=" * 60)
print("🤖 Telegram Notification Configuration Helper")
print("=" * 60)

print("""
Step 1: Create a Telegram Bot
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Search for @BotFather in Telegram
2. Send the /newbot command
3. Follow the instructions to set the bot name and username
4. BotFather will give you a Token, formatted like:
   123456789:ABCdefGHIjklMNOpqrsTUVwxyz
5. Copy this Token
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

bot_token = input("Enter your Bot Token: ").strip()

if not bot_token:
    print("❌ Token cannot be empty")
    exit(1)

print(f"\n✅ Bot Token: {bot_token[:20]}...")

print("""
Step 2: Get the Chat ID
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Search for the bot you just created in Telegram
2. Click Start or send any message to the bot
3. Press Enter to continue...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

input("Press Enter to continue...")

# Fetch updates
try:
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    response = requests.get(url, timeout=10)
    data = response.json()

    if not data.get('ok'):
        print(f"❌ Failed to fetch updates: {data.get('description')}")
        exit(1)

    updates = data.get('result', [])

    if not updates:
        print("❌ No messages found. Please ensure:")
        print("1. You have sent a message to the bot in Telegram")
        print("2. The Bot Token is correct")
        exit(1)

    # Get the latest chat_id
    chat_id = str(updates[-1]['message']['chat']['id'])
    username = updates[-1]['message']['from'].get('username', 'Unknown')

    print(f"\n✅ Found user: @{username}")
    print(f"✅ Chat ID: {chat_id}")

    # Test sending a message
    print("\nTesting message sending...")
    test_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    test_payload = {
        "chat_id": chat_id,
        "text": "🎉 Congratulations! Telegram notification setup is successful!\n\nThe trading bot is ready."
    }

    test_response = requests.post(test_url, json=test_payload, timeout=10)

    if test_response.json().get('ok'):
        print("✅ Test message sent successfully! Check Telegram.")
    else:
        print(f"⚠️ Test message failed: {test_response.json()}")

    # Output configuration
    print("\n" + "=" * 60)
    print("📝 Configuration Information")
    print("=" * 60)
    print("\nAdd the following content to the telegram section of config.json:\n")

    telegram_config = {
        "enabled": True,
        "bot_token": bot_token,
        "chat_id": chat_id,
        "notify_startup": True,
        "notify_signals": True,
        "notify_trades": True,
        "notify_closures": True,
        "notify_errors": True,
        "notify_daily_summary": True
    }

    print(json.dumps({"telegram": telegram_config}, indent=2))

    print("\n" + "=" * 60)

    # Ask if config.json should be updated automatically
    update_config = input("\nDo you want to automatically update config.json? (y/n): ").strip().lower()

    if update_config == 'y':
        try:
            # Read existing config
            with open('config.json', 'r') as f:
                config = json.load(f)

            # Update telegram config
            config['telegram'] = telegram_config

            # Write back to file
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=2)

            print("✅ config.json updated!")

        except FileNotFoundError:
            print("⚠️ config.json not found. Please create it manually.")
        except Exception as e:
            print(f"❌ Update failed: {e}")
            print("Please manually copy the above configuration to config.json")
    else:
        print("Please manually copy the above configuration to config.json")

    print("\n" + "=" * 60)
    print("🎉 Configuration complete!")
    print("=" * 60)
    print("\nYou can now run the trading bot, and it will automatically send Telegram notifications!")

except requests.exceptions.RequestException as e:
    print(f"❌ Network request failed: {e}")
    print("Please check your network connection")
except Exception as e:
    print(f"❌ Error: {e}")
