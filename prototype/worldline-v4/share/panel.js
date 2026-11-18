// Disposable prototype layout. Only run after explicit per-profile opt-in.
var old = panels();
for (var i=0; i<old.length; i++) old[i].remove();
var p = new Panel;
p.location = 'bottom';
p.height = 48;
p.floating = true;
var launcher = p.addWidget('org.kde.plasma.kickoff');
launcher.currentConfigGroup = ['General'];
launcher.writeConfig('icon', 'steins-os');
launcher.writeConfig('favoritesPortedToKAstats', true);
var tasks = p.addWidget('org.kde.plasma.icontasks');
tasks.currentConfigGroup = ['General'];
tasks.writeConfig('launchers', ['applications:steins-navigator.desktop',
    'applications:org.kde.dolphin.desktop', 'applications:steins-terminal.desktop',
    'applications:steins-dmail.desktop']);
p.addWidget('org.kde.plasma.marginsseparator');
p.addWidget('org.kde.plasma.systemtray');
p.addWidget('org.kde.plasma.digitalclock');
