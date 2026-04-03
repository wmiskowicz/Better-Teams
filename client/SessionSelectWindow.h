#pragma once
#include <QWidget>

class QPushButton;
class QLineEdit;

class SessionSelectWindow : public QWidget {
    Q_OBJECT

public:
    SessionSelectWindow(QString username);

signals:
    void hostChat(QString name, int port);
    void joinChat(QString ip, int port);

private:
    QString username;

    QLineEdit* chatName;
    QLineEdit* portEdit;
    QLineEdit* ipEdit;

    QPushButton* hostBtn;
    QPushButton* joinBtn;

private slots:
    void hostClicked();
    void joinClicked();
};
