#pragma once
#include <QWidget>
#include <QTcpSocket>

class QLineEdit;
class QPushButton;

class LoginWindow : public QWidget {
    Q_OBJECT

public:
    LoginWindow();

private:
    QLineEdit *usernameInput;
    QPushButton *startButton;
    QTcpSocket *socket;

private slots:
    void connectToServer();
};