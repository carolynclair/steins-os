// Test harness only; exercised by the real Qt QML engine on a private bus.
function migrationChecks(source) {
    var activePanel;
    function panels() { return [activePanel]; }
    function assert(value, message) { if (!value) throw new Error(message); }
    function fixture(nativeSequence) {
        var list=[], added=0, removed=[];
        function widget(id,type,config) {
            var w={id:id,type:type,currentConfigGroup:[],geometry:{x:0,y:0,width:40,height:46},config:config||{}};
            w.readConfig=function(k,d){
                var value=Object.prototype.hasOwnProperty.call(w.config,k)?w.config[k]:d;
                if (nativeSequence && k==='launchers' && Array.isArray(value)) {
                    var sequence={length:value.length};
                    value.forEach(function(v,i){sequence[i]=v;});
                    assert(!Array.isArray(sequence),'native sequence fixture became an Array');
                    return sequence;
                }
                return value;
            };
            w.writeConfig=function(k,v){w.config[k]=v;};
            w.remove=function(){removed.push(String(id));list=list.filter(function(i){return i.id!==id;});};
            // An attempt to rely on the Plasma6.3 stub is a test failure.
            Object.defineProperty(w,'index',{get:function(){throw new Error('Widget.index read');},set:function(){throw new Error('Widget.index written');}});
            return w;
        }
        list=[widget(1,'org.kde.plasma.kickoff',{icon:'steins-os'}),
          widget(2,'org.steinsos.worldline'),
          widget(3,'org.kde.plasma.icontasks',{launchers:['preferred://browser','applications:steins-navigator.desktop','applications:org.kde.konsole.desktop','applications:steins-worldline.desktop','applications:steins-navigator-v4.desktop','applications:steins-terminal.desktop','preferred://browser','applications:steins-terminal-v3.desktop','steins-worldlines.desktop','steins-terminal.desktop','applications:other.steins-navigator.desktop','applications:steins-worldlines','steins-navigator']}),
          widget(4,'org.kde.plasma.systemtray'),widget(5,'org.kde.plasma.digitalclock'),widget(6,'third.party.keepme',{personal:'keep'})];
        var p={id:10,location:'bottom',currentConfigGroup:['Existing'],config:{AppletOrder:'1;2;3;4;5;6'},height:54,floating:true};
        p.widgets=function(){return list.slice();};p.readConfig=function(k,d){return Object.prototype.hasOwnProperty.call(p.config,k)?p.config[k]:d;};p.writeConfig=function(k,v){p.config[k]=v;};
        p.addWidget=function(type,x,y){assert(x>0&&y>0,'insertion geometry');var w=widget(7+added++,type);list.push(w);return w;};
        return {panel:p,list:function(){return list;},removed:removed,added:function(){return added;}};
    }
    function run(f,replace) {activePanel=f.panel;return JSON.parse(eval(source.replace('__STEINS_OPTIONS__',JSON.stringify({replaceV3:replace,panelId:null}))));}
    var plain=fixture();var originalPins=JSON.stringify(plain.list()[2].config.launchers);var r=run(plain,false);
    assert(JSON.stringify(plain.list()[2].config.launchers)===originalPins,'plain apply changed task launchers');
    assert(plain.removed.length===0,'plain apply removed an existing widget');
    assert(r.saved_order==='1;7;2;3;4;5;6','plain apply changed unrelated order');
    assert(plain.panel.height===46&&plain.panel.floating===false,'panel geometry');
    assert(plain.panel.currentConfigGroup[0]==='Existing','panel config group not restored');
    var replace=fixture(true);var s=run(replace,true);
    assert(JSON.stringify(replace.removed)==='["2"]','replace removed an unrelated widget');
    assert(s.saved_order==='1;7;3;4;5;6','replace order');
    assert(replace.list().filter(function(w){return w.id===6;})[0].config.personal==='keep','third party settings');
    var tasks=replace.list().filter(function(w){return w.id===3;})[0];
    var expectedPins=['preferred://browser','applications:steins-navigator-v4.desktop','applications:org.kde.konsole.desktop','applications:steins-terminal-v3.desktop','preferred://browser','applications:other.steins-navigator.desktop'];
    assert(JSON.stringify(tasks.config.launchers)===JSON.stringify(expectedPins),'own aliases were not normalized/deduplicated or third-party pins changed');
    assert(tasks.config.iconSpacing===1&&tasks.config.maxStripes===1,'native task options');
    var again=run(replace,true);assert(replace.added()===1,'idempotent apply duplicated V4 meter');
    assert(again.saved_order===s.saved_order,'second apply changed order');
    assert(JSON.stringify(tasks.config.launchers)===JSON.stringify(expectedPins),'second apply changed task pins');
    // Qt.application.arguments is a genuine native QStringList exposed to QML.
    // It exercises the same non-Array V4Sequence bridge as KConfig readConfig.
    var nativeArguments=Qt.application.arguments;
    assert(typeof nativeArguments==='object'&&nativeArguments.length>0,'native Qt QStringList unavailable');
    var nativeConfig=fixture(false);nativeConfig.list()[2].config.launchers=nativeArguments;
    var nativeBefore=JSON.stringify(nativeArguments);run(nativeConfig,true);
    assert(JSON.stringify(nativeConfig.list().filter(function(w){return w.id===3;})[0].config.launchers)===nativeBefore,'native Qt sequence values were altered');
    var jsArray=fixture(false);run(jsArray,true);
    assert(JSON.stringify(jsArray.list().filter(function(w){return w.id===3;})[0].config.launchers)===JSON.stringify(expectedPins),'ordinary JS array regression');
    var invalid=fixture(false);invalid.list()[2].config.launchers={length:1000000000};var invalidRefused=false;
    try {run(invalid,true);} catch(e){invalidRefused=true;}
    assert(invalidRefused&&invalid.added()===0&&invalid.removed.length===0&&invalid.panel.height===54,'unbounded native sequence was not refused before mutation');
    var badEntry=fixture(false);badEntry.list()[2].config.launchers={0:42,length:1};var entryRefused=false;
    try {run(badEntry,true);} catch(e){entryRefused=true;}
    assert(entryRefused&&badEntry.added()===0&&badEntry.removed.length===0&&badEntry.panel.height===54,'invalid native entry was not refused before mutation');
    var bad=fixture();bad.panel.config.AppletOrder='';var refused=false;
    try {run(bad,true);} catch(e){refused=true;}
    assert(refused&&bad.added()===0&&bad.removed.length===0&&bad.panel.height===54,'missing saved order was not a safe refusal');
    return {passed:true,plain_order:r.saved_order,replace_order:s.saved_order,removed:replace.removed,idempotent:true,safe_refusal:true,unrelated_widgets_preserved:true,plain_pins_unchanged:true,native_sequence_copy:true,native_qt_qstringlist:{array:Array.isArray(nativeArguments),tag:Object.prototype.toString.call(nativeArguments),length:nativeArguments.length},js_array_compatible:true,invalid_sequences_refused_before_mutation:true,normalized_own_pins:tasks.config.launchers,third_party_duplicates_preserved:true};
}
