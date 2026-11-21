// SPDX-License-Identifier: MIT
// Original Steins;OS application chrome around unmodified QTermWidget 6.
#include <QApplication>
#include <QAction>
#include <QClipboard>
#include <QCloseEvent>
#include <QColor>
#include <QCommandLineParser>
#include <QDBusConnection>
#include <QDBusMessage>
#include <QDBusPendingCallWatcher>
#include <QDBusPendingReply>
#include <QDBusServiceWatcher>
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QFontDatabase>
#include <QHBoxLayout>
#include <QJsonDocument>
#include <QJsonArray>
#include <QJsonObject>
#include <QLabel>
#include <QListWidget>
#include <QMainWindow>
#include <QMenu>
#include <QMenuBar>
#include <QMessageBox>
#include <QProcess>
#include <QProcessEnvironment>
#include <QPointer>
#include <QPushButton>
#include <QResizeEvent>
#include <QSaveFile>
#include <QShortcut>
#include <QSignalBlocker>
#include <QStandardPaths>
#include <QStatusBar>
#include <QTabBar>
#include <QTabWidget>
#include <QTimer>
#include <QToolButton>
#include <QVBoxLayout>
#include <QWidget>
#include <QCryptographicHash>
#include <functional>
#include <qtermwidget6/qtermwidget.h>

static constexpr char BUS[] = "org.steinsos.Worldline1";
static constexpr char PATH[] = "/org/steinsos/Worldline";

struct Session {
    QTermWidget *terminal;
    QString title;
    QString directory;
    bool running = true;
};

class TerminalWindow final : public QMainWindow {
    Q_OBJECT
public:
    explicit TerminalWindow(const QString &directory, const QStringList &command) {
        setObjectName("SteinsTerminal");
        setWindowTitle("Steins;OS Terminal");
        setWindowIcon(QIcon::fromTheme("utilities-terminal"));
        resize(1100, 690);
        setMinimumSize(560, 360);
        auto *central = new QWidget;
        central->setObjectName("canvas");
        auto *outer = new QVBoxLayout(central);
        outer->setContentsMargins(0, 0, 0, 0);
        outer->setSpacing(0);
        auto *header = new QWidget;
        header->setObjectName("instrumentHeader");
        auto *top = new QHBoxLayout(header);
        top->setContentsMargins(15, 9, 15, 9);
        auto *name = new QLabel("TERMINAL");
        name->setObjectName("identity");
        top->addWidget(name);
        top->addStretch();
        worldline = new QPushButton("WORLDLINE / —.——————");
        worldline->setObjectName("worldline");
        worldline->setAccessibleName("Current worldline; open Worldlines");
        worldline->setToolTip("Open Worldlines. This terminal follows the shared session service.");
        connect(worldline, &QPushButton::clicked, this, [] {
            QProcess::startDetached("steins-navigator-v4", {});
        });
        top->addWidget(worldline);
        outer->addWidget(header);
        auto *body = new QHBoxLayout;
        body->setContentsMargins(0, 0, 0, 0);
        body->setSpacing(0);
        railContainer = new QWidget;
        railContainer->setObjectName("sessionRail");
        auto *left = new QVBoxLayout(railContainer);
        left->setContentsMargins(8, 10, 8, 10);
        railHeading = new QLabel("SESSIONS");
        railHeading->setObjectName("muted");
        left->addWidget(railHeading);
        rail = new QListWidget;
        rail->setObjectName("sessionList");
        rail->setAccessibleName("Terminal sessions");
        rail->setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOff);
        rail->setWordWrap(false);
        left->addWidget(rail, 1);
        addButton = new QPushButton("+  New session");
        addButton->setObjectName("newSessionButton");
        addButton->setAccessibleName("New terminal session");
        addButton->setToolTip("New session (Ctrl+Shift+T)");
        connect(addButton, &QPushButton::clicked, this, [this] { addSession(defaultDirectory, {}); });
        left->addWidget(addButton);
        body->addWidget(railContainer);
        tabs = new QTabWidget;
        tabs->setObjectName("sessionTabs");
        tabs->setDocumentMode(true);
        // Original close controls below retain upstream tabs and accessibility,
        // without depending on a desktop style's contrasting close-box asset.
        tabs->setTabsClosable(false);
        tabs->setMovable(true);
        tabs->setAccessibleName("Terminal session tabs");
        body->addWidget(tabs, 1);
        outer->addLayout(body, 1);
        setCentralWidget(central);
        status = new QLabel("Terminal ready");
        statusBar()->addWidget(status, 1);
        connectionStatus = new QLabel("Connecting to worldline service…");
        statusBar()->addPermanentWidget(connectionStatus);
        connect(rail, &QListWidget::currentRowChanged, this, [this](int row) {
            if (row >= 0 && row < tabs->count()) tabs->setCurrentIndex(row);
        });
        connect(tabs, &QTabWidget::currentChanged, this, [this](int row) {
            rail->setCurrentRow(row);
            if (auto *term = currentTerminal()) term->setFocus();
            updateStatus();
        });
        connect(tabs, &QTabWidget::tabCloseRequested, this, &TerminalWindow::closeSession);
        connect(tabs->tabBar(), &QTabBar::tabMoved, this, [this] { rebuildRail(); });
        menus();
        defaultDirectory = directory;
        loadDesignTokens();
        applyAppearance();
        addSession(directory, command);
        auto bus = QDBusConnection::sessionBus();
        bus.connect(BUS, PATH, BUS, "StateChanged", this, SLOT(stateChanged(QString)));
        auto *watcher = new QDBusServiceWatcher(BUS, bus, QDBusServiceWatcher::WatchForOwnerChange, this);
        connect(watcher, &QDBusServiceWatcher::serviceOwnerChanged, this,
                [this](const QString &, const QString &, const QString &) { requestState(); });
        requestState();
    }

    QTermWidget *currentTerminal() const {
        return qobject_cast<QTermWidget *>(tabs->currentWidget());
    }

protected:
    void resizeEvent(QResizeEvent *event) override {
        QMainWindow::resizeEvent(event);
        compact = width() < 900;
        if (railContainer) {
            railContainer->setFixedWidth(railVisible ? (compact ? 58 : 176) : 0);
            railContainer->setVisible(railVisible);
            railHeading->setVisible(!compact);
            addButton->setText(compact ? "+" : "+  New session");
            rebuildRail();
        }
    }
    void closeEvent(QCloseEvent *event) override {
        if (windowCloseConfirmation || confirmationDepth > 0) {
            event->ignore();
            return;
        }
        QList<QPointer<QTermWidget>> confirmed;
        for (auto it = sessions.cbegin(); it != sessions.cend(); ++it)
            if (it.value().running) confirmed.append(it.key());
        if (!confirmed.isEmpty()) {
            windowCloseConfirmation = true;
            ++confirmationDepth;
            const auto answer = QMessageBox::warning(this, "Close terminal sessions?",
                QString("%1 shell session(s) are still running. Closing this window terminates their processes and may lose unsaved work.").arg(confirmed.size()),
                QMessageBox::Cancel | QMessageBox::Close, QMessageBox::Cancel);
            --confirmationDepth;
            windowCloseConfirmation = false;
            if (answer != QMessageBox::Close && tabs->count() > 0) {
                event->ignore();
                return;
            }
            // Nested dialog dispatch may create/finish sessions. Approval only
            // covers the identities present when the warning was displayed.
            for (auto it = sessions.cbegin(); it != sessions.cend(); ++it) {
                if (it.value().running && !confirmed.contains(QPointer<QTermWidget>(it.key()))) {
                    status->setText("Sessions changed during confirmation. Close again to review them.");
                    event->ignore();
                    return;
                }
            }
        }
        event->accept();
    }

private slots:
    void stateChanged(const QString &encoded) {
        // A signal supersedes any older in-flight GetState response.
        ++stateGeneration;
        consumeState(encoded);
    }

private:
#ifdef STEINS_TERMINAL_TEST
    friend class TerminalContracts;
#endif
    QTabWidget *tabs = nullptr;
    QListWidget *rail = nullptr;
    QWidget *railContainer = nullptr;
    QLabel *railHeading = nullptr;
    QPushButton *addButton = nullptr;
    QPushButton *worldline = nullptr;
    QLabel *status = nullptr;
    QLabel *connectionStatus = nullptr;
    QHash<QTermWidget *, Session> sessions;
    QString defaultDirectory;
    QString accent = "#d9ad72", background = "#11181e", foreground = "#e6e8e7";
    QJsonObject design;
    QString alternate = "#151f28", selection = "#334657", muted = "#a9b6bf";
    QString worldId, worldName;
    QStringList terminalPalette;
    int fontSize = 11;
    quint64 stateGeneration = 0;
    bool compact = false, railVisible = true;
    bool windowCloseConfirmation = false;
    int confirmationDepth = 0;

    QAction *action(QMenu *menu, const QString &label, const QKeySequence &key,
                    const std::function<void()> &fn) {
        QAction *entry = menu->addAction(label);
        entry->setShortcut(key);
        connect(entry, &QAction::triggered, this, fn);
        return entry;
    }
    void menus() {
        auto *session = menuBar()->addMenu("&Session");
        action(session, "&New session", QKeySequence("Ctrl+Shift+T"), [this] { addSession(defaultDirectory, {}); });
        action(session, "&Close session…", QKeySequence("Ctrl+Shift+W"), [this] { closeSession(tabs->currentIndex()); });
        session->addSeparator();
        action(session, "Open &Konsole fallback", {}, [this] { QProcess::startDetached("konsole", {"--workdir", defaultDirectory}); });
        action(session, "&Quit…", QKeySequence("Ctrl+Shift+Q"), [this] { close(); });
        auto *edit = menuBar()->addMenu("&Edit");
        action(edit, "&Copy", QKeySequence("Ctrl+Shift+C"), [this] { if (auto *t = currentTerminal()) t->copyClipboard(); });
        action(edit, "&Paste…", QKeySequence("Ctrl+Shift+V"), [this] { paste(); });
        action(edit, "&Find in scrollback", QKeySequence("Ctrl+Shift+F"), [this] { if (auto *t = currentTerminal()) t->toggleShowSearchBar(); });
        auto *view = menuBar()->addMenu("&View");
        action(view, "Larger text", QKeySequence("Ctrl++"), [this] { changeFont(1); });
        action(view, "Smaller text", QKeySequence("Ctrl+-"), [this] { changeFont(-1); });
        action(view, "Reset text size", QKeySequence("Ctrl+0"), [this] { fontSize = 11; changeFont(0); });
        auto *railAction = action(view, "Session rail", QKeySequence("Ctrl+Shift+B"), [this] {
            railVisible = !railVisible;
            railContainer->setFixedWidth(railVisible ? (compact ? 58 : 176) : 0);
            railContainer->setVisible(railVisible);
        });
        railAction->setCheckable(true);
        railAction->setChecked(true);
        action(view, "Next session", QKeySequence("Ctrl+PgDown"), [this] {
            if (tabs->count()) tabs->setCurrentIndex((tabs->currentIndex() + 1) % tabs->count());
        });
        action(view, "Previous session", QKeySequence("Ctrl+PgUp"), [this] {
            if (tabs->count()) tabs->setCurrentIndex((tabs->currentIndex() + tabs->count() - 1) % tabs->count());
        });
        for (int i = 0; i < 9; ++i) {
            auto *shortcut = new QShortcut(QKeySequence(QString("Alt+%1").arg(i + 1)), this);
            connect(shortcut, &QShortcut::activated, this, [this, i] { if (i < tabs->count()) tabs->setCurrentIndex(i); });
        }
        auto *help = menuBar()->addMenu("&Help");
        action(help, "About Steins;OS Terminal", {}, [this] {
            QMessageBox::about(this, "Steins;OS Terminal — experimental",
                "Original Steins;OS interface around QTermWidget 6, maintained by LXQt.\n\n"
                "Terminal emulation and PTY handling are provided by QTermWidget, not reimplemented here. "
                "Konsole remains available as a fallback.\n\n"
                "Steins;OS frontend source: MIT. QTermWidget includes GPL-2+ and LGPL-2+ code; packaged executable is distributed under GPL-2-or-later.\n"
                "No scene animation, shell injection, remote connection or telemetry.");
        });
    }
    void paste() {
        auto *term = currentTerminal();
        if (!term) return;
        // QTermWidget confirms multiline paste for every engine paste path,
        // including keyboard/menu/middle-click; bracketed paste stays enabled.
        term->pasteClipboard();
    }
    void changeFont(int delta) {
        fontSize = qBound(7, fontSize + delta, 28);
        QFont font = QFontDatabase::systemFont(QFontDatabase::FixedFont);
        font.setPointSize(fontSize);
        for (auto *term : sessions.keys()) term->setTerminalFont(font);
        updateStatus();
    }
    void addSession(const QString &directory, const QStringList &command) {
        auto *term = new QTermWidget(0, tabs);
        term->setAccessibleName("Terminal output and shell input");
        term->setHistorySize(10000);
        term->setScrollBarPosition(QTermWidget::ScrollBarRight);
        term->setTerminalOpacity(1.0);
        term->setBlinkingCursor(false);
        term->setMargin(14);
        term->setConfirmMultilinePaste(true);
        term->setWorkingDirectory(directory);
        QString program = qEnvironmentVariable("SHELL", "/bin/bash");
        if (!QFileInfo(program).isExecutable()) program = "/bin/bash";
        term->setShellProgram(command.isEmpty() ? program : command.first());
        term->setArgs(command.isEmpty() ? QStringList{"-l"} : command.mid(1));
        auto environment = QProcessEnvironment::systemEnvironment();
        environment.insert("TERM", "xterm-256color");
        environment.insert("COLORTERM", "truecolor");
        term->setEnvironment(environment.toStringList());
        const QString label = command.isEmpty() ? QFileInfo(program).fileName() : QFileInfo(command.first()).fileName();
        sessions.insert(term, Session{term, label, directory, true});
        tabs->addTab(term, label);
        tabs->setCurrentWidget(term);
        auto *closeButton = new QToolButton(tabs->tabBar());
        closeButton->setObjectName("sessionClose");
        closeButton->setText(QString::fromUtf8("×"));
        closeButton->setToolButtonStyle(Qt::ToolButtonTextOnly);
        closeButton->setAccessibleName("Close terminal session");
        closeButton->setToolTip("Close session (Ctrl+Shift+W)");
        closeButton->setFixedSize(24, 24);
        closeButton->setFocusPolicy(Qt::StrongFocus);
        QPointer<QTermWidget> target(term);
        connect(closeButton, &QToolButton::clicked, this, [this, target] {
            const int index = target ? tabs->indexOf(target.data()) : -1;
            if (index >= 0) closeSession(index);
        });
        tabs->tabBar()->setTabButton(tabs->indexOf(term), QTabBar::RightSide, closeButton);
        connect(term, &QTermWidget::finished, this, [this, term] {
            if (!sessions.contains(term)) return;
            sessions[term].running = false;
            const int index = tabs->indexOf(term);
            if (index >= 0) removeSession(index);
        });
        connect(term, &QTermWidget::titleChanged, this, [this, term] {
            if (!sessions.contains(term)) return;
            QString title = term->title().simplified().left(80);
            if (!title.isEmpty()) sessions[term].title = title;
            const int index = tabs->indexOf(term);
            if (index >= 0) tabs->setTabText(index, sessions[term].title.left(28));
            rebuildRail();
        });
        applyTerminalAppearance(term);
        changeFont(0);
        rebuildRail();
        term->startShellProgram();
        term->setFocus();
    }
    void closeSession(int index) {
        if (index < 0) return;
        QPointer<QTermWidget> target = qobject_cast<QTermWidget *>(tabs->widget(index));
        if (!target || !sessions.contains(target.data())) return;
        if (sessions.value(target.data()).running) {
            ++confirmationDepth;
            const auto answer = QMessageBox::warning(this, "Close shell session?",
                "This shell is still running. Closing its session terminates its processes and may lose unsaved work.",
                QMessageBox::Cancel | QMessageBox::Close, QMessageBox::Cancel);
            --confirmationDepth;
            if (answer != QMessageBox::Close) {
                if (tabs->count() == 0 && confirmationDepth == 0) close();
                return;
            }
        }
        // Session completion can remove/reorder tabs inside the modal event
        // loop. Never reuse the old index to close a different shell.
        const int currentIndex = target ? tabs->indexOf(target.data()) : -1;
        if (currentIndex >= 0 && sessions.contains(target.data())) removeSession(currentIndex);
        else if (tabs->count() == 0 && confirmationDepth == 0) close();
    }
    void removeSession(int index) {
        auto *term = qobject_cast<QTermWidget *>(tabs->widget(index));
        sessions.remove(term);
        tabs->removeTab(index);
        if (term) term->deleteLater();
        rebuildRail();
        if (tabs->count() == 0 && confirmationDepth == 0) close();
    }
    void rebuildRail() {
        if (!rail || !tabs) return;
        const QSignalBlocker block(rail);
        rail->clear();
        for (int i = 0; i < tabs->count(); ++i) {
            auto *term = qobject_cast<QTermWidget *>(tabs->widget(i));
            const auto session = sessions.value(term);
            QString caption = compact ? QString::number(i + 1) : session.title.left(24) + "\n" + QDir::toNativeSeparators(session.directory);
            auto *item = new QListWidgetItem(caption, rail);
            item->setToolTip(session.title + "\nStarted in " + session.directory);
            item->setData(Qt::AccessibleTextRole, "Session " + QString::number(i + 1) + ": " + session.title);
            item->setSizeHint(QSize(40, compact ? 44 : 64));
        }
        rail->setCurrentRow(tabs->currentIndex());
    }
    void updateStatus() {
        auto *term = currentTerminal();
        status->setText(QString("%1 pt · %2 sessions").arg(fontSize).arg(tabs->count()));
        if (term) setWindowTitle(sessions.value(term).title + " — Steins;OS Terminal");
    }
    void requestState() {
        const auto generation = ++stateGeneration;
        auto message = QDBusMessage::createMethodCall(BUS, PATH, BUS, "GetState");
        auto *watcher = new QDBusPendingCallWatcher(QDBusConnection::sessionBus().asyncCall(message, 3000), this);
        connect(watcher, &QDBusPendingCallWatcher::finished, this, [this, generation](QDBusPendingCallWatcher *call) {
            QDBusPendingReply<QString> reply = *call;
            call->deleteLater();
            if (generation != stateGeneration) return;
            if (reply.isError()) {
                connectionStatus->setText("Worldline service unavailable · terminal remains usable");
                return;
            }
            consumeState(reply.value());
        });
    }
    static QString safeColor(const QJsonObject &p, const char *key, const QString &fallback) {
        QColor c(p.value(key).toString());
        return c.isValid() ? c.name(QColor::HexRgb) : fallback;
    }
    void consumeState(const QString &encoded) {
        QJsonParseError error;
        const auto document = QJsonDocument::fromJson(encoded.toUtf8(), &error);
        if (error.error != QJsonParseError::NoError || !document.isObject()) return;
        const auto object = document.object();
        const auto palette = object.value("palette").toObject();
        if (palette.isEmpty()) return;
        background = safeColor(palette, "bg", background);
        alternate = safeColor(palette, "bg_alt", alternate);
        foreground = safeColor(palette, "fg", foreground);
        selection = safeColor(palette, "selection", selection);
        muted = safeColor(palette, "muted", muted);
        const auto ansi = object.value("terminal_palette").toArray();
        terminalPalette.clear();
        if (ansi.size() == 16) {
            QStringList parsed;
            for (const auto &entry : ansi) {
                QColor color(entry.toString());
                if (!color.isValid()) { parsed.clear(); break; }
                parsed.append(color.name(QColor::HexRgb));
            }
            if (parsed.size() == 16) terminalPalette = parsed;
        }
        worldId = object.value("id").toString().left(48);
        accent = safeColor(design.value("worldlines").toObject().value(worldId).toObject(),
                           "accent", uiColor("accent"));
        worldName = object.value("name").toString().left(64);
        const QString number = object.value("divergence").toString().left(16);
        worldline->setText(number + "  /  " + worldName);
        worldline->setAccessibleName("Current worldline " + worldName + ", divergence " + number + ". Open Worldlines.");
        const bool applied = !object.contains("applied") || object.value("applied").toBool();
        connectionStatus->setText(applied ? "Shared worldline · connected" : "Worldline appearance needs recovery");
        applyAppearance();
    }
    void loadDesignTokens() {
        // Read only the packaged shared contract; user shell/profile files are untouched.
        QFile file("/usr/share/steins-v4/tokens.json");
        if (file.open(QIODevice::ReadOnly) && file.size() <= 256 * 1024) {
            QJsonParseError error;
            const auto document = QJsonDocument::fromJson(file.readAll(), &error);
            if (error.error == QJsonParseError::NoError && document.isObject()) design = document.object();
        }
        // Offline/standalone fallback matches V4 identity, including all six subdued accents.
        if (design.value("worldlines").toObject().isEmpty()) {
            QJsonObject worlds;
            const QStringList ids{"alpha", "steins-gate", "hinamizawa", "hitogashima", "lugunica", "mitakihara"};
            const QStringList colors{"#c39b91", "#d9ad72", "#b4bf99", "#92bebc", "#b5a9cf", "#c5a8bb"};
            for (int i=0; i<ids.size(); ++i) worlds.insert(ids[i], QJsonObject{{"accent", colors[i]}});
            design.insert("worldlines", worlds);
        }
        accent = uiColor("accent");
    }
    QString uiColor(const char *key) const {
        static const QJsonObject fallback{{"canvas", "#11181e"}, {"panel", "#151d23"},
            {"raised", "#1d272f"}, {"input", "#0e151b"}, {"border", "#3c4b55"},
            {"text", "#e6e8e7"}, {"muted", "#abb6bc"}, {"selection", "#303b43"}, {"accent", "#d9ad72"}};
        return safeColor(design.value("color").toObject(), key, fallback.value(key).toString());
    }
    void applyAppearance() {
        // Chrome remains the same neutral OS identity in every world. Only the
        // instrument digits and narrow selection/focus strokes follow divergence.
        // Engine content/ANSI colours remain separate and never restart the PTY.
        QPalette p = palette();
        p.setColor(QPalette::Window, QColor(uiColor("panel")));
        p.setColor(QPalette::WindowText, QColor(uiColor("text")));
        p.setColor(QPalette::Base, QColor(uiColor("input")));
        p.setColor(QPalette::Text, QColor(uiColor("text")));
        p.setColor(QPalette::Button, QColor(uiColor("raised")));
        p.setColor(QPalette::ButtonText, QColor(uiColor("text")));
        p.setColor(QPalette::Highlight, QColor(uiColor("selection")));
        p.setColor(QPalette::HighlightedText, QColor(uiColor("text")));
        setPalette(p);
        QString sheet = QString(
            "QMainWindow,QWidget#canvas{background:%1;color:%2;}"
            "QWidget#instrumentHeader{background:%5;border-bottom:1px solid %7;}"
            "QLabel#identity{font-weight:600;letter-spacing:2px;} QLabel#muted{color:%3;font-size:11px;}"
            "QLabel{color:%2;} QPushButton{background:%8;color:%2;border:1px solid %7;border-radius:@radius@px;padding:8px;}"
            "QPushButton:hover{background:%6;} QPushButton:focus{border:2px solid %4;}"
            "QPushButton#worldline{font-family:monospace;color:%4;background:%9;padding:7px 12px;}"
            "QWidget#sessionRail{background:%5;border-right:1px solid %7;}"
            "QListWidget{background:transparent;border:0;color:%3;outline:none;}"
            "QListWidget::item{padding:6px;border-left:2px solid transparent;border-radius:4px;}"
            "QListWidget::item:selected{background:%6;color:%2;border-left:2px solid %4;}"
            "QListWidget::item:focus{border:1px solid %4;}"
            "QTabWidget::pane{border:0;} QTabBar{background:%5;}"
            "QTabBar::tab{background:%5;color:%3;min-width:90px;padding:9px 12px;border-bottom:2px solid transparent;}"
            "QTabBar::tab:selected{background:%8;color:%2;border-bottom:2px solid %4;}"
            "QTabBar::tab:hover{background:%6;}"
            "QToolButton#sessionClose{color:%3;background:transparent;border:1px solid transparent;border-radius:4px;padding:0;font-size:18px;}"
            "QToolButton#sessionClose:hover{color:%2;background:%6;}"
            "QToolButton#sessionClose:focus{border:1px solid %4;} QToolButton#sessionClose:pressed{background:%6;}"
            "QScrollBar:vertical{background:%1;width:16px;margin:2px;border:1px solid transparent;}"
            "QScrollBar:focus{border:1px solid %4;}"
            "QScrollBar::handle:vertical{background:%7;min-height:32px;border:2px solid %1;border-radius:5px;}"
            "QScrollBar::handle:vertical:hover,QScrollBar::handle:vertical:pressed{background:%3;}"
            "QScrollBar::handle:vertical:disabled{background:%6;}"
            "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0px;border:0;}"
            "QScrollBar::up-arrow:vertical,QScrollBar::down-arrow:vertical{width:0px;height:0px;}"
            "QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical{background:transparent;}"
            "QMenuBar,QMenu,QStatusBar{background:%5;color:%2;}"
            "QMenuBar::item:selected,QMenu::item:selected{background:%6;} QStatusBar{border-top:1px solid %7;}"
            "QStatusBar QLabel{color:%3;padding:3px 8px;font-size:11px;}"
            "QLineEdit{background:%9;color:%2;border:1px solid %7;border-radius:4px;padding:5px;selection-background-color:%6;selection-color:%2;}"
            "QLineEdit:focus{border:2px solid %4;}"
            "QMessageBox{background:%5;color:%2;} QToolTip{background:%8;color:%2;border:1px solid %7;}"
        ).arg(uiColor("canvas"), uiColor("text"), uiColor("muted"), accent, uiColor("panel"),
              uiColor("selection"), uiColor("border"), uiColor("raised"), uiColor("input"));
        const int radius = qBound(2, design.value("radius").toObject().value("control").toInt(6), 12);
        sheet.replace("@radius@", QString::number(radius));
        setStyleSheet(sheet);
        for (auto *term : sessions.keys()) applyTerminalAppearance(term);
    }
    void applyTerminalAppearance(QTermWidget *term) {
        const QString cache = QStandardPaths::writableLocation(QStandardPaths::CacheLocation);
        QDir().mkpath(cache);
        // Only application-private cache is written. Never edit Konsole/user profiles.
        auto rgb = [](const QString &value) {
            QColor c(value);
            return QString("%1,%2,%3").arg(c.red()).arg(c.green()).arg(c.blue());
        };
        QString colors = "[General]\nDescription=Steins current worldline\nOpacity=1\n"
            "[Background]\nColor=" + rgb(background) + "\n[BackgroundIntense]\nColor=" + rgb(background) +
            "\n[Foreground]\nColor=" + rgb(foreground) + "\n[ForegroundIntense]\nColor=" + rgb(foreground) + "\n";
        const QStringList ansi = terminalPalette.size() == 16 ? terminalPalette : QStringList{
            "#202830","#ee8e85","#a9cd9a","#efc476","#8dbbe3","#c6a5d4","#8ecada","#e8e5df",
            "#687f8f","#ffb0a5","#c1dfa8","#ffdda1","#b5d5f2","#e2c0ed","#b0e3e7","#ffffff"};
        for (int i=0;i<ansi.size();++i) colors += QString("[Color%1%2]\nColor=%3\n").arg(i%8).arg(i>=8 ? "Intense" : "").arg(rgb(ansi[i]));
        // QTermWidget caches loaded schemes by path: content-addressed names
        // ensure a real palette refresh without resetting PTY/application state.
        const QString digest = QString::fromLatin1(QCryptographicHash::hash(colors.toUtf8(), QCryptographicHash::Sha256).toHex().left(16));
        const QString filename = cache + "/worldline-" + digest + ".colorscheme";
        QSaveFile file(filename);
        if (file.open(QIODevice::WriteOnly)) {
            file.write(colors.toUtf8());
            if (file.commit()) term->setColorScheme(filename);
        }
        QPalette palette = term->palette();
        palette.setColor(QPalette::Highlight, QColor(selection));
        palette.setColor(QPalette::HighlightedText, QColor("#ffffff"));
        term->setPalette(palette);
    }
};

#ifndef STEINS_TERMINAL_TEST
int main(int argc, char **argv) {
    QApplication app(argc, argv);
    QApplication::setApplicationName("steins-terminal-v3");
    QApplication::setApplicationVersion("0.3.0~v4.1");
    QApplication::setOrganizationName("SteinsOS");
    QGuiApplication::setDesktopFileName("steins-terminal-v3");
    QCommandLineParser parser;
    parser.setApplicationDescription("Experimental Steins;OS terminal around maintained QTermWidget 6.");
    parser.addHelpOption();
    parser.addVersionOption();
    parser.addOption({{"d", "working-directory", "workdir"}, "Initial working directory", "directory", QDir::homePath()});
    parser.addOption({{"e", "execute"}, "Execute the following command and arguments"});
    parser.setOptionsAfterPositionalArgumentsMode(QCommandLineParser::ParseAsPositionalArguments);
    parser.addPositionalArgument("command", "Optional command and arguments after --", "[command [arguments…]]");
    parser.process(app);
    const QString directory = QFileInfo(parser.value("working-directory")).absoluteFilePath();
    if (!QFileInfo(directory).isDir()) {
        qCritical("Initial working directory is not a directory");
        return 2;
    }
    const QStringList command = parser.positionalArguments();
    if (parser.isSet("execute") && command.isEmpty()) {
        qCritical("--execute requires a command");
        return 2;
    }
    if (!command.isEmpty() && QStandardPaths::findExecutable(command.first()).isEmpty()) {
        qCritical("Requested command is not executable");
        return 2;
    }
    TerminalWindow window(directory, command);
    window.show();
    return app.exec();
}
#else
#include <QtTest>
#include <QTemporaryDir>

class TerminalContracts : public QObject {
    Q_OBJECT
private slots:
    void initTestCase() { QApplication::setQuitOnLastWindowClosed(false); }
    void realPtyUnicodeResizeAndDynamicPalette() {
        QTemporaryDir fixture;
        QVERIFY(fixture.isValid());
        TerminalWindow window(fixture.path(), {"/bin/bash", "--noprofile", "--norc", "-i"});
        window.show();
        auto *term = window.currentTerminal();
        QVERIFY(term);
        QTRY_VERIFY_WITH_TIMEOUT(term->getShellPID() > 0, 5000);
        const int pid = term->getShellPID();
        const QString output = fixture.path() + "/pty.txt";
        term->sendText(QString("test -t 0 && test -t 1 && printf 'TTY=yes\\nPID=%%s\\nUNICODE=λ→Δ日本語\\n' \"$$\" > '%1'; stty size >> '%1'\n").arg(output).replace("%%s", "%s"));
        QTRY_VERIFY_WITH_TIMEOUT(QFileInfo(output).size() > 40, 5000);
        QFile first(output); QVERIFY(first.open(QIODevice::ReadOnly));
        const auto initial = QString::fromUtf8(first.readAll());
        QVERIFY(initial.contains("TTY=yes"));
        QVERIFY(initial.contains("UNICODE=λ→Δ日本語"));
        QVERIFY(initial.contains(QString("PID=%1").arg(pid)));
        const int initialColumns = term->screenColumnsCount();
        window.resize(1350, 850);
        QTRY_VERIFY(term->screenColumnsCount() > initialColumns);
        QCOMPARE(term->getShellPID(), pid);
        QJsonObject state{{"id", "hitogashima"}, {"name", "Hitogashima"}, {"divergence", "3.072100"}, {"applied", true},
            {"palette", QJsonObject{{"bg", "#0f1f2a"}, {"bg_alt", "#0b1821"}, {"fg", "#e3eef3"}, {"accent", "#38a8e0"}, {"selection", "#1f78a6"}, {"muted", "#7fa3b8"}}}};
        const QString encoded = QString::fromUtf8(QJsonDocument(state).toJson(QJsonDocument::Compact));
        QVERIFY(QMetaObject::invokeMethod(&window, "stateChanged", Qt::DirectConnection, Q_ARG(QString, encoded)));
        QCOMPARE(term->getShellPID(), pid);
        auto *badge = window.findChild<QPushButton *>("worldline");
        QVERIFY(badge && badge->text().contains("3.072100"));
        QVERIFY(window.styleSheet().contains("#92bebc"));
        QVERIFY(window.styleSheet().contains("background:#151d23"));
        QVERIFY(window.styleSheet().contains("background:#303b43"));
        QVERIFY(!window.styleSheet().contains("#38a8e0"));
        QTest::qWait(50);
        const QImage rendered = term->grab().toImage();
        QCOMPARE(rendered.pixelColor(rendered.width()/2, rendered.height()-35), QColor("#0f1f2a"));
        const QString resized = fixture.path() + "/resized.txt";
        term->sendText(QString("printf 'PID=%%s\\n' \"$$\" > '%1'; stty size >> '%1'\n").arg(resized).replace("%%s", "%s"));
        QTRY_VERIFY_WITH_TIMEOUT(QFileInfo(resized).size() > 10, 5000);
        QFile second(resized); QVERIFY(second.open(QIODevice::ReadOnly));
        QVERIFY(QString::fromUtf8(second.readAll()).contains(QString("PID=%1").arg(pid)));
    }
    void linkedSessionModelAndCloseCancellation() {
        QTemporaryDir fixture;
        TerminalWindow window(fixture.path(), {"/bin/bash", "--noprofile", "--norc", "-i"});
        window.show();
        window.activateWindow();
        QTest::qWait(100);
        auto *tabs = window.findChild<QTabWidget *>("sessionTabs");
        auto *rail = window.findChild<QListWidget *>("sessionList");
        auto *first = window.currentTerminal();
        QVERIFY(tabs && rail && first);
        QTest::keyClick(&window, Qt::Key_T, Qt::ControlModifier | Qt::ShiftModifier);
        QTRY_COMPARE(tabs->count(), 2);
        QCOMPARE(rail->count(), 2);
        tabs->tabBar()->moveTab(0, 1);
        rail->setCurrentRow(1);
        QCOMPARE(window.currentTerminal(), first);
        window.resize(700, 600);
        QTRY_COMPARE(window.findChild<QWidget *>("sessionRail")->width(), 58);
        QCOMPARE(rail->item(1)->text(), QString("2"));
        bool cancelWasDefault = false;
        QTimer::singleShot(100, &window, [&cancelWasDefault] {
            for (auto *widget : QApplication::topLevelWidgets()) {
                if (auto *box = qobject_cast<QMessageBox *>(widget)) {
                    cancelWasDefault = box->standardButton(box->defaultButton()) == QMessageBox::Cancel;
                    box->reject();
                }
            }
        });
        QTest::keyClick(&window, Qt::Key_W, Qt::ControlModifier | Qt::ShiftModifier);
        QVERIFY(cancelWasDefault);
        QCOMPARE(tabs->count(), 2);
        first->sendText("exit\n");
        QTRY_COMPARE_WITH_TIMEOUT(tabs->count(), 1, 5000);
        QCOMPARE(rail->count(), 1);
    }
    void exitingTargetDuringConfirmationDoesNotCloseOtherShell() {
        QTemporaryDir fixture;
        TerminalWindow window(fixture.path(), {"/bin/bash", "--noprofile", "--norc", "-i"});
        window.show(); window.activateWindow(); QTest::qWait(100);
        auto *tabs = window.tabs;
        QPointer<QTermWidget> target = window.currentTerminal();
        window.addSession(fixture.path(), {"/bin/bash", "--noprofile", "--norc", "-i"});
        QPointer<QTermWidget> survivor = window.currentTerminal();
        const int survivorPid = survivor->getShellPID();
        tabs->setCurrentWidget(target.data());
        bool targetExitedInDialog = false;
        QTimer poll;
        connect(&poll, &QTimer::timeout, &window, [&] {
            if (!target || tabs->indexOf(target.data()) < 0) {
                targetExitedInDialog = true;
                poll.stop();
                for (auto *widget : QApplication::topLevelWidgets()) {
                    if (auto *box = qobject_cast<QMessageBox *>(widget))
                        if (box->windowTitle() == "Close shell session?") box->button(QMessageBox::Close)->click();
                }
            }
        });
        QTimer::singleShot(50, &window, [&] { if (target) target->sendText("exit\n"); });
        QTimer::singleShot(5000, &window, [&] {
            for (auto *widget : QApplication::topLevelWidgets())
                if (auto *box = qobject_cast<QMessageBox *>(widget)) box->reject();
        });
        poll.start(20);
        auto *closeButton = qobject_cast<QToolButton *>(tabs->tabBar()->tabButton(0, QTabBar::RightSide));
        QVERIFY(closeButton);
        QCOMPARE(closeButton->accessibleName(), QString("Close terminal session"));
        closeButton->click();
        QVERIFY(targetExitedInDialog);
        QCOMPARE(tabs->count(), 1);
        QVERIFY(survivor);
        QCOMPARE(window.currentTerminal(), survivor.data());
        QCOMPARE(survivor->getShellPID(), survivorPid);
        const QString canary = fixture.path() + "/survivor-alive";
        survivor->sendText(QString("printf alive > '%1'\n").arg(canary));
        QTRY_VERIFY_WITH_TIMEOUT(QFileInfo(canary).size() == 5, 5000);
    }
    void windowConfirmationCannotApproveANewShell() {
        QTemporaryDir fixture;
        TerminalWindow window(fixture.path(), {"/bin/bash", "--noprofile", "--norc", "-i"});
        window.show(); window.activateWindow(); QTest::qWait(100);
        QPointer<QTermWidget> original = window.currentTerminal();
        QPointer<QTermWidget> newcomer;
        QTimer::singleShot(50, &window, [&] {
            window.addSession(fixture.path(), {"/bin/bash", "--noprofile", "--norc", "-i"});
            newcomer = window.currentTerminal();
            original->sendText("exit\n");
        });
        QTimer::singleShot(200, &window, [&] {
            for (auto *widget : QApplication::topLevelWidgets())
                if (auto *box = qobject_cast<QMessageBox *>(widget))
                    if (box->windowTitle() == "Close terminal sessions?") box->button(QMessageBox::Close)->click();
        });
        QVERIFY(!window.close());
        QVERIFY(window.isVisible());
        QVERIFY(newcomer);
        QCOMPARE(window.currentTerminal(), newcomer.data());
        QTRY_VERIFY(!original || window.tabs->indexOf(original.data()) < 0);
        QCOMPARE(window.tabs->count(), 1);
        const QString canary = fixture.path() + "/newcomer-alive";
        newcomer->sendText(QString("printf alive > '%1'\n").arg(canary));
        QTRY_VERIFY_WITH_TIMEOUT(QFileInfo(canary).size() == 5, 5000);
    }
    void optionalAnsiPaletteDoesNotRetainPreviousWorld() {
        QTemporaryDir fixture;
        TerminalWindow window(fixture.path(), {"/bin/bash", "--noprofile", "--norc", "-i"});
        QJsonArray custom;
        for (int i = 0; i < 16; ++i) custom.append("#123456");
        QJsonObject state{{"palette", QJsonObject{{"bg", "#101820"}}}, {"terminal_palette", custom}};
        window.consumeState(QString::fromUtf8(QJsonDocument(state).toJson()));
        QCOMPARE(window.terminalPalette.size(), 16);
        state.remove("terminal_palette");
        window.consumeState(QString::fromUtf8(QJsonDocument(state).toJson()));
        QVERIFY(window.terminalPalette.isEmpty());
        state.insert("terminal_palette", custom);
        window.consumeState(QString::fromUtf8(QJsonDocument(state).toJson()));
        custom[3] = "invalid colour";
        state.insert("terminal_palette", custom);
        window.consumeState(QString::fromUtf8(QJsonDocument(state).toJson()));
        QVERIFY(window.terminalPalette.isEmpty());
    }
    void hiddenSessionRailIsRemovedFromFocusTraversal() {
        QTemporaryDir fixture;
        TerminalWindow window(fixture.path(), {"/bin/bash", "--noprofile", "--norc", "-i"});
        window.show(); window.activateWindow(); QTest::qWait(100);
        QTest::keyClick(&window, Qt::Key_B, Qt::ControlModifier | Qt::ShiftModifier);
        QVERIFY(!window.railContainer->isVisible());
        QVERIFY(!window.addButton->isVisible());
        window.resize(700, 600);
        QTest::qWait(20);
        QVERIFY(!window.railContainer->isVisible());
        QTest::keyClick(&window, Qt::Key_B, Qt::ControlModifier | Qt::ShiftModifier);
        QVERIFY(window.railContainer->isVisible());
        QCOMPARE(window.railContainer->width(), 58);
    }
};
QTEST_MAIN(TerminalContracts)
#endif

#include "main.moc"
