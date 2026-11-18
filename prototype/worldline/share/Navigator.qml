import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: root
    visible: true
    title: "Worldlines"
    width: 880; height: 650
    minimumWidth: 650; minimumHeight: 540
    color: "#141a20"
    property color accent: worldline.state.palette.accent || "#e99a45"
    palette.window: "#141a20"
    palette.windowText: "#e9e6df"
    palette.base: "#1b242c"
    palette.text: "#e9e6df"
    palette.button: "#26323c"
    palette.buttonText: "#e9e6df"
    palette.highlight: "#805026"
    palette.highlightedText: "#ffffff"
    font.family: "Noto Sans"
    font.pixelSize: 14
    Shortcut { sequence: "Escape"; onActivated: root.close() }
    ScrollView {
        anchors.fill: parent
        contentWidth: availableWidth
        ColumnLayout {
            width: parent.width
            spacing: 20
            anchors.margins: 28
            Item { Layout.preferredHeight: 8 }
            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 28; Layout.rightMargin: 28
                ColumnLayout {
                    spacing: 4
                    Label { text: "WORLDLINES"; color: "#aebcc5"; font.pixelSize: 11; font.letterSpacing: 3 }
                    Label { text: "Choose your worldline"; color: "#e9e6df"; font.pixelSize: 28; font.weight: Font.DemiBold }
                    Label { text: "One divergence. A different atmosphere."; color: "#aebcc5" }
                }
                Item { Layout.fillWidth: true }
                ColumnLayout {
                    Label { text: worldline.state.divergence; color: root.accent; font.family: "DejaVu Sans Mono"; font.pixelSize: 28 }
                    Label { text: worldline.state.name; color: "#cbd4da"; Layout.alignment: Qt.AlignRight }
                }
            }
            GridLayout {
                columns: 3
                rowSpacing: 12; columnSpacing: 12
                Layout.fillWidth: true
                Layout.leftMargin: 28; Layout.rightMargin: 28
                Repeater {
                    model: worldline.packs
                    delegate: Button {
                        id: card
                        required property var modelData
                        property bool selected: worldline.state.id === modelData.id
                        Layout.fillWidth: true; Layout.preferredHeight: 134
                        enabled: !worldline.busy
                        Accessible.name: modelData.name + (selected ? ", selected" : "")
                        onClicked: worldline.select(modelData.divergence)
                        background: Rectangle {
                            radius: 10
                            color: card.selected ? "#25333c" : (card.hovered ? "#243039" : "#1c252d")
                            border.width: card.activeFocus || card.selected ? 2 : 1
                            border.color: card.activeFocus || card.selected ? modelData.palette.accent : "#35424c"
                            Rectangle { x: 16; y: 18; width: 24; height: 3; radius: 1; color: modelData.palette.accent }
                        }
                        contentItem: Column {
                            leftPadding: 16; topPadding: 34; spacing: 7
                            Label { text: card.modelData.name; color: "#e9e6df"; font.pixelSize: 17; font.weight: Font.DemiBold }
                            Label { text: card.modelData.divergence; color: card.modelData.palette.accent; font.family: "DejaVu Sans Mono" }
                            Label { text: card.selected ? "Current worldline" : "Switch worldline"; color: "#afbec8"; font.pixelSize: 12 }
                        }
                    }
                }
            }
            Rectangle { Layout.fillWidth: true; Layout.leftMargin: 28; Layout.rightMargin: 28; height: 1; color: "#34424a" }
            RowLayout {
                Layout.leftMargin: 28; Layout.rightMargin: 28; Layout.fillWidth: true
                ColumnLayout {
                    Label { text: "Divergence meter"; color: "#e9e6df"; font.weight: Font.DemiBold }
                    Label { text: "Keep the tube display open on the desktop"; color: "#afbec8"; font.pixelSize: 12 }
                }
                Item { Layout.fillWidth: true }
                Switch {
                    id: meter
                    Accessible.name: "Show divergence meter"
                    checked: worldline.state.preferences.meter || false
                    enabled: !worldline.busy
                    onToggled: worldline.meter(checked)
                    indicator: Rectangle {
                        implicitWidth: 46; implicitHeight: 26
                        x: meter.leftPadding; y: (meter.height - height) / 2
                        radius: 13; color: meter.checked ? "#805026" : "#303e48"
                        border.color: meter.activeFocus ? "#ffffff" : "#5b6b75"
                        border.width: meter.activeFocus ? 2 : 1
                        Rectangle {
                            x: meter.checked ? parent.width - width - 4 : 4; y: 4
                            width: 18; height: 18; radius: 9
                            color: meter.checked ? "#f2bb76" : "#c0cbd2"
                        }
                    }
                }
            }
            RowLayout {
                Layout.leftMargin: 28; Layout.rightMargin: 28; Layout.fillWidth: true
                Label { text: "Appearance recovery"; color: "#afbec8" }
                Item { Layout.fillWidth: true }
                BusyIndicator { running: worldline.busy; visible: running; Layout.preferredWidth: 24; Layout.preferredHeight: 24 }
                Button {
                    id: retry
                    text: "Reapply current"; enabled: !worldline.busy; onClicked: worldline.retry()
                    leftPadding: 14; rightPadding: 14; topPadding: 9; bottomPadding: 9
                    background: Rectangle {
                        radius: 6; color: retry.hovered ? "#334550" : "#26343e"
                        border.width: retry.activeFocus ? 2 : 1
                        border.color: retry.activeFocus ? root.accent : "#536570"
                    }
                }
            }
            Label {
                Layout.leftMargin: 28; Layout.rightMargin: 28; Layout.fillWidth: true
                text: worldline.error; visible: text.length > 0; color: "#ffb2a6"; wrapMode: Text.Wrap
                Accessible.role: Accessible.AlertMessage
            }
            Item { Layout.preferredHeight: 12 }
        }
    }
}
