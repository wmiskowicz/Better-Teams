#include "LoginWindow.h"
#include "ChatWindow.h"
#include "SessionSelectWindow.h"
#include <QVBoxLayout>
#include <QLineEdit>
#include <QPushButton>

LoginWindow::LoginWindow() {
    auto layout = new QVBoxLayout(this);

    usernameInput = new QLineEdit();
    startButton = new QPushButton("Start");

    layout->addWidget(usernameInput);
    layout->addWidget(startButton);

    socket = new QTcpSocket(this);

    connect(startButton, &QPushButton::clicked,
            this, &LoginWindow::OpenSessionSelectWindow);
}

void LoginWindow::OpenSessionSelectWindow()
{
    QString username = usernameInput->text();

    if(username.isEmpty())
        return;

    SessionSelectWindow* session = new SessionSelectWindow(username);
    session->show();

    this->hide();
}