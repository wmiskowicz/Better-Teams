#pragma once
#include <QWidget>
#include <QTcpSocket>

class QTextEdit;
class QLineEdit;
class QPushButton;
class QComboBox;

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

private slots:
    void sendMessage();
    void readData();
};
