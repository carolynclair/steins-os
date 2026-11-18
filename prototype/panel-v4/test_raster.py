#!/usr/bin/env python3
"""Render actual KSvg frames and white-text composites in a private Plasma loader."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,tempfile
from PIL import Image
HERE=Path(__file__).resolve().parent
QML=r'''
import QtQuick
import QtQuick.Layouts
import org.kde.ksvg as KSvg
import org.kde.plasma.plasmoid
PlasmoidItem {
    id: root
    width: 620; height: 510
    preferredRepresentation: fullRepresentation
    property var cases: __CASES__
    property int caseIndex: 0
    property int saved: 0
    property bool done: false
    function ready() {
        saved++;
        if (saved!==2) return;
        saved=0;
        if (caseIndex+1===cases.length) {root.done=true;console.log("RASTER_DONE");}
        else {caseIndex++;}
    }
    fullRepresentation: Item {
        Layout.minimumWidth: 620; Layout.minimumHeight: 510
        implicitWidth: 620; implicitHeight: 510
        Rectangle {
            id: composite
            width: root.cases[root.caseIndex].width
            height: root.cases[root.caseIndex].height
            color: "#080d12"
            Column {
                anchors.fill: parent
                Repeater {
                    model: 20
                    Text {
                        text: "WHITE UNDERLAY 0123456789 WHITE UNDERLAY"
                        color: "white";font.bold: true;font.pixelSize: 28
                        font.family: "DejaVu Sans Mono"
                    }
                }
            }
            KSvg.FrameSvgItem {
                id: frame
                anchors.fill: parent
                imagePath: root.cases[root.caseIndex].path
                prefix: root.cases[root.caseIndex].prefix || ""
            }
        }
        Timer {
            id: capture
            interval: 500;running: !root.done;repeat: true
            onTriggered: {
                const test=root.cases[root.caseIndex];
                frame.grabToImage(function(result) {console.log("RASTER_SAVE "+test.name+" frame "+result.saveToFile(test.frame));root.ready();});
                composite.grabToImage(function(result) {console.log("RASTER_SAVE "+test.name+" composite "+result.saveToFile(test.composite));root.ready();});
            }
        }
    }
}
'''

def main():
    out=HERE/'evidence/raster';out.mkdir(parents=True,exist_ok=True)
    cases=[]
    for name,rel,w,h,prefix in [('dialog-389','dialogs/background.svg',389,247,''),('dialog-568','dialogs/background.svg',568,458,''),('widget-411','widgets/background.svg',411,317,''),('panel-607','widgets/panel-background.svg',607,46,''),('task-focus','widgets/tasks.svg',93,36,'focus'),('list-pressed','widgets/listitem.svg',247,38,'pressed')]:
        cases.append({'name':name,'path':str(HERE/'theme'/rel),'prefix':prefix,'width':w,'height':h,'frame':str(out/(name+'-frame.png')),'composite':str(out/(name+'-composite.png'))})
    with tempfile.TemporaryDirectory(prefix='steins-raster-qa-') as tmp_name:
        tmp=Path(tmp_name);(tmp/'run').mkdir(mode=0o700)
        package=tmp/'package';(package/'contents/ui').mkdir(parents=True)
        (package/'metadata.json').write_text(json.dumps({'KPackageStructure':'Plasma/Applet','KPlugin':{'Id':'org.steinsos.raster-fixture','Name':'Steins frame raster fixture','Version':'1.0','License':'MIT'},'X-Plasma-API-Minimum-Version':'6.3'}))
        (package/'contents/ui/main.qml').write_text(QML.replace('__CASES__',json.dumps(cases)))
        conf=tmp/'bus.conf';conf.write_text('<busconfig><type>session</type><listen>unix:tmpdir=/tmp</listen><auth>EXTERNAL</auth><policy context="default"><allow send_destination="*" eavesdrop="true"/><allow eavesdrop="true"/><allow own="*"/></policy></busconfig>')
        env=dict(os.environ,HOME=str(tmp),XDG_CONFIG_HOME=str(tmp/'config'),XDG_DATA_HOME=str(tmp/'data'),XDG_CACHE_HOME=str(tmp/'cache'),XDG_RUNTIME_DIR=str(tmp/'run'),QT_QPA_PLATFORM='offscreen',QT_QUICK_BACKEND='software')
        log=out/'loader.log'
        with log.open('w') as f:result=subprocess.run(['dbus-run-session','--config-file',str(conf),'--','timeout','-k','2s','8s','plasmawindowed',str(package)],env=env,stdout=f,stderr=f,timeout=20)
        assert result.returncode==124,(result.returncode,log.read_text())
        assert 'RASTER_DONE' in log.read_text(),log.read_text()
    reports=[]
    for c in cases:
        image=Image.open(c['frame']).convert('RGBA');assert image.size==(c['width'],c['height']),image.size
        w,h=image.size;threshold=230 if c['name'].startswith('panel') else 254
        # Ignore rounded corner regions and the 1px antialiased outside edge.
        coordinates=[(x,y) for y in range(1,6) for x in range(8,w-8)]
        coordinates += [(x,y) for x in range(1,6) for y in range(8,h-8)]
        coordinates += [(x,y) for y in range(h-6,h-1) for x in range(8,w-8)]
        coordinates += [(x,y) for x in range(w-6,w-1) for y in range(8,h-8)]
        gaps=[(x,y,image.getpixel((x,y))[3]) for x,y in coordinates if image.getpixel((x,y))[3]<threshold]
        reports.append({'case':c['name'],'size':[w,h],'minimum_edge_alpha':min(image.getpixel(p)[3] for p in coordinates),'gap_pixels':len(gaps),'sample_gaps':gaps[:12],'source_sha256':hashlib.sha256(Path(c['path']).read_bytes()).hexdigest()})
    report={'passed':all(r['gap_pixels']==0 for r in reports),'scope':'actual KSvg FrameSvgItem raster + bold white text underlay composites on private offscreen Plasma, temporary HOME/XDG and private D-Bus','cases':reports}
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    assert report['passed'],'Native frame raster contains transparent edge seams'
if __name__=='__main__':main()
