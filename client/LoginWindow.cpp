#include "LoginWindow.h"
#include "ChatWindow.h"
#include <QVBoxLayout>
#include <QLineEdit>
#include <QPushButton>

LoginWindow::LoginWindow() {
    auto layout = new QVBoxLayout(this);

    usernameInput = new QLineEdit();
    connectButton = new QPushButton("Connect");

    layout->addWidget(usernameInput);
    layout->addWidget(connectButton);

    socket = new QTcpSocket(this);

    connect(connectButton, &QPushButton::clicked,
            this, &LoginWindow::connectToServer);
}

void LoginWindow::connectToServer() {
    socket->connectToHost("127.0.0.1", 54000);

    if (socket->waitForConnected()) {
        QString username = usernameInput->text();
        socket->write(("REGISTER:" + username).toStdString().c_str());

        auto chat = new ChatWindow(socket, username);
        chat->show();
        this->close();
    }
}