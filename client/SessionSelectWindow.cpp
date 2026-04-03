#include "SessionSelectWindow.h"
#include <QVBoxLayout>
#include <QPushButton>
#include <QLineEdit>
#include <QLabel>

SessionSelectWindow::SessionSelectWindow(QString user)
    : username(user)
{
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
    layout->addWidget(portEdit);
    layout->addWidget(joinBtn);

    connect(hostBtn,&QPushButton::clicked,this,&SessionSelectWindow::hostClicked);
    connect(joinBtn,&QPushButton::clicked,this,&SessionSelectWindow::joinClicked);
}

void SessionSelectWindow::hostClicked()
{
    emit hostChat(chatName->text(),portEdit->text().toInt());
}

void SessionSelectWindow::joinClicked()
{
    emit joinChat(ipEdit->text(),portEdit->text().toInt());
}