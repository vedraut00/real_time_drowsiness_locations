#!/usr/bin/env python3
"""
Simple Telegram Bot Setup for Drowsiness Detection
"""

import json
import requests
import os

def test_bot_token(token):
    """Test if bot token is valid"""
    try:
        url = f"https://api.telegram.org/bot{token}/getMe"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data.get('result', {})
                return True, bot_info.get('username', 'Unknown')
        return False, "Invalid token"
    except Exception as e:
        return False, str(e)

def get_chat_id(token):
    """Get recent chat IDs"""
    try:
        url = f"https://api.telegram.org/bot{token}/getUpdates"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                updates = data.get('result', [])
                chat_ids = []
                for update in updates[-5:]:  # Last 5 updates
                    if 'message' in update:
                        chat = update['message']['chat']
                        chat_ids.append({
                            'id': chat['id'],
                            'type': chat['type'],
                            'name': chat.get('first_name', chat.get('title', 'Unknown'))
                        })
                return chat_ids
        return []
    except Exception as e:
        print(f"Error getting chat IDs: {e}")
        return []

def main():
    print("🤖 Telegram Bot Setup for Drowsiness Detection")
    print("=" * 50)
    
    # Use the configured bot token
    bot_token = "8403007470:AAGtV8866_V1v3pZHAVXpVxz0fjFY2CPCxs"
    
    print("\n1️⃣ Using Configured Bot")
    print("🔍 Testing bot connection...")
    valid, info = test_bot_token(bot_token)
    
    if valid:
        print(f"✅ Bot connected successfully!")
        print(f"🤖 Bot username: @{info}")
        print(f"🔗 Bot link: t.me/{info}")
    else:
        print(f"❌ Bot connection failed: {info}")
        print("Please check your internet connection and try again.")
        return
    
    # Get chat IDs
    print("\n2️⃣ Setting Up Recipients")
    print("📱 IMPORTANT: Anyone who wants to receive alerts must:")
    print(f"   • Find your bot by username: @{info}")
    print("   • Send ANY message to the bot (like 'hello' or '/start')")
    print("   • Then we can detect their chat ID")
    
    # Start with your configured chat ID
    selected_chats = ["1569080701"]  # Your chat ID
    print(f"\n✅ Your chat ID ({selected_chats[0]}) is already configured")
    print("   This is from your bot creation details")
    
    add_more = input("\nDo you want to add more recipients? (y/n): ").lower()
    
    if add_more == 'y' or not selected_chats:
        if not selected_chats:
            print("\nNo existing recipients found. Let's add some!")
        
        input("\nMake sure all recipients have messaged your bot, then press Enter...")
        
        print("🔍 Looking for recent messages...")
        chat_ids = get_chat_id(bot_token)
        
        if not chat_ids:
            print("❌ No recent messages found!")
            print("Make sure recipients have:")
            print("   • Started a chat with your bot")
            print("   • Sent at least one message")
            if not selected_chats:
                chat_id = input("Enter a chat ID manually: ").strip()
                if chat_id:
                    selected_chats = [chat_id]
        else:
            print("\n📱 Found recent chats:")
            for i, chat in enumerate(chat_ids, 1):
                print(f"   {i}. {chat['name']} (ID: {chat['id']}, Type: {chat['type']})")
            
            print("\n🎯 Select recipients for emergency alerts:")
            print("   • Enter numbers separated by commas (e.g., 1,3,5)")
            print("   • Or press Enter to keep existing recipients only")
            
            selection = input("Select chats: ").strip()
            
            if selection:
                # Parse selection
                try:
                    indices = [int(x.strip()) - 1 for x in selection.split(',')]
                    for idx in indices:
                        if 0 <= idx < len(chat_ids):
                            chat_id = str(chat_ids[idx]['id'])
                            if chat_id not in selected_chats:
                                selected_chats.append(chat_id)
                                print(f"✅ Added: {chat_ids[idx]['name']}")
                            else:
                                print(f"⚠️ Already included: {chat_ids[idx]['name']}")
                        else:
                            print(f"❌ Invalid choice: {idx + 1}")
                except ValueError:
                    print("❌ Invalid format, keeping existing recipients")
    
    if not selected_chats:
        print("❌ No recipients configured!")
        return
    
    print(f"\n📱 Total recipients configured: {len(selected_chats)}")
    
    # Emergency threshold
    print("\n3️⃣ Emergency Settings")
    while True:
        try:
            threshold = float(input("Emergency threshold in seconds (default 4.0): ") or "4.0")
            if threshold > 0:
                break
            else:
                print("❌ Threshold must be positive")
        except ValueError:
            print("❌ Please enter a valid number")
    
    # Save configuration
    config = {
        "bot_token": bot_token,
        "chat_ids": selected_chats,  # Multiple chat IDs
        "emergency_threshold": threshold
    }
    
    config_file = "telegram_config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n✅ Configuration saved to {config_file}")
    print(f"📱 {len(selected_chats)} recipient(s) configured")
    
    # Test alert
    test = input("\n🧪 Send test alert to all recipients? (y/n): ").lower()
    if test == 'y':
        success_count = 0
        for chat_id in selected_chats:
            try:
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                message = (
                    "🧪 <b>Test Alert</b>\n\n"
                    "✅ Your Telegram bot is configured correctly!\n"
                    "🚗 Drowsiness detection alerts are now active."
                )
                data = {
                    'chat_id': chat_id,
                    'text': message,
                    'parse_mode': 'HTML'
                }
                response = requests.post(url, data=data, timeout=10)
                
                if response.status_code == 200:
                    success_count += 1
                else:
                    print(f"❌ Test failed for chat ID: {chat_id}")
                    
            except Exception as e:
                print(f"❌ Test failed for chat ID {chat_id}: {e}")
        
        print(f"✅ Test alerts sent to {success_count}/{len(selected_chats)} recipients!")
    
    print("\n🎉 Setup complete!")
    print("📋 Summary:")
    print(f"   • Bot: @{info}")
    print(f"   • Recipients: {len(selected_chats)}")
    print(f"   • Threshold: {threshold}s")
    print("\n💡 To add more recipients later:")
    print("   1. Have them message your bot")
    print("   2. Run this setup again")

if __name__ == "__main__":
    main()