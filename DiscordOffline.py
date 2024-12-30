import socket
import threading
import subprocess
import json
import time
import os

# === PLACEHOLDER FOR BANNER ===
BANNER = r"""
 ________  ___  ________  ________  ________  ________  ________          ________  ________ ________ ___       ___  ________   _______      
|\   ___ \|\  \|\   ____\|\   ____\|\   __  \|\   __  \|\   ___ \        |\   __  \|\  _____\\  _____\\  \     |\  \|\   ___  \|\  ___ \     
\ \  \_|\ \ \  \ \  \___|\ \  \___|\ \  \|\  \ \  \|\  \ \  \_|\ \       \ \  \|\  \ \  \__/\ \  \__/\ \  \    \ \  \ \  \\ \  \ \   __/|    
 \ \  \ \\ \ \  \ \_____  \ \  \    \ \  \\\  \ \   _  _\ \  \ \\ \       \ \  \\\  \ \   __\\ \   __\\ \  \    \ \  \ \  \\ \  \ \  \_|/__  
  \ \  \_\\ \ \  \|____|\  \ \  \____\ \  \\\  \ \  \\  \\ \  \_\\ \       \ \  \\\  \ \  \_| \ \  \_| \ \  \____\ \  \ \  \\ \  \ \  \_|\ \ 
   \ \_______\ \__\____\_\  \ \_______\ \_______\ \__\\ _\\ \_______\       \ \_______\ \__\   \ \__\   \ \_______\ \__\ \__\\ \__\ \_______\
    \|_______|\|__|\_________\|_______|\|_______|\|__|\|__|\|_______|        \|_______|\|__|    \|__|    \|_______|\|__|\|__| \|__|\|_______|
                  \|_________|                                                                                                              
"""

DISCLAIMER = "This is not affiliated with Discord. This is an alternative."

# UDP Broadcast for server discovery
BROADCAST_PORT = 54321
DISCOVERY_MESSAGE = "DISCOVER_SERVERS"
SERVER_LIST = []  # Keeps track of discovered servers
HOST = "0.0.0.0"

# === SERVER CODE ===
def broadcast_server(server_name, server_port):
    """Broadcast the server's presence periodically."""
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    while True:
        server_info = json.dumps({"name": server_name, "port": server_port})
        udp_socket.sendto(server_info.encode("utf-8"), ("<broadcast>", BROADCAST_PORT))
        time.sleep(5)  # Broadcast every 5 seconds


def handle_client(client_socket, username, client_addr):
    """Handles messages from a connected client."""
    try:
        while True:
            message = client_socket.recv(1024).decode("utf-8")
            if message:
                print(f"[{username}]: {message}")
                broadcast(f"[{username}]: {message}")
    except ConnectionResetError:
        print(f"{username} has disconnected.")
    finally:
        client_socket.close()


def broadcast(message):
    """Send a message to all connected clients."""
    for client_socket in client_sockets:
        try:
            client_socket.send(message.encode("utf-8"))
        except:
            continue


def server():
    """Start the server and listen for connections."""
    server_name = input("Enter a name for your server: ")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, 0))
    server_port = server_socket.getsockname()[1]  # Get assigned port
    print(f"Server '{server_name}' started on port {server_port}")

    threading.Thread(target=broadcast_server, args=(server_name, server_port), daemon=True).start()
    server_socket.listen(5)

    while True:
        client_socket, addr = server_socket.accept()
        username = client_socket.recv(1024).decode("utf-8")
        print(f"{username} joined the server.")
        client_sockets.append(client_socket)
        broadcast(f"{username} has joined the chat!")
        threading.Thread(target=handle_client, args=(client_socket, username, addr), daemon=True).start()


# === CLIENT CODE ===
def discover_servers():
    """Discover available servers via UDP broadcast."""
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp_socket.settimeout(3)
    udp_socket.bind(("", BROADCAST_PORT))

    print("Discovering servers...")
    try:
        start_time = time.time()
        while time.time() - start_time < 3:  # Wait for 3 seconds to collect responses
            try:
                data, addr = udp_socket.recvfrom(1024)
                server_info = json.loads(data.decode("utf-8"))
                SERVER_LIST.append((server_info["name"], addr[0], server_info["port"]))
            except socket.timeout:
                break
    finally:
        udp_socket.close()


def client():
    """Start the client and connect to a server."""
    global SERVER_LIST
    while True:
        SERVER_LIST.clear()
        discover_servers()

        if not SERVER_LIST:
            print("No servers found.")
            retry = input("Do you want to search again? (yes/no): ").strip().lower()
            if retry == "no":
                print("Exiting client...")
                return
            else:
                continue

        print("\nAvailable servers:")
        for i, (name, ip, port) in enumerate(SERVER_LIST):
            print(f"{i + 1}. {name} ({ip}:{port})")

        try:
            choice = int(input("\nSelect a server to join (or 0 to search again): "))
        except ValueError:
            print("Invalid input. Please enter a number.")
            continue

        if choice == 0:
            continue

        if choice < 1 or choice > len(SERVER_LIST):
            print("Invalid choice. Please select a valid server.")
            continue

        server_name, server_ip, server_port = SERVER_LIST[choice - 1]
        username = input("Enter your username: ")

        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((server_ip, server_port))
            client_socket.send(username.encode("utf-8"))

            os.system('cls' if os.name == 'nt' else 'clear')  # Clear the screen
            print(f"Connected to '{server_name}'. Type '/quit' to exit.\n")

            def receive_messages():
                """Receive messages from the server."""
                while True:
                    try:
                        message = client_socket.recv(1024).decode("utf-8")
                        if message:
                            print(message)
                    except:
                        print("Disconnected from the server.")
                        break

            threading.Thread(target=receive_messages, daemon=True).start()

            while True:
                message = input()
                if message.lower() == "/quit":
                    print("Exiting...")
                    break
                client_socket.send(message.encode("utf-8"))

        except ConnectionRefusedError:
            print("Failed to connect to the server.")
        finally:
            client_socket.close()


# === MAIN MENU ===
def display_menu():
    print(BANNER)
    print(DISCLAIMER)
    print("\nWelcome to Discord Offline!")
    print("1. Start a Server")
    print("2. Start as Client")
    print("3. Exit")
    choice = input("Enter your choice: ")

    if choice == "1":
        subprocess.Popen(["start", "cmd", "/k", "python", __file__, "server"], shell=True)
    elif choice == "2":
        client()
    elif choice == "3":
        print("Goodbye!")
        exit()
    else:
        print("Invalid choice.")
        display_menu()


if __name__ == "__main__":
    import sys

    client_sockets = []
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        server()
    else:
        display_menu()

