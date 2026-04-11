#pragma once
#include <QWidget>
#include <QTcpSocket>
#include <QCamera>
#include <QMediaCaptureSession>
#include <QVideoWidget>
#include <QVideoSink>
#include <QTimer>

class QTextEdit;
class QLineEdit;
class QPushButton;
class QComboBox;
class QLabel;        // <-- brakująca deklaracja

class ChatWindow : public QWidget {
    Q_OBJECT

public:
    ChatWindow(QTcpSocket* socket, QString username);

private:
    QTcpSocket* socket;
    QString username;

    QTextEdit* chatBox;
    QLineEdit* input;
    QPushButton* sendBtn;
    QComboBox* userList;

    QPushButton* leaveBtn;

    QCamera* camera;
    QMediaCaptureSession captureSession;
    QVideoWidget* videoWidget;

    QVideoSink* videoSink;
    QTimer* frameTimer;

    QLabel* remoteVideoFrame;

private slots:
    void sendMessage();
    void readData();
    void leaveChat();
    void startCamera();
    void processFrame(const QVideoFrame &frame);
};