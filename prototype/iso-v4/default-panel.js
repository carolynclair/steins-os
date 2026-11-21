// SPDX-License-Identifier: MIT
var panel = new Panel;
panel.location = "bottom";
panel.height = 46;
panel.floating = false;
panel.opacity = "translucent";

var launcher = panel.addWidget("org.kde.plasma.kickoff");
launcher.currentConfigGroup = ["General"];
launcher.writeConfig("icon", "steins-launcher");
panel.addWidget("org.steinsos.worldline.v4");

var tasks = panel.addWidget("org.kde.plasma.icontasks");
tasks.currentConfigGroup = ["General"];
tasks.writeConfig("maxStripes", 1);
tasks.writeConfig("iconSpacing", 1);
tasks.writeConfig("launchers", [
    "applications:steins-navigator-v4.desktop",
    "applications:org.kde.dolphin.desktop",
    "applications:steins-terminal-v3.desktop",
    "applications:steins-dmail.desktop"
]);

panel.addWidget("org.kde.plasma.marginsseparator");
panel.addWidget("org.kde.plasma.systemtray");
panel.addWidget("org.kde.plasma.digitalclock");
