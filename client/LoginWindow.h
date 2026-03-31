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
    QPushButton *connectButton;
    QTcpSocket *socket;

private slots:
    void connectToServer();
};