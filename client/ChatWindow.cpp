#include "ChatWindow.h"
#include <QVBoxLayout>
#include <QTextEdit>
#include <QLineEdit>
#include <QPushButton>
#include <QComboBox>

ChatWindow::ChatWindow(QTcpSocket* sock, QString user)
    : socket(sock), username(user)
{
    auto layout = new QVBoxLayout(this);

    userList = new QComboBox();
    chatBox = new QTextEdit();
    input = new QLineEdit();
    sendBtn = new QPushButton("Send");

    chatBox->setReadOnly(true);

    layout->addWidget(userList);
    layout->addWidget(chatBox);
    layout->addWidget(input);
    layout->addWidget(sendBtn);

    connect(sendBtn, &QPushButton::clicked,
            this, &ChatWindow::sendMessage);

    connect(socket, &QTcpSocket::readyRead,
            this, &ChatWindow::readData);
}

void ChatWindow::sendMessage() {
    QString target = userList->currentText();
    QString text = input->text();

    QString msg = "MSG:" + target + ":" + text;
    socket->write(msg.toStdString().c_str());

    chatBox->append("Me: " + text);
    input->clear();
}

void ChatWindow::readData() {
    QByteArray data = socket->readAll();
    QString msg = QString(data);

    if (msg.startsWith("USERS:")) {
        userList->clear();
        auto users = msg.mid(6).split(",");
        userList->addItems(users);
    }
    else if (msg.startsWith("FROM:")) {
        auto parts = msg.split(":");
        chatBox->append(parts[1] + ": " + parts[2]);
    }
}
