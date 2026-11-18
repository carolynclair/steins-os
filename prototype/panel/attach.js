// Explicit disposable-profile helper: add/move only our instrument, never delete widgets.
// Plasma 6.3 Widget.index is a stub. New widgets accept insertion coordinates;
// an existing widget's saved General/AppletOrder takes effect on shell restart.
(function () {
    var plugin = "org.steinsos.worldline";
    var launcherTypes = ["org.kde.plasma.kickoff", "org.kde.plasma.kicker", "org.kde.plasma.kickerdash"];
    var candidates = panels().filter(function (p) { return p.location === "bottom"; });
    var panel = null;
    var launcher = null;
    for (var p = 0; p < candidates.length && panel === null; ++p) {
        var launchers = candidates[p].widgets().filter(function (w) { return launcherTypes.indexOf(w.type) !== -1; });
        if (launchers.length > 0) { panel = candidates[p]; launcher = launchers[0]; }
    }
    if (panel === null) throw new Error("No existing bottom panel with a supported application launcher; use Plasma's widget browser.");
    var items = panel.widgets();
    var found = items.filter(function (w) { return w.type === plugin; });
    if (found.length > 1) throw new Error("Multiple Worldline Instruments exist; choose their positions in panel Edit Mode.");
    if (found.length === 0) {
        var geometry = launcher.geometry;
        if (!geometry || geometry.width <= 0 || geometry.height <= 0)
            throw new Error("Launcher geometry is not ready; retry after the panel is visible.");
        // Supported insertion workaround from KDE bug 523675, comment 4.
        var instrument = panel.addWidget(plugin, geometry.x + geometry.width / 2 + 1,
                                         geometry.y + geometry.height / 2 + 1);
        return JSON.stringify({action: "added-at-launcher", panel: panel.id, instrument: instrument.id,
                               launcher: launcher.id, restart_required: false,
                               note: "Verify live order; Plasma saves the insertion order after the script returns."});
    }
    var instrument = found[0];
    var previousGroup = panel.currentConfigGroup;
    var result;
    try {
        panel.currentConfigGroup = ["General"];
        var raw = String(panel.readConfig("AppletOrder", ""));
        if (!raw) throw new Error("The panel has no saved AppletOrder; refusing to guess the other widgets' visual order.");
        var valid = {};
        items.forEach(function (w) { valid[String(w.id)] = true; });
        var order = [];
        raw.split(";").forEach(function (id) {
            if (valid[id] && order.indexOf(id) === -1) order.push(id);
        });
        // Match Plasma 6.3 restore(): unsaved existing widgets append at the end.
        items.forEach(function (w) { var id = String(w.id); if (order.indexOf(id) === -1) order.push(id); });
        var id = String(instrument.id);
        order.splice(order.indexOf(id), 1);
        var launcherIndex = order.indexOf(String(launcher.id));
        if (launcherIndex === -1) throw new Error("Launcher missing from panel order; nothing changed.");
        order.splice(launcherIndex + 1, 0, id);
        var desired = order.join(";");
        var changed = raw !== desired;
        if (changed) panel.writeConfig("AppletOrder", desired);
        result = {action: changed ? "saved-order-for-shell-restart" : "order-already-configured",
                  panel: panel.id, instrument: instrument.id, launcher: launcher.id,
                  previous_order: raw, saved_order: desired, restart_required: changed,
                  note: "Plasma 6.3 reads AppletOrder when the panel loads; verify after a normal guest-only shell restart."};
    } finally {
        panel.currentConfigGroup = previousGroup;
    }
    return JSON.stringify(result);
}());
