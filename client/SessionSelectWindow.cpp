#include "SessionSelectWindow.h"
#include "ChatWindow.h"
#include <QVBoxLayout>
#include <QPushButton>
#include <QLineEdit>
#include <QLabel>
#include <QTcpSocket>

SessionSelectWindow::SessionSelectWindow(QString user)
    : username(user)
{
    socket = new QTcpSocket(this);
    socket->connectToHost("127.0.0.1", 54000);

    if(!socket->waitForConnected(3000))
    {
        qDebug() << "Server connection failed";
    }

    auto layout = new QVBoxLayout(this);

    chatName = new QLineEdit();
    chatName->setPlaceholderText("Chat name");

    portEdit = new QLineEdit();
    portEdit->setPlaceholderText("Port");

    ipEdit = new QLineEdit();
    ipEdit->setPlaceholderText("Host IP");

    hostBtn = new QPushButton("Host Chat");
    joinBtn = new QPushButton("Join Chat");

    layout->addWidget(new QLabel("Host new chat"));
    layout->addWidget(chatName);
    layout->addWidget(portEdit);
    layout->addWidget(hostBtn);

    layout->addWidget(new QLabel("Join chat"));
    layout->addWidget(ipEdit);
    layout->addWidget(joinBtn);

    connect(hostBtn,&QPushButton::clicked,this,&SessionSelectWindow::hostClicked);
    connect(joinBtn,&QPushButton::clicked,this,&SessionSelectWindow::joinClicked);
}

void SessionSelectWindow::hostClicked()
{
    QString name = chatName->text();

    QString msg = "CREATE_ROOM:" + name + ":" + username;

    socket->write(msg.toUtf8());

    auto chat = new ChatWindow(socket, username);
    chat->show();

    this->close();
}

void SessionSelectWindow::joinClicked()
{
    QString room = chatName->text();

    QString msg = "JOIN_ROOM:" + room + ":" + username;

    socket->write(msg.toUtf8());

    auto chat = new ChatWindow(socket, username);
    chat->show();

    this->close();
}
