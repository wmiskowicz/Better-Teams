#include "ChatWindow.h"
#include "SessionSelectWindow.h"

#include <QVBoxLayout>
#include <QTextEdit>
#include <QLineEdit>
#include <QPushButton>
#include <QComboBox>

#include <QLabel>
#include <QPixmap>
#include <QBuffer>
#include <QImage>

#include <QCamera>
#include <QVideoWidget>
#include <QVideoSink>
#include <QVideoFrame>

ChatWindow::ChatWindow(QTcpSocket* sock, QString user)
    : socket(sock), username(user)
{
    auto layout = new QVBoxLayout(this);

    userList = new QComboBox();

    remoteVideoFrame = new QLabel();
    remoteVideoFrame->setMinimumSize(320,240);
    remoteVideoFrame->setStyleSheet("background:black;");
    remoteVideoFrame->setAlignment(Qt::AlignCenter);

    videoWidget = new QVideoWidget();
    videoWidget->setMinimumSize(320,240);

    chatBox = new QTextEdit();
    chatBox->setReadOnly(true);

    input = new QLineEdit();

    sendBtn = new QPushButton("Send");
    leaveBtn = new QPushButton("Leave Chat");

    layout->addWidget(userList);

    layout->addWidget(new QLabel("Remote camera"));
    layout->addWidget(remoteVideoFrame);

    layout->addWidget(new QLabel("My camera"));
    layout->addWidget(videoWidget);

    layout->addWidget(chatBox);
    layout->addWidget(input);
    layout->addWidget(sendBtn);
    layout->addWidget(leaveBtn);

    connect(sendBtn,&QPushButton::clicked,
            this,&ChatWindow::sendMessage);

    connect(leaveBtn,&QPushButton::clicked,
            this,&ChatWindow::leaveChat);

    connect(socket,&QTcpSocket::readyRead,
            this,&ChatWindow::readData);

    startCamera();
}

void ChatWindow::sendMessage() {

    QString target = userList->currentText();
    QString text = input->text();

    QString msg = "MSG:" + target + ":" + text;

    socket->write(msg.toUtf8());

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

        if(parts.size() >= 3)
            chatBox->append(parts[1] + ": " + parts[2]);
    }
    else if (msg.startsWith("IMG:")) {
        QByteArray imgData =
            QByteArray::fromBase64(msg.mid(4).toUtf8());

        QPixmap pix;
        pix.loadFromData(imgData);

        remoteVideoFrame->setPixmap(
            pix.scaled(
                remoteVideoFrame->size(),
                Qt::KeepAspectRatio
            )
        );
    }
}

void ChatWindow::leaveChat()
{
    socket->write("LEAVE");

    SessionSelectWindow* session =
        new SessionSelectWindow(username);

    session->show();

    this->close();
}

void ChatWindow::startCamera()
{
    camera = new QCamera(this);

    videoSink = new QVideoSink(this);

    captureSession.setCamera(camera);

    // lokalny podgląd
    captureSession.setVideoOutput(videoWidget);

    connect(videoSink,
            &QVideoSink::videoFrameChanged,
            this,
            &ChatWindow::processFrame);

    camera->start();
}

void ChatWindow::processFrame(const QVideoFrame &frame)
{
    QVideoFrame copy(frame);

    if(!copy.isValid())
        return;

    QImage img = copy.toImage();

    if(img.isNull())
        return;

    img = img.scaled(320,240,Qt::KeepAspectRatio);

    QByteArray bytes;
    QBuffer buffer(&bytes);

    buffer.open(QIODevice::WriteOnly);
    img.save(&buffer,"JPG",50);

    QByteArray base64 = bytes.toBase64();

    QString msg = "IMG:" + QString(base64);

    socket->write(msg.toUtf8());
}
