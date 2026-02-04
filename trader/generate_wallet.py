#!/usr/bin/env python3
"""
Generate a new Ethereum wallet
For the Hyperliquid trading bot
"""
from eth_account import Account
import secrets

def generate_wallet():
    """Generate a new wallet"""
    # Generate a random private key
    private_key = "0x" + secrets.token_hex(32)

    # Create an account from the private key
    account = Account.from_key(private_key)

    print("=" * 60)
    print("🎉 New Wallet Generated!")
    print("=" * 60)
    print(f"\n📍 Wallet Address (wallet_address):")
    print(f"   {account.address}")
    print(f"\n🔑 Private Key (private_key):")
    print(f"   {private_key}")
    print("\n" + "=" * 60)
    print("⚠️  Important Reminder:")
    print("=" * 60)
    print("1. Keep your private key secure and do not share it with anyone")
    print("2. Losing your private key = permanent loss of funds")
    print("3. It is recommended to write down your private key and store it offline")
    print("4. Transfer a small amount of funds to this address for testing")
    print("5. Hyperliquid requires funds on the Arbitrum network")
    print("=" * 60)

    # Save to file
    save = input("\nSave to wallet_info.txt? (y/n): ")
    if save.lower() == 'y':
        with open('wallet_info.txt', 'w') as f:
            f.write(f"Wallet Address: {account.address}\n")
            f.write(f"Private Key: {private_key}\n")
            f.write(f"\n⚠️ WARNING: Keep this file secure and delete after copying to config.json\n")
        print("✅ Saved to wallet_info.txt")
        print("⚠️  Please delete this file after copying the information!")

if __name__ == "__main__":
    print("\n🔐 Ethereum Wallet Generator")
    print("For the Hyperliquid trading bot\n")

    confirm = input("Confirm wallet generation? (yes/no): ")
    if confirm.lower() == 'yes':
        generate_wallet()
    else:
        print("Cancelled")
