// SPDX-License-Identifier: MIT
// Opt-in only. Reorder our own meter; preserve all other applets and task launchers.
// Plasma 6.3 Widget.index is a stub; coordinate insertion + saved AppletOrder are used.
(function () {
    var options = __STEINS_OPTIONS__;
    var plugin = "org.steinsos.worldline.v4";
    var oldPlugin = "org.steinsos.worldline";
    var launcherTypes = ["org.kde.plasma.kickoff", "org.kde.plasma.kicker", "org.kde.plasma.kickerdash"];
    function launcherArray(value) {
        // Qt's KConfig bridge returns a V4Sequence, not a JavaScript Array.
        // Read its indexed QString values without trusting an unbounded length.
        if (value === null || typeof value !== "object")
            throw new Error("Task launchers are not a readable Qt sequence; no migration was applied.");
        var length=Number(value.length);
        if (!isFinite(length) || Math.floor(length)!==length || length<0 || length>4096)
            throw new Error("Task launcher sequence length is invalid; no migration was applied.");
        var result=[];
        for (var i=0;i<length;++i) {
            if (typeof value[i]!=="string")
                throw new Error("Task launcher sequence contains a non-string value; no migration was applied.");
            result.push(value[i]);
        }
        return result;
    }
    var panel = null, launcher = null;
    panels().forEach(function (p) {
        if (panel !== null || p.location !== "bottom" || (options.panelId !== null && String(p.id) !== options.panelId)) return;
        var launchers = p.widgets().filter(function(w) { return launcherTypes.indexOf(w.type) !== -1; });
        if (launchers.length) {panel=p; launcher=launchers[0];}
    });
    if (panel === null) throw new Error("No matching existing bottom panel with a standard launcher. Nothing changed.");
    var items=panel.widgets();
    var found=items.filter(function(w) {return w.type===plugin;});
    var old=items.filter(function(w) {return w.type===oldPlugin;});
    if (found.length>1) throw new Error("Multiple V4 meters exist. Choose one in panel Edit Mode before applying this preset.");
    var previousGroup=panel.currentConfigGroup;
    panel.currentConfigGroup=["General"];
    var raw=String(panel.readConfig("AppletOrder", ""));
    panel.currentConfigGroup=previousGroup;
    if (!raw) throw new Error("No saved AppletOrder. Refusing to guess the other widgets' order.");
    var geometry=launcher.geometry;
    if (!found.length && (!geometry || geometry.width<=0 || geometry.height<=0))
        throw new Error("Launcher geometry is not ready. Retry after the panel becomes visible.");
    // Validate native sequences before adding/removing widgets or changing geometry.
    var launcherLists={};
    if (options.replaceV3) items.forEach(function(w) {
        if (w.type!=="org.kde.plasma.icontasks" && w.type!=="org.kde.plasma.taskmanager")return;
        var group=w.currentConfigGroup;
        try {
            w.currentConfigGroup=["General"];
            launcherLists[String(w.id)]=launcherArray(w.readConfig("launchers",[]));
        } finally {w.currentConfigGroup=group;}
    });
    var instrument=found.length ? found[0] : panel.addWidget(plugin,geometry.x+geometry.width/2+1,geometry.y+geometry.height/2+1);
    if (!instrument || instrument.type!==plugin) throw new Error("V4 instrument could not be added; old meter remains.");
    var removed=[];
    if (options.replaceV3) old.forEach(function(w) {removed.push(String(w.id));w.remove();});
    items=panel.widgets();
    var valid={};items.forEach(function(w) {valid[String(w.id)]=true;});
    var order=[];
    raw.split(";").forEach(function(id) {if(valid[id] && order.indexOf(id)===-1)order.push(id);});
    items.forEach(function(w) {var id=String(w.id);if(order.indexOf(id)===-1)order.push(id);});
    var id=String(instrument.id);order.splice(order.indexOf(id),1);
    order.splice(order.indexOf(String(launcher.id))+1,0,id);
    panel.currentConfigGroup=["General"];
    panel.writeConfig("AppletOrder",order.join(";"));
    panel.currentConfigGroup=previousGroup;
    panel.height=46;
    panel.floating=false;
    panel.opacity="translucent";
    // Native launchers, task manager, tray and clock retain their normal keyboard/menu behavior.
    var originalGroup=launcher.currentConfigGroup;
    launcher.currentConfigGroup=["General"];
    launcher.writeConfig("icon","steins-launcher");
    launcher.currentConfigGroup=originalGroup;
    var tasks=[];
    items.forEach(function(w) {
        if (w.type!=="org.kde.plasma.icontasks" && w.type!=="org.kde.plasma.taskmanager")return;
        var group=w.currentConfigGroup;w.currentConfigGroup=["General"];
        w.writeConfig("maxStripes",1);w.writeConfig("forceStripes",false);
        if (w.type==="org.kde.plasma.icontasks")w.writeConfig("iconSpacing",1);
        if (options.replaceV3) {
            var launchers=launcherLists[String(w.id)];
            // Normalize only our exact desktop IDs. Inherited/third-party pins,
            // including deliberate duplicates, keep their original value/order.
            var aliases={
                "steins-navigator":"steins-navigator-v4.desktop",
                "steins-worldlines":"steins-navigator-v4.desktop",
                "steins-worldline":"steins-navigator-v4.desktop",
                "steins-navigator.desktop":"steins-navigator-v4.desktop",
                "steins-worldlines.desktop":"steins-navigator-v4.desktop",
                "steins-worldline.desktop":"steins-navigator-v4.desktop",
                "steins-navigator-v4.desktop":"steins-navigator-v4.desktop",
                "steins-terminal.desktop":"steins-terminal-v3.desktop",
                "steins-terminal-v3.desktop":"steins-terminal-v3.desktop"
            };
            var seen={},mapped=[];
            launchers.forEach(function(s) {
                var desktop=s.indexOf("applications:")===0 ? s.slice(13) : s;
                var target=Object.prototype.hasOwnProperty.call(aliases,desktop) ? aliases[desktop] : null;
                if (!target) {mapped.push(s);return;}
                if (!seen[target]) {mapped.push("applications:"+target);seen[target]=true;}
            });
            if (JSON.stringify(mapped)!==JSON.stringify(launchers))w.writeConfig("launchers",mapped);
        }
        w.currentConfigGroup=group;tasks.push(w.id);
    });
    return JSON.stringify({action:"v4-panel-preset",panel:panel.id,instrument:instrument.id,
        previous_order:raw,saved_order:order.join(";"),removed_v3_meters:removed,
        task_managers:tasks,panel_height:46,floating:false,restart_required:true,
        note:"Other applets and launchers preserved. Sign out/in or restart only the guest shell to confirm saved order and theme."});
}());
