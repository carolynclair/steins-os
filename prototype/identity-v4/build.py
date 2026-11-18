#!/usr/bin/env python3
"""Original V4 icon family + token package; builds only, never installs or selects."""
import base64,hashlib,json,os,shutil,subprocess,tempfile
from html import escape
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]
OUT=PROJECT/'dist/v4/identity'
VERSION='0.4.0~prototype1'
TOKENS=json.loads((ROOT/'TOKENS.json').read_text())
INK=TOKENS['color']['icon']; ACC=TOKENS['color']['accent']
# Original geometry on a 24 DIP grid. Symbols preserve their familiar meaning.
FOLDER='<path d="M3.5 8V6.5A2 2 0 0 1 5.5 4.5H10l2.5 3h6A2 2 0 0 1 20.5 9.5v8A2 2 0 0 1 18.5 19.5h-13A2 2 0 0 1 3.5 17.5Z"/>'
ICONS={
 'launcher':('<rect x="4" y="4" width="6" height="6" rx="1.5"/><rect x="14" y="4" width="6" height="6" rx="1.5"/><rect x="4" y="14" width="6" height="6" rx="1.5"/><rect x="14" y="14" width="6" height="6" rx="1.5"/>','Applications'),
 'terminal':('<rect x="3.5" y="4.5" width="17" height="15" rx="3"/><path d="m7.5 9 3.5 3-3.5 3m6 0h3"/>','Terminal'),
 'folder':(FOLDER,'Files'),
 'folder-open':('<path d="M3.5 10V6.5A2 2 0 0 1 5.5 4.5H10l2.5 3h6A2 2 0 0 1 20.5 9.5V11M3.5 10H21l-2.2 8a2 2 0 0 1-1.9 1.5H5a2 2 0 0 1-2-1.7L2 12a1.7 1.7 0 0 1 1.5-2Z"/>','Open folder'),
 'mail':('<rect x="3.5" y="5.5" width="17" height="13" rx="3"/><path d="m4.5 7 7.5 5.5L19.5 7"/>','Mail'),
 'worldlines':('<circle cx="12" cy="12" r="8.5"/><path d="M3.8 12h16.4M12 3.5c3 2.2 4.2 5 4.2 8.5s-1.2 6.3-4.2 8.5c-3-2.2-4.2-5-4.2-8.5s1.2-6.3 4.2-8.5Z"/>','Worldlines'),
 'settings':('<g transform="translate(0 -.8)"><path d="M9.5 3.5h5l.6 2.2 1.6.9 2.2-.6 2.5 4.3-1.6 1.6v1.8l1.6 1.6-2.5 4.3-2.2-.6-1.6.9-.6 2.2h-5l-.6-2.2-1.6-.9-2.2.6-2.5-4.3 1.6-1.6v-1.8l-1.6-1.6L5.1 6l2.2.6 1.6-.9Z"/><circle cx="12" cy="12.8" r="3"/></g>','Settings'),
 'appearance':('<rect x="4" y="4" width="16" height="6" rx="2"/><path d="M17 10v3h-5v7M4 6H2.5v5"/>','Appearance'),
 'power':('<path d="M7.1 5.5a8 8 0 1 0 9.8 0M12 2.8v9"/>','Power'),
 'reboot':('<path d="M19.5 9A8 8 0 1 0 20 15M19.5 3.5V9H14"/>','Restart'),
 'logout':('<path d="M11.5 4.5h-7v15h7M10 12h11m-4-4 4 4-4 4"/>','Sign out'),
 'notification':('<path d="M6.5 10a5.5 5.5 0 0 1 11 0v4l2 3h-15l2-3Zm3 10h5M12 2.5v2"/>','Notifications'),
 'network':('<path d="M3.5 8.5a13 13 0 0 1 17 0M6.5 12a8.4 8.4 0 0 1 11 0M9.5 15.5a3.8 3.8 0 0 1 5 0"/><circle cx="12" cy="19" r=".8" fill="currentColor" stroke="none"/>','Network'),
 'volume':('<path d="M3.5 9.5h4L12 5v14l-4.5-4.5h-4ZM15.5 8a5.5 5.5 0 0 1 0 8m3-11a9.5 9.5 0 0 1 0 14"/>','Volume'),
 'volume-medium':('<path d="M3.5 9.5h4L12 5v14l-4.5-4.5h-4ZM15.5 8a5.5 5.5 0 0 1 0 8"/>','Medium volume'),
 'volume-low':('<path d="M3.5 9.5h4L12 5v14l-4.5-4.5h-4ZM15.5 10a2.7 2.7 0 0 1 0 4"/>','Low volume'),
 'volume-muted':('<path d="M3.5 9.5h4L12 5v14l-4.5-4.5h-4ZM16 9l5 6m0-6-5 6"/>','Muted volume'),
 'home':('<path d="m3.5 10 8.5-7 8.5 7M5.5 8.5v11h5v-6h3v6h5v-11"/>','Home'),
 'document':('<path d="M5.5 3.5h8l5 5v12h-13ZM13.5 3.5v5h5M8.5 12.5h7m-7 4h7"/>','Document'),
 'download':('<path d="M12 3.5v11m-4-4 4 4 4-4M4.5 16v4.5h15V16"/>','Downloads'),
 'image':('<rect x="3.5" y="3.5" width="17" height="17" rx="3"/><circle cx="8" cy="8" r="1.3"/><path d="m4 17 5-5 4 4 3-3 4 4"/>','Pictures'),
 'audio':('<path d="M9 17V5.5L19 3v11.5M9 9l10-2.5"/><ellipse cx="6" cy="17.5" rx="3" ry="2.5"/><ellipse cx="16" cy="15" rx="3" ry="2.5"/>','Music'),
 'video':('<rect x="3.5" y="5" width="17" height="14" rx="3"/><path d="m10 9 5 3-5 3Z"/>','Videos'),
 'trash':('<path d="M4.5 6.5h15M6 6.5l1 14h10l1-14M8.5 6.5v-3h7v3M10 10v7m4-7v7"/>','Trash'),
 'search':('<circle cx="10.5" cy="10.5" r="6.5"/><path d="m15.5 15.5 5 5"/>','Search'),
 'close':('<path d="m6 6 12 12M18 6 6 18"/>','Close'),
 'plus':('<path d="M12 4v16M4 12h16"/>','New item'),
 'chevron-down':('<path d="m6 9 6 6 6-6"/>','Expand'),
}
# Places keep one outer folder silhouette, with small conventional contents.
for name,body,title in [
 ('folder-home','<path d="m8 13 4-3 4 3m-7-1v5h6v-5"/>','Home folder'),
 ('folder-documents','<path d="M9 10.5h6v6H9Zm2 2h2m-2 2h2"/>','Documents folder'),
 ('folder-downloads','<path d="M12 10v6m-2.5-2.5L12 16l2.5-2.5"/>','Downloads folder'),
 ('folder-pictures','<rect x="8.5" y="10.5" width="7" height="6" rx="1"/><path d="m9 15 2-2 2 2 1-1 1 1"/>','Pictures folder'),
 ('folder-music','<path d="M11 15v-4l4-1v4"/><ellipse cx="9.8" cy="15.6" rx="1.3" ry="1"/><ellipse cx="13.8" cy="14.6" rx="1.3" ry="1"/>','Music folder'),
 ('folder-videos','<path d="m10.5 10.5 4 3-4 3Z"/>','Videos folder'),
 ('folder-network','<path d="M12 10v3m-4 3v-3h8v3"/><circle cx="8" cy="17" r=".7" fill="currentColor" stroke="none"/><circle cx="16" cy="17" r=".7" fill="currentColor" stroke="none"/>','Network folder'),
]:
 ICONS[name]=(FOLDER+body,title)
ALIASES={
 'apps':{'steins-launcher':'launcher','start-here':'launcher','utilities-terminal':'terminal','steins-terminal':'terminal','steins-terminal-v3':'terminal','steins-terminal-v4':'terminal','org.kde.konsole':'terminal','konsole':'terminal','system-file-manager':'folder','org.kde.dolphin':'folder','dolphin':'folder','steins-dmail':'mail','internet-mail':'mail','steins-navigator':'worldlines','steins-navigator-v4':'worldlines','steins-worldline':'worldlines','steins-worldlines':'worldlines','preferences-system':'settings','systemsettings':'settings','systemsettings5':'settings','systemsettings6':'settings','preferences-desktop-theme':'appearance','preferences-desktop':'settings'},
 'places':{'folder':'folder','folder-open':'folder-open','user-home':'home','user-desktop':'home','folder-home':'folder-home','folder-documents':'folder-documents','folder-download':'folder-downloads','folder-downloads':'folder-downloads','folder-pictures':'folder-pictures','folder-music':'folder-music','folder-videos':'folder-videos','folder-network':'folder-network','user-trash':'trash','user-trash-full':'trash'},
 'actions':{'system-shutdown':'power','system-reboot':'reboot','system-log-out':'logout','configure':'settings','preferences-other':'settings','edit-find':'search','window-close':'close','tab-close':'close','list-add':'plus','arrow-down':'chevron-down','mail-message-new':'mail'},
 'status':{'notifications':'notification','notification-inactive':'notification','network-wireless':'network','network-wireless-connected-100':'network','audio-volume-high':'volume','audio-volume-medium':'volume-medium','audio-volume-low':'volume-low','audio-volume-muted':'volume-muted'},
 'mimetypes':{'text-x-generic':'document','application-x-desktop':'launcher','image-x-generic':'image','audio-x-generic':'audio','video-x-generic':'video'}
}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def svg(body,title):
 return '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" color="'+INK+'" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><title>'+escape(title)+'</title><metadata>Original Steins;OS icon geometry; CC-BY-4.0; Steins;OS contributors</metadata>'+body+'</svg>\n'
def write(path,text):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
def build_assets():
 for name,(body,title) in ICONS.items():write(ROOT/'icons'/f'{name}.svg',svg(body,title))
 theme=ROOT/'theme/SteinsLab'
 sections=[]
 for context,aliases in ALIASES.items():
  directory=theme/'scalable'/context;directory.mkdir(parents=True,exist_ok=True)
  for alias,source in aliases.items():shutil.copyfile(ROOT/'icons'/f'{source}.svg',directory/(alias+'.svg'))
  sections.append(f'[scalable/{context}]\nSize=24\nMinSize=16\nMaxSize=256\nType=Scalable\nContext='+{'apps':'Applications','places':'Places','actions':'Actions','status':'Status','mimetypes':'MimeTypes'}[context]+'\n')
 original=PROJECT/'config/includes.chroot/usr/share/icons/hicolor/scalable/apps/steins-os.svg'
 shutil.copyfile(original,theme/'scalable/apps/steins-os.svg')
 dirs=','.join('scalable/'+key for key in ALIASES)
 write(theme/'index.theme','[Icon Theme]\nName=SteinsLab\nComment=Original restrained Steins;OS semantic icon family\nInherits=Papirus-Dark,breeze-dark,breeze,hicolor\nDirectories='+dirs+'\n\n'+'\n'.join(sections))
 return original

def board():
 # Every small icon appears at its true16/24/32px size before a64px inspection sample.
 rows=list(ICONS);columns=4;cellw=310;cellh=148;W=1320;H=220+((len(rows)+columns-1)//columns)*cellh+180
 parts=[f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',f'<rect width="{W}" height="{H}" fill="#11181e"/>']
 def text(x,y,t,size=14,color='#e6e8e7',weight=400):parts.append(f'<text x="{x}" y="{y}" font-family="Noto Sans" font-size="{size}" font-weight="{weight}" fill="{color}">{escape(t)}</text>')
 def asset(path):return 'data:image/svg+xml;base64,'+base64.b64encode(path.read_bytes()).decode()
 text(40,51,'STEINS;OS / V4 ICON FAMILY',27,weight=600)
 text(40,83,'One consistent OS identity. Six different atmospheres.',16,'#abb6bc')
 text(40,111,'Original vector assets · true 16 / 24 / 32 px samples · existing emblem retained',13,'#93a3ad')
 parts.append('<image x="1192" y="30" width="64" height="64" xlink:href="'+asset(ROOT/'theme/SteinsLab/scalable/apps/steins-os.svg')+'"/>')
 text(1090,120,'Current mark unchanged',12,'#93a3ad')
 # Static panel asset composition, explicitly not a running shell.
 parts.append('<rect x="40" y="143" width="1240" height="46" rx="8" fill="#151d23" stroke="#3c4b55"/>')
 for i,name in enumerate(['launcher','terminal','folder','mail','worldlines','settings']):parts.append(f'<image x="{56+i*48}" y="154" width="24" height="24" xlink:href="{asset(ROOT/"icons"/(name+".svg"))}"/>')
 for i,(name,data) in enumerate(TOKENS['worldlines'].items()):
  x=440+i*130
  parts.append(f'<rect x="{x}" y="154" width="110" height="24" rx="4" fill="#0e151b" stroke="#3c4b55"/><path d="M{x+8} 174h94" stroke="{data["accent"]}" stroke-opacity=".6"/>')
  text(x+11,170,name[:13],10,data['accent'])
 for index,name in enumerate(rows):
  x=40+(index%columns)*cellw;y=225+(index//columns)*cellh
  parts.append(f'<rect x="{x}" y="{y}" width="294" height="132" rx="8" fill="#151d23" stroke="#293640"/>')
  text(x+14,y+25,ICONS[name][1],13,weight=500)
  cursor=x+14
  for size in [16,24,32,64]:
   parts.append(f'<image x="{cursor}" y="{y+44}" width="{size}" height="{size}" xlink:href="{asset(ROOT/"icons"/(name+".svg"))}"/>')
   text(cursor,y+120,str(size),10,'#93a3ad');cursor+=size+23
 bottom=H-125
 text(40,bottom,'Semantic shapes stay familiar: folder, terminal prompt, envelope, globe, settings cog.',14)
 text(40,bottom+27,'Neutral ink, 24px construction grid, 1.75px rounded strokes, restrained shared geometry.',13,'#abb6bc')
 text(40,bottom+53,'Third-party application brands remain upstream through inherited icon themes.',13,'#abb6bc')
 text(40,bottom+85,'ASSET PROOF / panel arrangement above is a static study, not a running desktop capture.',12,'#93a3ad')
 parts.append('</svg>');write(ROOT/'evidence/comparison-sheet.svg',''.join(parts))

def render():
 code="""import subprocess\nfrom pathlib import Path\nr=Path('/identity')\nfor p in sorted((r/'icons').glob('*.svg')):\n for size in [16,24,32]:\n  dest=r/'evidence/sizes'/(p.stem+'-'+str(size)+'.png');dest.parent.mkdir(parents=True,exist_ok=True)\n  subprocess.run(['rsvg-convert','-w',str(size),'-h',str(size),str(p),'-o',str(dest)],check=True)\nsubprocess.run(['rsvg-convert',str(r/'evidence/comparison-sheet.svg'),'-o',str(r/'evidence/comparison-sheet.png')],check=True)\n"""
 subprocess.run(['docker','run','--rm','--user',f'{os.getuid()}:{os.getgid()}','-v',str(ROOT)+':/identity','steins-os-builder:trixie','python3','-c',code],check=True)

def package(original):
 OUT.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='steins-identity-') as tmp:
  stage=Path(tmp);theme=stage/'usr/share/icons/SteinsLab';theme.parent.mkdir(parents=True);shutil.copytree(ROOT/'theme/SteinsLab',theme)
  target=stage/'usr/share/steins-v4';target.mkdir(parents=True);shutil.copyfile(ROOT/'TOKENS.json',target/'tokens.json')
  doc=stage/'usr/share/doc/steins-identity-v4';doc.mkdir(parents=True)
  for name in ['README.md','LICENSE','PROVENANCE.json','copyright']:shutil.copyfile(ROOT/name,doc/name)
  control=stage/'DEBIAN/control';control.parent.mkdir();control.write_text('Package: steins-identity-v4\nVersion: '+VERSION+'\nArchitecture: all\nMaintainer: Steins OS contributors <steins@localhost>\nSection: x11\nPriority: optional\nDepends: papirus-icon-theme\nDescription: Original SteinsLab icon family and shared V4 design tokens\n Familiar semantic symbols with stable neutral ink and subtle world accents.\n No icon theme or desktop configuration is selected automatically.\n')
  for p in stage.rglob('*'):p.chmod(0o755 if p.is_dir() else 0o644)
  artifact=OUT/('steins-identity-v4_'+VERSION+'_all.deb')
  env=dict(os.environ,SOURCE_DATE_EPOCH=(PROJECT/'packaging/SOURCE_DATE_EPOCH').read_text().strip())
  subprocess.run(['dpkg-deb','--root-owner-group','--build',str(stage),str(artifact)],check=True,env=env)
 return artifact

def main():
 original=build_assets();board();render()
 provenance={'original_geometry':True,'source':'Hand-authored SVG on a 24px grid; no reference artwork traced; no fonts bundled',
 'canonical_icon_count':len(ICONS),'alias_count':sum(len(x) for x in ALIASES.values()),'current_emblem_preserved_sha256':sha(original),'theme_emblem_sha256':sha(ROOT/'theme/SteinsLab/scalable/apps/steins-os.svg'),
 'license':'Original icons CC-BY-4.0, Steins;OS contributors; project code/tokens MIT; inherited upstream themes retain their own licenses',
 'icons':[{'name':name,'meaning':title,'sha256':sha(ROOT/'icons'/f'{name}.svg')} for name,(_,title) in ICONS.items()],
 'aliases':ALIASES,'default_selection':'None; package does not alter host or guest configuration'}
 write(ROOT/'PROVENANCE.json',json.dumps(provenance,indent=2)+'\n')
 artifact=package(original)
 result={'package':str(artifact.relative_to(PROJECT)),'sha256':sha(artifact),'bytes':artifact.stat().st_size,'version':VERSION,'token_install_path':'/usr/share/steins-v4/tokens.json','theme_name':'SteinsLab','canonical_icons':len(ICONS),'host_install_performed':False}
 write(OUT/'BUILD.json',json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
