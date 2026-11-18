import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: root
    visible: true
    title: "Worldlines — Steins;OS"
    width: 880; height: 650
    minimumWidth: 650; minimumHeight: 540
    readonly property var ink: designTokens.color
    readonly property var typography: designTokens.typography
    readonly property var worlds: designTokens.worldlines
    function worldAccent(id) { return worlds[id] ? worlds[id].accent : ink.accent }
    readonly property color accent: worldAccent(worldline.state.id)
    color: ink.canvas
    palette.window: ink.canvas
    palette.windowText: ink.text
    palette.base: ink.input
    palette.text: ink.text
    palette.button: ink.raised
    palette.buttonText: ink.text
    palette.highlight: ink.selection
    palette.highlightedText: ink.text
    font.family: typography.uiFamily
    font.pixelSize: typography.sizes.body
    Shortcut { sequence: "Escape"; onActivated: root.close() }
    ScrollView {
        anchors.fill: parent
        contentWidth: availableWidth
        ColumnLayout {
            width: parent.width
            spacing: 24
            Item { Layout.preferredHeight: 4 }
            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 28; Layout.rightMargin: 28
                ColumnLayout {
                    spacing: 6
                    Label { text: "WORLDLINES"; color: root.ink.muted; font.pixelSize: root.typography.sizes.caption; font.letterSpacing: 2 }
                    Label { text: "Choose your worldline"; color: root.ink.text; font.pixelSize: root.typography.sizes.title; font.weight: Font.DemiBold }
                    Label { text: "One divergence. A different atmosphere."; color: root.ink.muted }
                }
                Item { Layout.fillWidth: true }
                ColumnLayout {
                    Label { text: worldline.state.divergence; color: root.accent; font.family: root.typography.terminalFamily; font.pixelSize: 25 }
                    Label { text: worldline.state.name; color: root.ink.muted; Layout.alignment: Qt.AlignRight }
                }
            }
            GridLayout {
                columns: root.width < 760 ? 2 : 3
                uniformCellWidths: true
                rowSpacing: 12; columnSpacing: 12
                Layout.fillWidth: true
                Layout.leftMargin: 28; Layout.rightMargin: 28
                Repeater {
                    model: worldline.packs
                    delegate: Button {
                        id: card
                        objectName: "worldline-card-" + modelData.id
                        required property var modelData
                        readonly property bool selected: worldline.state.id === modelData.id
                        readonly property color worldAccent: root.worldAccent(modelData.id)
                        Layout.fillWidth: true; Layout.preferredHeight: 134
                        enabled: !worldline.busy
                        Accessible.name: modelData.name + (selected ? ", current worldline" : ", switch worldline")
                        onClicked: worldline.select(modelData.divergence)
                        background: Rectangle {
                            radius: designTokens.radius.window
                            color: card.down || card.selected ? root.ink.selection : (card.hovered ? root.ink.raisedHover : root.ink.panel)
                            border.width: card.activeFocus ? 2 : 1
                            border.color: card.activeFocus ? card.worldAccent : root.ink.border
                            Rectangle { x: 16; y: 18; width: 24; height: 2; radius: 1; color: card.worldAccent }
                            Rectangle {
                                visible: card.selected
                                anchors.left: parent.left; anchors.leftMargin: 16
                                anchors.bottom: parent.bottom; anchors.bottomMargin: 12
                                width: 24; height: 2; radius: 1; color: card.worldAccent
                            }
                        }
                        contentItem: Column {
                            leftPadding: 16; topPadding: 34; spacing: 7
                            Label { text: card.modelData.name; color: root.ink.text; font.pixelSize: 17; font.weight: Font.DemiBold }
                            Label { text: card.modelData.divergence; color: card.worldAccent; font.family: root.typography.terminalFamily }
                            Label { text: card.selected ? "Current worldline" : "Switch worldline"; color: root.ink.muted; font.pixelSize: 12 }
                        }
                    }
                }
            }
            Rectangle { Layout.fillWidth: true; Layout.leftMargin: 28; Layout.rightMargin: 28; height: 1; color: root.ink.border }
            RowLayout {
                Layout.leftMargin: 28; Layout.rightMargin: 28; Layout.fillWidth: true
                ColumnLayout {
                    spacing: 6
                    Label { text: "Divergence meter"; color: root.ink.text; font.weight: Font.DemiBold }
                    Label { text: "Keep the tube display open on the desktop"; color: root.ink.muted; font.pixelSize: 12 }
                }
                Item { Layout.fillWidth: true }
                Switch {
                    id: meter
                    objectName: "meter-switch"
                    Accessible.name: "Show divergence meter"
                    checked: worldline.state.preferences.meter || false
                    enabled: !worldline.busy
                    onToggled: worldline.meter(checked)
                    indicator: Rectangle {
                        implicitWidth: 46; implicitHeight: 26
                        x: meter.leftPadding; y: (meter.height - height) / 2
                        radius: 13; color: meter.checked ? root.ink.selection : root.ink.input
                        border.color: meter.activeFocus || meter.checked ? root.accent : root.ink.border
                        border.width: meter.activeFocus ? 2 : 1
                        Rectangle {
                            x: meter.checked ? parent.width - width - 4 : 4; y: 4
                            width: 18; height: 18; radius: 9
                            color: meter.checked ? root.accent : root.ink.muted
                        }
                    }
                }
            }
            RowLayout {
                Layout.leftMargin: 28; Layout.rightMargin: 28; Layout.fillWidth: true
                Label { text: "Appearance recovery"; color: root.ink.muted }
                Item { Layout.fillWidth: true }
                BusyIndicator { running: worldline.busy; visible: running; Layout.preferredWidth: 24; Layout.preferredHeight: 24 }
                Button {
                    id: retry
                    objectName: "appearance-retry"
                    text: "Reapply current"; enabled: !worldline.busy; onClicked: worldline.retry()
                    leftPadding: 14; rightPadding: 14; topPadding: 9; bottomPadding: 9
                    background: Rectangle {
                        radius: designTokens.radius.control; color: retry.hovered || retry.down ? root.ink.selection : root.ink.raised
                        border.width: retry.activeFocus ? 2 : 1
                        border.color: retry.activeFocus ? root.accent : root.ink.border
                    }
                }
            }
            Label {
                Layout.leftMargin: 28; Layout.rightMargin: 28; Layout.fillWidth: true
                text: worldline.error; visible: text.length > 0; color: root.ink.error; wrapMode: Text.Wrap
                Accessible.role: Accessible.AlertMessage
            }
            Item { Layout.preferredHeight: 12 }
        }
    }
}
