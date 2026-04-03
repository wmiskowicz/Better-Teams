#include "ChatWindow.h"
#include <QVBoxLayout>
#include <QTextEdit>
#include <QLineEdit>
#include <QPushButton>
#include <QComboBox>
#include <QLabel>
#include <QFileDialog>
#include <QPixmap>

ChatWindow::ChatWindow(QTcpSocket* sock, QString user)
    : socket(sock), username(user)
{
    auto layout = new QVBoxLayout(this);

    userList = new QComboBox();
    chatBox = new QTextEdit();
    input = new QLineEdit();

    sendBtn = new QPushButton("Send");
    leaveBtn = new QPushButton("Leave Chat");
    chooseImageBtn = new QPushButton("Choose Image");

    videoFrame = new QLabel();
    videoFrame->setMinimumSize(320,240);
    videoFrame->setStyleSheet("background:black;");
    videoFrame->setAlignment(Qt::AlignCenter);

    chatBox->setReadOnly(true);

    layout->addWidget(userList);
    layout->addWidget(videoFrame);   // pole obrazu
    layout->addWidget(chatBox);
    layout->addWidget(input);
    layout->addWidget(sendBtn);
    layout->addWidget(chooseImageBtn);
    layout->addWidget(leaveBtn);

    connect(sendBtn, &QPushButton::clicked,
            this, &ChatWindow::sendMessage);

    connect(leaveBtn, &QPushButton::clicked,
            this, &ChatWindow::leaveChat);

    connect(chooseImageBtn, &QPushButton::clicked,
            this, &ChatWindow::chooseImage);

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
    else if (msg.startsWith("IMG:"))
    {
    QByteArray imgData =
        QByteArray::fromBase64(msg.mid(4).toUtf8());

    QPixmap pix;
    pix.loadFromData(imgData);

    videoFrame->setPixmap(
        pix.scaled(videoFrame->size(),
        Qt::KeepAspectRatio)
    );
    }
}

void ChatWindow::leaveChat()
{
    socket->write("LEAVE");
    socket->disconnectFromHost();
    close();
}

void ChatWindow::chooseImage()
{
    QString file = QFileDialog::getOpenFileName(
        this,
        "Choose Image",
        "",
        "Images (*.png *.jpg *.bmp)"
    );

    if(file.isEmpty())
        return;

    QPixmap img(file);

    videoFrame->setPixmap(
        img.scaled(videoFrame->size(),
        Qt::KeepAspectRatio)
    );
}
