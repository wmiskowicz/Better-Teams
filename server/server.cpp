#include <iostream>
#include <thread>
#include <vector>
#include <map>
#include <mutex>
#include <cstring>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <QTcpServer>
#include <QTcpSocket>
#include <chrono>
#include <iomanip>
#include <sstream>

#define PORT 54000

std::map<std::string, int> clients;
std::mutex clients_mutex;
std::mutex log_mutex;

void broadcastUserList()
{
    std::lock_guard<std::mutex> lock(clients_mutex);

    std::string list = "USERS:";
    for (auto &c : clients)
    {
        list += c.first + ",";
    }

    for (auto &c : clients)
    {
        send(c.second, list.c_str(), list.size(), 0);
    }
}

std::string now()
{
    auto t = std::time(nullptr);
    std::tm tm{};
    localtime_s(&tm, &t);

    std::ostringstream oss;
    oss << std::put_time(&tm, "%H:%M:%S");
    return oss.str();
}

void log(const std::string &msg)
{
    std::lock_guard<std::mutex> lock(log_mutex);
    std::cout << "[" << now() << "] " << msg << std::endl;
}

void handleClient(int clientSocket)
{
    char buffer[1024];
    std::string username;

    while (true)
    {
        memset(buffer, 0, sizeof(buffer));
        int bytes = recv(clientSocket, buffer, sizeof(buffer), 0);

        if (bytes <= 0)
            break;

        std::string msg(buffer);

        if (msg.rfind("REGISTER:", 0) == 0)
        {
            username = msg.substr(9);

            {
                std::lock_guard<std::mutex> lock(clients_mutex);
                clients[username] = clientSocket;
            }

            log("User connected: " + username);
            broadcastUserList();
        }
        else if (msg.rfind("MSG:", 0) == 0)
        {
            // format: MSG:target:message
            size_t first = msg.find(':', 4);
            std::string target = msg.substr(4, first - 4);
            std::string text = msg.substr(first + 1);

            std::lock_guard<std::mutex> lock(clients_mutex);

            if (clients.count(target))
            {
                std::string out = "FROM:" + username + ":" + text;
                send(clients[target], out.c_str(), out.size(), 0);

                log("MSG " + username + " -> " + target + ": " + text);
            }
            else
            {
                log("MSG FAILED " + username + " -> " + target + ": user not found");
            }
        }
    }

    {
        std::lock_guard<std::mutex> lock(clients_mutex);
        clients.erase(username);
    }

    log("User disconnected: " + username);
    broadcastUserList();
    closesocket(clientSocket);
}

int main()
{
    WSADATA wsaData;
    WSAStartup(MAKEWORD(2, 2), &wsaData);

    int serverSocket = socket(AF_INET, SOCK_STREAM, 0);

    sockaddr_in serverAddr{};
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_port = htons(PORT);
    serverAddr.sin_addr.s_addr = INADDR_ANY;

    bind(serverSocket, (sockaddr *)&serverAddr, sizeof(serverAddr));
    listen(serverSocket, 10);

    std::cout << "Server started on port " << PORT << std::endl;

    while (true)
    {
        sockaddr_in clientAddr{};
        socklen_t len = sizeof(clientAddr);

        int clientSocket = accept(serverSocket, (sockaddr *)&clientAddr, &len);

        char ip[INET_ADDRSTRLEN];
        inet_ntop(AF_INET, &clientAddr.sin_addr, ip, sizeof(ip));

        log(std::string("New connection from IP: ") + ip);

        std::thread(handleClient, clientSocket).detach();
    }
}
