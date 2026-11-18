// SPDX-License-Identifier: MIT
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.kirigami as Kirigami
import org.kde.plasma.workspace.dbus as DBus

PlasmoidItem {
    id: root
    width: design.meterWidth
    height: design.panelHeight
    DesignTokens { id: design }
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    preferredRepresentation: compactRepresentation
    property var state: ({})
    property var packs: []
    property var pending: null
    property var packRequest: null
    property bool pendingMutation: false
    property int generation: 0
    property double observedAt: 0
    property double clockNow: Date.now()
    readonly property bool vertical: Plasmoid.formFactor === PlasmaCore.Types.Vertical
    readonly property bool stale: connected && clockNow - observedAt > 8000
    property bool connected: false
    property string errorText: "Connecting to Worldline service…"
    readonly property bool busy: pending !== null
    readonly property bool applied: connected && state.applied === true
    readonly property bool partial: connected && state.applied === false
    readonly property string number: connected && /^\d\.\d{6}$/.test(state.divergence || "") ? state.divergence : "—.——————"
    readonly property string worldName: connected ? (state.name || "Unknown worldline") : "Service unavailable"
    readonly property color accent: connected && state.palette && /^#[0-9a-fA-F]{6}$/.test(state.palette.accent || "") ? state.palette.accent : design.brandAccent
    readonly property string statusText: busy && pendingMutation ? "Applying…" : !connected ? "Disconnected" : stale ? "State refresh delayed" : partial ? "Appearance incomplete" : applied ? "Current worldline" : "Appearance pending"
    toolTipMainText: worldName + " · " + number
    toolTipSubText: statusText + (errorText ? "\n" + errorText : "") + "\nOpen for worldlines and motion controls."

    function loseConnection(message) {
        connected = false;
        state = ({}); // Never leave an unavailable service displaying apparently current digits.
        errorText = message;
    }
    function accept(encoded) {
        const obj = JSON.parse(encoded);
        if (obj.interface !== 1 || typeof obj.divergence !== "string" || !/^\d\.\d{6}$/.test(obj.divergence))
            throw new Error("Invalid Worldline service response");
        state = obj;
        observedAt = Date.now();
        clockNow = observedAt;
        connected = true;
        errorText = (obj.errors || []).map(e => e.step + ": " + e.message).join("; ");
    }
    function call(method, args) {
        if (pending !== null) return;
        const serial = generation;
        const reply = DBus.SessionBus.asyncCall({service: "org.steinsos.Worldline1", path: "/org/steinsos/Worldline", iface: "org.steinsos.Worldline1", member: method, arguments: args || []});
        pendingMutation = ["SetDivergence", "SetPreference", "ApplyCurrent"].includes(method);
        pending = reply;
        let completed = false;
        const complete = function() {
            if (completed) return;
            completed = true;
            if (serial !== generation) return;
            pending = null;
            if (reply.isError) {
                if (method === "GetState") loseConnection(reply.error.message);
                else errorText = reply.error.message;
                return;
            }
            try { accept(reply.value); }
            catch (e) { loseConnection(String(e)); }
        };
        if (reply.isFinished) complete(); else reply.finished.connect(complete);
    }
    function loadPacks() {
        if (packRequest !== null) return;
        const serial = generation;
        const reply = DBus.SessionBus.asyncCall({service: "org.steinsos.Worldline1", path: "/org/steinsos/Worldline", iface: "org.steinsos.Worldline1", member: "ListWorldlines"});
        packRequest = reply;
        let completed = false;
        const complete = function() {
            if (completed) return;
            completed = true;
            if (serial !== generation) return;
            packRequest = null;
            if (reply.isError) return;
            try {
                const result = JSON.parse(reply.value);
                if (!Array.isArray(result)) throw new Error("Invalid worldline list");
                packs = result.filter(p => typeof p.name === "string" && /^\d\.\d{6}$/.test(p.divergence || ""));
            } catch (e) { errorText = String(e); }
        };
        if (reply.isFinished) complete(); else reply.finished.connect(complete);
    }
    function refresh() { call("GetState", []); }
    function selectWorld(value) {
        if (/^\d\.\d{6}$/.test(value)) call("SetDivergence", [new DBus.string(value)]);
    }
    function setMeter(value) { call("SetPreference", [new DBus.string("meter"), new DBus.string(value ? "true" : "false")]); }
    function setMotion(value) {
        if (["off", "reduced", "full"].includes(value)) call("SetPreference", [new DBus.string("motion"), new DBus.string(JSON.stringify(value))]);
    }
    onExpandedChanged: if (expanded) { refresh(); loadPacks(); }
    Component.onCompleted: { refresh(); loadPacks(); }
    DBus.DBusServiceWatcher {
        watchedService: "org.steinsos.Worldline1"
        busType: DBus.BusType.Session
        onRegisteredChanged: {
            root.generation++;
            root.pending = null;
            root.packRequest = null;
            if (registered) { root.refresh(); root.loadPacks(); }
            else root.loseConnection("Worldline service disconnected. Reconnecting automatically.");
        }
    }
    Timer { interval: 2000; repeat: true; running: true; onTriggered: { root.clockNow = Date.now(); root.refresh(); } }

    compactRepresentation: Controls.AbstractButton {
        id: instrument
        Layout.minimumWidth: root.vertical ? 40 : design.meterMinimumWidth
        Layout.preferredWidth: root.vertical ? 46 : design.meterWidth
        Layout.maximumWidth: root.vertical ? 96 : design.meterWidth
        Layout.minimumHeight: root.vertical ? 66 : design.controlTarget
        Layout.preferredHeight: root.vertical ? 72 : design.panelHeight
        hoverEnabled: true
        focusPolicy: Qt.StrongFocus
        Accessible.name: "Worldline " + root.number + ", " + root.worldName
        Accessible.description: root.statusText + ". Open worldline controls."
        onClicked: root.expanded = !root.expanded
        background: Rectangle {
            anchors.centerIn: parent
            width: parent.width - 4
            height: root.vertical ? parent.height - 8 : Math.min(design.meterHeight, parent.height - 2)
            radius: design.controlRadius
            color: instrument.down ? design.selection : instrument.hovered ? design.raisedHover : design.input
            border.color: instrument.activeFocus ? design.brandAccent : design.border
            border.width: instrument.activeFocus ? design.focusWidth : design.borderWidth
            Rectangle {
                x: 7; y: 9; width: 2; height: Math.max(8, parent.height - 18); radius: 1
                color: !root.connected ? design.subtle : root.partial || root.stale ? design.warning : root.accent
            }
        }
        contentItem: Item {
            Column {
                anchors.centerIn: parent
                width: parent.width - 24
                spacing: 0
                Text {
                    width: parent.width
                    text: root.vertical ? root.number.slice(0, 5) + "\n" + root.number.slice(5) : root.number
                    horizontalAlignment: Text.AlignHCenter
                    font.family: design.monoFamily
                    font.pixelSize: root.vertical ? 11 : design.digitSize
                    font.weight: Font.Medium
                    font.letterSpacing: root.vertical ? 0 : 1.3
                    color: root.connected ? root.accent : design.subtle
                }
                Text {
                    width: parent.width
                    text: root.busy && root.pendingMutation ? "Applying…" : !root.connected ? "Disconnected" : root.stale ? "Refresh delayed" : root.partial ? "Appearance incomplete" : root.worldName
                    horizontalAlignment: Text.AlignHCenter
                    elide: Text.ElideRight
                    color: root.partial || root.stale ? design.warning : design.muted
                    font.family: design.uiFamily
                    font.pixelSize: 10
                }
            }
        }
    }

    fullRepresentation: ColumnLayout {
        Layout.minimumWidth: 330
        Layout.preferredWidth: 380
        Layout.maximumWidth: 480
        Layout.minimumHeight: 350
        spacing: 8
        Controls.Label { text: "WORLDLINE INSTRUMENT"; font.letterSpacing: 1.7; font.pixelSize: 11; color: design.muted; Layout.topMargin: 10; Layout.leftMargin: 12 }
        Controls.Label { text: root.number; color: root.accent; font.family: design.monoFamily; font.pixelSize: 29; Layout.leftMargin: 12 }
        Controls.Label { text: root.worldName + " · " + root.statusText; wrapMode: Text.WordWrap; Layout.fillWidth: true; Layout.leftMargin: 12; Layout.rightMargin: 12 }
        Controls.Label {
            visible: root.errorText !== ""
            text: root.errorText
            wrapMode: Text.WordWrap
            color: design.error
            Layout.fillWidth: true
            Layout.leftMargin: 12; Layout.rightMargin: 12
            font.pixelSize: 11
        }
        GridLayout {
            columns: 2
            Layout.fillWidth: true
            Layout.leftMargin: 10; Layout.rightMargin: 10
            Repeater {
                model: root.packs
                delegate: Controls.Button {
                    required property var modelData
                    Layout.fillWidth: true
                    text: modelData.name
                    checkable: true
                    checked: root.connected && root.state.id === modelData.id
                    enabled: root.connected && !root.busy
                    Accessible.description: "Switch to " + modelData.name + ", divergence " + modelData.divergence
                    onClicked: root.selectWorld(modelData.divergence)
                }
            }
        }
        Controls.CheckBox {
            text: "Expanded tube meter"
            checked: root.connected && root.state.preferences && root.state.preferences.meter === true
            enabled: root.connected && !root.busy
            Layout.leftMargin: 8
            onClicked: root.setMeter(checked)
        }
        RowLayout {
            Layout.leftMargin: 12; Layout.rightMargin: 12
            Controls.Label { text: "Motion" }
            Controls.ComboBox {
                id: motion
                model: ["Off", "Reduced", "Full"]
                currentIndex: root.state.preferences ? ["off", "reduced", "full"].indexOf(root.state.preferences.motion) : 1
                enabled: root.connected && !root.busy
                Accessible.name: "Worldline motion"
                onActivated: root.setMotion(["off", "reduced", "full"][currentIndex])
            }
            Item { Layout.fillWidth: true }
            Controls.Button { text: root.partial ? "Reapply" : "Refresh"; enabled: !root.busy; onClicked: root.partial ? root.call("ApplyCurrent", []) : root.refresh() }
        }
        Controls.Button {
            text: "Open Worldlines"
            Layout.fillWidth: true
            Layout.leftMargin: 10; Layout.rightMargin: 10; Layout.bottomMargin: 10
            enabled: root.connected && !root.busy
            onClicked: root.call("OpenNavigator", [])
        }
    }
}
