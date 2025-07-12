def handle_client(client_id, newsocket, main_window, clients):
    try:
        while True:
            try:
                data = newsocket.recv(4096).decode()
            except Exception as e:
                print(f"[!] Error decoding data from {client_id}: {e}")
                break

            if data:
                print(f"[+] Data from {client_id}: {data.strip()}")
                main_window.handle_received_data(data.strip(), client_id)
            else:
                break
    except Exception as e:
        print(f"[!] Error handling data from client {client_id}: {e}")
    finally:
        if client_id in clients:
            del clients[client_id]
        print(f"[-] Client {client_id} disconnected")
        main_window.handle_client_disconnection(client_id)